# BLACK BOX ASR Service - Whisper.cpp with CUDA acceleration
# Optimized for fast speech recognition on Jetson Orin Nano

FROM nvcr.io/nvidia/l4t-base:r36.2.0

LABEL maintainer="BLACK BOX Project"
LABEL description="Whisper.cpp ASR service with GPU acceleration"

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    python3-pip \
    libopenblas-dev \
    pkg-config \
    cuda-toolkit-12-2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    numpy==1.24.3 \
    soundfile==0.12.1 \
    pydantic==2.5.0 \
    python-json-logger==2.0.7

# Clone and build whisper.cpp with CUDA support
WORKDIR /build
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR /build/whisper.cpp

# Build with CUDA support
RUN make clean && \
    WHISPER_CUDA=1 make -j$(nproc)

# Install Python bindings
RUN pip3 install --no-cache-dir .

# Create application directory
WORKDIR /app

# Copy service files
COPY transcribe.py .
COPY healthcheck.py .
COPY requirements.txt .

# Install additional requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /models/whisper

# Download Whisper models
RUN cd /models/whisper && \
    wget -q https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin && \
    wget -q https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# Set library path for CUDA
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Expose service port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 healthcheck.py || exit 1

# Run transcription service
CMD ["python3", "transcribe.py"]

