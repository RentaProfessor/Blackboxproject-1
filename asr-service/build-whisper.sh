#!/bin/bash
# BLACK BOX - Whisper.cpp Build Script
# Build GPU-accelerated Whisper.cpp for Jetson Orin Nano

set -e

echo "============================================================================"
echo "BLACK BOX - Whisper.cpp Builder"
echo "============================================================================"

# Check for CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: CUDA not found"
    exit 1
fi

echo "✓ CUDA available"

# Build Whisper.cpp with CUDA support
cd /build/whisper.cpp
make clean
WHISPER_CUDA=1 make -j$(nproc)

echo "✓ Whisper.cpp built with CUDA support"

# Download models
MODEL_DIR="/models/whisper"
mkdir -p "${MODEL_DIR}"

echo "Downloading Whisper models..."

# Download tiny.en (fastest, ~75MB)
if [ ! -f "${MODEL_DIR}/ggml-tiny.en.bin" ]; then
    wget -q --show-progress \
        -O "${MODEL_DIR}/ggml-tiny.en.bin" \
        https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
    echo "✓ Downloaded tiny.en model"
fi

# Download base.en (better accuracy, ~142MB)
if [ ! -f "${MODEL_DIR}/ggml-base.en.bin" ]; then
    wget -q --show-progress \
        -O "${MODEL_DIR}/ggml-base.en.bin" \
        https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
    echo "✓ Downloaded base.en model"
fi

echo "============================================================================"
echo "✓ Whisper.cpp build complete"
echo "Models available:"
ls -lh "${MODEL_DIR}"
echo "============================================================================"

