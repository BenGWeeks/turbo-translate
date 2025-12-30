"""Speaker diarization service using pyannote-audio."""

import io
import os
import json
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

# Initialize app
app = FastAPI(title="Speaker Diarization Service")

# Global models (loaded on startup)
diarization_pipeline = None
embedding_model = None
speaker_embeddings = {}

EMBEDDINGS_DIR = Path("/app/embeddings")
DEVICE = os.environ.get("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")


@app.on_event("startup")
async def load_models():
    """Load models on startup."""
    global diarization_pipeline, embedding_model, speaker_embeddings

    hf_token = os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("WARNING: HUGGINGFACE_TOKEN not set. Some models may not load.")

    try:
        from pyannote.audio import Pipeline, Model

        # Load diarization pipeline
        print("Loading diarization pipeline...")
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        diarization_pipeline.to(torch.device(DEVICE))
        print("Diarization pipeline loaded.")

        # Load embedding model for speaker identification
        print("Loading embedding model...")
        embedding_model = Model.from_pretrained(
            "pyannote/wespeaker-voxceleb-resnet34-LM",
            use_auth_token=hf_token
        )
        embedding_model.to(torch.device(DEVICE))
        print("Embedding model loaded.")

        # Load saved speaker embeddings
        load_speaker_embeddings()

    except Exception as e:
        print(f"Error loading models: {e}")
        raise


def load_speaker_embeddings():
    """Load saved speaker embeddings from disk."""
    global speaker_embeddings

    EMBEDDINGS_DIR.mkdir(exist_ok=True)
    index_file = EMBEDDINGS_DIR / "index.json"

    if index_file.exists():
        with open(index_file) as f:
            index = json.load(f)

        for speaker_id, info in index.items():
            emb_file = EMBEDDINGS_DIR / info["embedding_file"]
            if emb_file.exists():
                embedding = np.load(emb_file)
                speaker_embeddings[speaker_id] = {
                    "name": info["name"],
                    "embedding": embedding,
                    "is_user": info.get("is_user", False)
                }
        print(f"Loaded {len(speaker_embeddings)} speaker embeddings.")


def save_speaker_embeddings():
    """Save speaker embeddings index to disk."""
    index = {}
    for speaker_id, info in speaker_embeddings.items():
        emb_file = f"{speaker_id}.npy"
        np.save(EMBEDDINGS_DIR / emb_file, info["embedding"])
        index[speaker_id] = {
            "name": info["name"],
            "embedding_file": emb_file,
            "is_user": info.get("is_user", False)
        }

    with open(EMBEDDINGS_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "device": DEVICE}


@app.post("/diarize")
async def diarize(file: UploadFile = File(...)):
    """
    Perform speaker diarization on audio.

    Returns segments with speaker labels.
    """
    if diarization_pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Read audio
        audio_bytes = await file.read()
        audio_buffer = io.BytesIO(audio_bytes)
        waveform, sample_rate = sf.read(audio_buffer)

        # Convert to tensor
        if len(waveform.shape) == 1:
            waveform = waveform.reshape(1, -1)
        elif len(waveform.shape) == 2:
            waveform = waveform.T

        waveform_tensor = torch.tensor(waveform, dtype=torch.float32)

        # Run diarization
        diarization = diarization_pipeline({
            "waveform": waveform_tensor,
            "sample_rate": sample_rate
        })

        # Convert to segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Map speaker label to ID
            speaker_id = int(speaker.split("_")[-1]) if "_" in speaker else 0

            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker_id
            })

        return JSONResponse({"segments": segments})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/identify")
async def identify_speaker(file: UploadFile = File(...)):
    """
    Identify a speaker from audio using enrolled profiles.

    Returns the closest matching speaker or -1 if unknown.
    """
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not speaker_embeddings:
        return JSONResponse({
            "speaker_id": -1,
            "speaker_name": "Unknown",
            "confidence": 0.0
        })

    try:
        # Read audio
        audio_bytes = await file.read()
        audio_buffer = io.BytesIO(audio_bytes)
        waveform, sample_rate = sf.read(audio_buffer)

        # Get embedding
        if len(waveform.shape) == 1:
            waveform = waveform.reshape(1, -1)
        waveform_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            embedding = embedding_model(waveform_tensor.to(DEVICE))
            embedding = embedding.cpu().numpy().flatten()

        # Find closest speaker
        best_match = None
        best_score = -1

        for speaker_id, info in speaker_embeddings.items():
            stored_emb = info["embedding"]
            # Cosine similarity
            score = np.dot(embedding, stored_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(stored_emb)
            )

            if score > best_score:
                best_score = score
                best_match = (speaker_id, info)

        # Threshold for identification
        threshold = 0.7
        if best_match and best_score > threshold:
            return JSONResponse({
                "speaker_id": best_match[0],
                "speaker_name": best_match[1]["name"],
                "confidence": float(best_score),
                "is_user": best_match[1].get("is_user", False)
            })

        return JSONResponse({
            "speaker_id": -1,
            "speaker_name": "Unknown",
            "confidence": float(best_score) if best_match else 0.0
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enroll")
async def enroll_speaker(
    file: UploadFile = File(...),
    name: str = Form(...),
    is_user: str = Form("false")
):
    """
    Enroll a new speaker profile.

    Extracts voice embedding and saves for future identification.
    """
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Read audio
        audio_bytes = await file.read()
        audio_buffer = io.BytesIO(audio_bytes)
        waveform, sample_rate = sf.read(audio_buffer)

        # Get embedding
        if len(waveform.shape) == 1:
            waveform = waveform.reshape(1, -1)
        waveform_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            embedding = embedding_model(waveform_tensor.to(DEVICE))
            embedding = embedding.cpu().numpy().flatten()

        # Generate speaker ID
        speaker_id = f"speaker_{len(speaker_embeddings)}"
        is_user_bool = is_user.lower() == "true"

        # If enrolling as user, mark as speaker 0
        if is_user_bool:
            speaker_id = "speaker_0"

        # Save embedding
        speaker_embeddings[speaker_id] = {
            "name": name,
            "embedding": embedding,
            "is_user": is_user_bool
        }
        save_speaker_embeddings()

        return JSONResponse({
            "speaker_id": speaker_id,
            "name": name,
            "is_user": is_user_bool,
            "status": "enrolled"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/speakers")
async def list_speakers():
    """List all enrolled speakers."""
    speakers = []
    for speaker_id, info in speaker_embeddings.items():
        speakers.append({
            "speaker_id": speaker_id,
            "name": info["name"],
            "is_user": info.get("is_user", False)
        })
    return JSONResponse({"speakers": speakers})


@app.delete("/speakers/{speaker_id}")
async def delete_speaker(speaker_id: str):
    """Delete an enrolled speaker."""
    if speaker_id not in speaker_embeddings:
        raise HTTPException(status_code=404, detail="Speaker not found")

    del speaker_embeddings[speaker_id]
    save_speaker_embeddings()

    # Remove embedding file
    emb_file = EMBEDDINGS_DIR / f"{speaker_id}.npy"
    if emb_file.exists():
        emb_file.unlink()

    return JSONResponse({"status": "deleted", "speaker_id": speaker_id})
