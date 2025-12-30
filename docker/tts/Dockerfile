# Text-to-Speech Service using Coqui TTS
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    espeak-ng \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    TTS \
    fastapi \
    uvicorn \
    python-multipart \
    numpy \
    scipy

# Copy application code
COPY app.py .

EXPOSE 8003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
