"""Text-to-Speech service using Coqui TTS."""

import io
import os
from typing import Optional

import numpy as np
import scipy.io.wavfile as wav
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="TTS Service")

# Global TTS model
tts = None

# Language to model mapping
LANGUAGE_MODELS = {
    "en": "tts_models/en/ljspeech/tacotron2-DDC",
    "hu": "tts_models/hu/css10/vits",
    "de": "tts_models/de/thorsten/tacotron2-DDC",
    "es": "tts_models/es/css10/vits",
}

# Cached TTS instances per language
tts_instances = {}

DEVICE = os.environ.get("DEVICE", "cuda")


class TTSRequest(BaseModel):
    """TTS request model."""

    text: str
    language: str = "en"
    speaker: Optional[str] = None


@app.on_event("startup")
async def load_models():
    """Pre-load default English model on startup."""
    try:
        from TTS.api import TTS

        print("Pre-loading English TTS model...")
        tts_instances["en"] = TTS(model_name=LANGUAGE_MODELS["en"]).to(DEVICE)
        print("English TTS model loaded.")

    except Exception as e:
        print(f"Error loading TTS model: {e}")


def get_tts(language: str):
    """Get or create TTS instance for language."""
    from TTS.api import TTS

    if language not in tts_instances:
        model_name = LANGUAGE_MODELS.get(language)
        if not model_name:
            # Fall back to multilingual model
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

        print(f"Loading TTS model for {language}...")
        tts_instances[language] = TTS(model_name=model_name).to(DEVICE)
        print(f"TTS model for {language} loaded.")

    return tts_instances[language]


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device": DEVICE,
        "loaded_languages": list(tts_instances.keys())
    }


@app.post("/api/tts")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text.

    Returns WAV audio data.
    """
    try:
        tts = get_tts(request.language)

        # Generate speech
        wav_data = tts.tts(text=request.text)

        # Convert to numpy array if needed
        if isinstance(wav_data, list):
            wav_data = np.array(wav_data, dtype=np.float32)

        # Normalize
        wav_data = wav_data / np.max(np.abs(wav_data))

        # Convert to 16-bit PCM
        wav_int16 = (wav_data * 32767).astype(np.int16)

        # Get sample rate from model
        sample_rate = tts.synthesizer.output_sample_rate

        # Write to buffer
        buffer = io.BytesIO()
        wav.write(buffer, sample_rate, wav_int16)

        return Response(
            content=buffer.getvalue(),
            media_type="audio/wav"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/languages")
async def list_languages():
    """List supported languages."""
    return {
        "languages": list(LANGUAGE_MODELS.keys()),
        "default": "en"
    }
