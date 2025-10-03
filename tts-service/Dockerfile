# BLACK BOX TTS Service - Piper TTS
# Fast, neural text-to-speech with warm startup

FROM python:3.10-slim

LABEL maintainer="BLACK BOX Project"
LABEL description="Piper TTS service with warm startup and streaming"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libsndfile1 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    piper-tts==1.2.0 \
    numpy==1.24.3 \
    soundfile==0.12.1 \
    pydantic==2.5.0 \
    python-json-logger==2.0.7 \
    onnxruntime==1.16.3

# Create application directory
WORKDIR /app

# Copy service files
COPY server.py .
COPY healthcheck.py .
COPY requirements.txt .

# Install additional requirements
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /models/piper

# Download Piper voice model (en_US-lessac-medium for clarity)
RUN cd /models/piper && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Expose service port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python healthcheck.py || exit 1

# Run TTS service with preload flag (warm startup)
CMD ["python", "server.py", "--preload"]

