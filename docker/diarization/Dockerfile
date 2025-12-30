# Speaker Diarization Service with pyannote-audio
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    pyannote.audio \
    torch \
    torchaudio \
    numpy \
    scipy \
    soundfile

# Copy application code
COPY app.py .

# Create embeddings directory
RUN mkdir -p /app/embeddings

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
