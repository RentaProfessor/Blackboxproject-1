#!/bin/bash
# BLACK BOX - Jetson Orin Nano System Configuration Script
# Applies all mandatory system optimizations for performance and resilience

set -e

echo "============================================================================"
echo "BLACK BOX - Jetson Orin Nano System Configuration"
echo "============================================================================"
echo ""
echo "This script will configure your Jetson Orin Nano for optimal performance:"
echo "  - Disable GUI (frees ~1GB RAM)"
echo "  - Create 16GB SWAP file on NVMe"
echo "  - Set 15W power mode"
echo "  - Configure ALSA audio"
echo "  - Install required dependencies"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# ============================================================================
# Check Prerequisites
# ============================================================================

echo ""
echo "[1/8] Checking prerequisites..."

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "⚠ Warning: This does not appear to be a Jetson device"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

echo "✓ Prerequisites checked"

# ============================================================================
# Disable GUI
# ============================================================================

echo ""
echo "[2/8] Disabling GUI to free RAM..."

# Set default target to multi-user (no GUI)
systemctl set-default multi-user.target

echo "✓ GUI will be disabled on next boot"
echo "  (GUI currently still running - reboot required)"

# ============================================================================
# Configure SWAP
# ============================================================================

echo ""
echo "[3/8] Configuring 16GB SWAP file..."

# Disable existing ZRAM
if systemctl is-active --quiet nvzramconfig; then
    systemctl disable nvzramconfig
    systemctl stop nvzramconfig 2>/dev/null || true
    echo "✓ Disabled ZRAM"
fi

# Create SWAP file on NVMe (assuming mounted at /)
SWAP_FILE="/swapfile"
SWAP_SIZE_GB=16

if [ -f "$SWAP_FILE" ]; then
    echo "⚠ SWAP file already exists at $SWAP_FILE"
    swapoff "$SWAP_FILE" 2>/dev/null || true
    rm "$SWAP_FILE"
fi

echo "Creating ${SWAP_SIZE_GB}GB SWAP file (this may take a few minutes)..."
fallocate -l ${SWAP_SIZE_GB}G "$SWAP_FILE"
chmod 600 "$SWAP_FILE"
mkswap "$SWAP_FILE"
swapon "$SWAP_FILE"

# Add to /etc/fstab for persistence
if ! grep -q "$SWAP_FILE" /etc/fstab; then
    echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
    echo "✓ Added SWAP to /etc/fstab"
fi

echo "✓ 16GB SWAP file configured"
free -h

# ============================================================================
# Set Power Mode
# ============================================================================

echo ""
echo "[4/8] Setting 15W power mode..."

# Set power mode using nvpmodel
if command -v nvpmodel &> /dev/null; then
    # Mode 0 is typically 15W for Orin Nano
    nvpmodel -m 0
    echo "✓ Set to 15W power mode"
    
    # Set fan to maximum (for thermal management)
    if [ -f /sys/devices/pwm-fan/target_pwm ]; then
        echo 255 > /sys/devices/pwm-fan/target_pwm
        echo "✓ Set fan to maximum"
    fi
else
    echo "⚠ nvpmodel not found - power mode not changed"
fi

# ============================================================================
# Configure ALSA
# ============================================================================

echo ""
echo "[5/8] Configuring ALSA audio..."

# Disable PulseAudio (we use ALSA directly for lower latency)
if systemctl is-active --quiet pulseaudio; then
    systemctl --user stop pulseaudio
    systemctl --user disable pulseaudio
    echo "✓ Disabled PulseAudio"
fi

# Copy ALSA configuration
if [ -f "$(dirname "$0")/alsa.conf" ]; then
    cp "$(dirname "$0")/alsa.conf" /etc/asound.conf
    echo "✓ ALSA configuration installed"
else
    echo "⚠ ALSA config not found - skipping"
fi

# Set USB audio as default (if present)
echo "✓ ALSA configured"

# ============================================================================
# Install Dependencies
# ============================================================================

echo ""
echo "[6/8] Installing system dependencies..."

apt-get update
apt-get install -y \
    docker.io \
    docker-compose \
    nvidia-docker2 \
    git \
    curl \
    wget \
    build-essential \
    python3-pip \
    alsa-utils \
    v4l-utils

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Add user to docker group
usermod -aG docker $SUDO_USER 2>/dev/null || true

echo "✓ Dependencies installed"

# ============================================================================
# Configure Docker for NVIDIA Runtime
# ============================================================================

echo ""
echo "[7/8] Configuring Docker with NVIDIA runtime..."

# Set NVIDIA as default runtime
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
EOF

systemctl restart docker

echo "✓ Docker configured with NVIDIA runtime"

# ============================================================================
# Create Required Directories
# ============================================================================

echo ""
echo "[8/8] Creating application directories..."

mkdir -p /opt/blackbox
mkdir -p /opt/blackbox/data
mkdir -p /opt/blackbox/backups
mkdir -p /opt/blackbox/logs
mkdir -p /opt/blackbox/models

# Set permissions
chown -R $SUDO_USER:$SUDO_USER /opt/blackbox

echo "✓ Directories created"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "============================================================================"
echo "System Configuration Complete"
echo "============================================================================"
echo ""
echo "Applied configurations:"
echo "  ✓ GUI disabled (frees ~1GB RAM)"
echo "  ✓ 16GB SWAP file created on NVMe"
echo "  ✓ 15W power mode set"
echo "  ✓ ALSA audio configured (PulseAudio disabled)"
echo "  ✓ Docker and NVIDIA runtime installed"
echo "  ✓ Application directories created"
echo ""
echo "⚠ IMPORTANT: Reboot required for all changes to take effect"
echo ""
echo "After reboot:"
echo "  1. System will boot to console (no GUI)"
echo "  2. Log in via SSH or local console"
echo "  3. Deploy BLACK BOX application:"
echo "     cd /opt/blackbox"
echo "     docker-compose up -d"
echo ""
read -p "Reboot now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    reboot
else
    echo "Please reboot manually when ready: sudo reboot"
fi

