#!/bin/bash
# BLACK BOX - Manual Setup Script
# Apply BLACK BOX optimizations after PDF Phases 1-3
# Safe, controlled setup without dangerous operations

set -e

echo "============================================================================"
echo "BLACK BOX - Manual Setup Script"
echo "============================================================================"
echo ""
echo "This script applies BLACK BOX optimizations after PDF setup."
echo "Prerequisites: PDF Phases 1-3 must be completed first."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "⚠ Warning: This does not appear to be a Jetson device"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "============================================================================"
echo "Applying BLACK BOX System Optimizations"
echo "============================================================================"

# 1. Set 15W Power Mode
echo ""
echo "[1/4] Setting 15W power mode..."
if command -v nvpmodel &> /dev/null; then
    nvpmodel -m 0
    echo "✓ Set to 15W power mode"
else
    echo "⚠ nvpmodel not found - power mode not changed"
fi

# 2. Disable GUI
echo ""
echo "[2/4] Disabling GUI to free RAM..."
systemctl set-default multi-user.target
echo "✓ GUI will be disabled on next boot"

# 3. Configure SWAP
echo ""
echo "[3/4] Configuring 16GB SWAP file..."
if [ -f "/swapfile" ]; then
    echo "⚠ SWAP file already exists"
    swapoff /swapfile 2>/dev/null || true
    rm /swapfile
fi

echo "Creating 16GB SWAP file..."
fallocate -l 16G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Add to /etc/fstab if not already there
if ! grep -q "/swapfile" /etc/fstab; then
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
    echo "✓ Added SWAP to /etc/fstab"
fi

echo "✓ 16GB SWAP configured"
free -h

# 4. Prepare TensorRT-LLM Environment
echo ""
echo "[4/4] Preparing TensorRT-LLM build environment..."
if [ ! -d "/opt/jetson-containers" ]; then
    echo "Cloning jetson-containers repository..."
    git clone https://github.com/dusty-nv/jetson-containers.git /opt/jetson-containers
    echo "✓ jetson-containers cloned"
else
    echo "✓ jetson-containers already exists"
fi

cd /opt/jetson-containers
if [ -f "scripts/install_build_dependencies.sh" ]; then
    echo "Installing build dependencies..."
    ./scripts/install_build_dependencies.sh
    echo "✓ Build dependencies installed"
else
    echo "⚠ Build dependencies script not found"
fi

echo ""
echo "============================================================================"
echo "BLACK BOX Optimizations Complete"
echo "============================================================================"
echo ""
echo "Applied optimizations:"
echo "  ✓ 15W power mode set"
echo "  ✓ GUI disabled (frees ~1GB RAM)"
echo "  ✓ 16GB SWAP file created"
echo "  ✓ TensorRT-LLM build environment ready"
echo ""
echo "Next steps:"
echo "  1. Continue with PDF Phases 4-6"
echo "  2. Deploy BLACK BOX services"
echo "  3. Reboot to apply GUI changes"
echo ""
echo "⚠ IMPORTANT: Reboot required for GUI changes to take effect"
echo ""
read -p "Reboot now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    reboot
else
    echo "Please reboot manually when ready: sudo reboot"
fi
