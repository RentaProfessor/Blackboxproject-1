# BLACK BOX LLM Service - TensorRT-LLM Inference
# Optimized for NVIDIA Jetson Orin Nano with INT4 quantization

FROM nvcr.io/nvidia/l4t-tensorrt:r8.6.2-runtime

LABEL maintainer="BLACK BOX Project"
LABEL description="TensorRT-LLM optimized inference service"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    build-essential \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Install TensorRT-LLM dependencies
RUN pip install --no-cache-dir \
    tensorrt==8.6.2 \
    torch==2.0.1 \
    transformers==4.35.0 \
    accelerate==0.24.0 \
    sentencepiece==0.1.99 \
    protobuf==3.20.3 \
    numpy==1.24.3 \
    pydantic==2.5.0 \
    fastapi==0.104.1 \
    uvicorn==0.24.0

# Create application directory
WORKDIR /app

# Copy service code
COPY inference.py .
COPY healthcheck.py .
COPY requirements.txt .

# Install additional requirements
RUN pip install --no-cache-dir -r requirements.txt

# Create model directory
RUN mkdir -p /models/engines

# Expose service port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python healthcheck.py || exit 1

# Run inference service
CMD ["python", "inference.py"]

