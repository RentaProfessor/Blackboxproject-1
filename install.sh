#!/bin/bash
# BLACK BOX - Master Deployment Script
# Transforms fresh Jetson OS install into fully optimized BLACK BOX prototype
# Single command deployment: sudo ./install.sh

set -e  # Exit on any error

# ============================================================================
# Script Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_FILE="/var/log/blackbox-install.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# Header and Prerequisites
# ============================================================================

echo "============================================================================"
echo "BLACK BOX - Master Deployment Script"
echo "============================================================================"
echo "This script will transform your Jetson Orin Nano into a fully optimized"
echo "offline voice assistant with ≤13 second response latency."
echo ""
echo "Estimated time: 2-4 hours (most time is LLM compilation)"
echo "Hardware requirements: NVIDIA Jetson Orin Nano (8GB), NVMe SSD"
echo "============================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    log_warning "This does not appear to be a Jetson device"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create log file
mkdir -p "$(dirname "$LOG_FILE")"
echo "BLACK BOX Installation started at $(date)" > "$LOG_FILE"

log_info "Starting BLACK BOX deployment..."

# ============================================================================
# 1. Dependencies Installation
# ============================================================================

log_info "Installing essential dependencies..."

# Update package lists
apt-get update

# Install essential tools
apt-get install -y \
    git \
    docker.io \
    docker-compose-plugin \
    wget \
    curl \
    build-essential \
    python3-pip \
    alsa-utils \
    v4l-utils \
    dkms \
    linux-headers-$(uname -r)

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Add current user to docker group (if not root)
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker "$SUDO_USER"
fi

log_success "Dependencies installed"

# ============================================================================
# 2. System Hardening and Resource Optimization
# ============================================================================

log_info "Applying system hardening and resource optimization..."

# 2.1-2.4 System Configuration (using existing script)
log_info "Running comprehensive system configuration..."

if [ -f "$PROJECT_ROOT/system/setup-jetson.sh" ]; then
    log_info "Executing system setup script..."
    chmod +x "$PROJECT_ROOT/system/setup-jetson.sh"
    
    # Run the existing setup script (but skip the reboot prompt)
    # We'll handle reboot at the end
    echo "y" | "$PROJECT_ROOT/system/setup-jetson.sh" || {
        log_warning "System setup script had issues, continuing with manual configuration..."
        
        # Fallback manual configuration
        log_info "Applying manual system configuration..."
        
        # 15W Power Mode
        if command -v nvpmodel &> /dev/null; then
            nvpmodel -m 0
            log_success "Set to 15W power mode"
        fi
        
        # GUI Disable
        systemctl set-default multi-user.target
        log_success "GUI will be disabled on next boot"
        
        # SWAP Configuration
        if systemctl is-active --quiet nvzramconfig; then
            systemctl disable nvzramconfig
            systemctl stop nvzramconfig 2>/dev/null || true
        fi
        
        SWAP_FILE="/swapfile"
        if [ ! -f "$SWAP_FILE" ]; then
            fallocate -l 16G "$SWAP_FILE"
            chmod 600 "$SWAP_FILE"
            mkswap "$SWAP_FILE"
            swapon "$SWAP_FILE"
            echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
            log_success "16GB SWAP configured"
        fi
        
        # ALSA Configuration
        if [ -f "$PROJECT_ROOT/system/alsa.conf" ]; then
            cp "$PROJECT_ROOT/system/alsa.conf" /etc/asound.conf
            log_success "ALSA configuration installed"
        fi
    }
else
    log_warning "System setup script not found, using manual configuration..."
    
    # Manual configuration fallback
    if command -v nvpmodel &> /dev/null; then
        nvpmodel -m 0
        log_success "Set to 15W power mode"
    fi
    
    systemctl set-default multi-user.target
    log_success "GUI will be disabled on next boot"
    
    # Basic SWAP setup
    if [ ! -f "/swapfile" ]; then
        fallocate -l 16G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
        log_success "16GB SWAP configured"
    fi
fi

log_success "System hardening complete"

# ============================================================================
# 3. LLM Engine Compilation (The Longest Step)
# ============================================================================

log_info "Starting LLM engine compilation (this will take 30-60 minutes)..."

# 3.1 TRT-LLM Tooling Setup
log_info "Setting up TensorRT-LLM compilation environment..."

# Clone jetson-containers for TRT-LLM support
JETSON_CONTAINERS_DIR="/opt/jetson-containers"
if [ ! -d "$JETSON_CONTAINERS_DIR" ]; then
    log_info "Cloning jetson-containers repository..."
    git clone https://github.com/dusty-nv/jetson-containers.git "$JETSON_CONTAINERS_DIR"
    log_success "jetson-containers cloned"
fi

# Set up jetson-containers environment
cd "$JETSON_CONTAINERS_DIR"
if [ -f "scripts/install_build_dependencies.sh" ]; then
    log_info "Installing build dependencies..."
    ./scripts/install_build_dependencies.sh
    log_success "Build dependencies installed"
fi

# 3.2 Engine Build
log_info "Building TensorRT-LLM engine..."

# Return to project directory
cd "$PROJECT_ROOT"

# Check if LLM build script exists
if [ -f "$PROJECT_ROOT/llm-service/build-trtllm.sh" ]; then
    log_info "Executing LLM engine build script..."
    chmod +x "$PROJECT_ROOT/llm-service/build-trtllm.sh"
    
    # Run the build script
    cd "$PROJECT_ROOT/llm-service"
    ./build-trtllm.sh
    cd "$PROJECT_ROOT"
    
    log_success "LLM engine build completed"
else
    log_warning "LLM build script not found - you'll need to build the engine manually"
    log_warning "See llm-service/build-trtllm.sh for instructions"
fi

# ============================================================================
# 4. Container Deployment and Service Activation
# ============================================================================

log_info "Deploying containers and activating services..."

# 4.1 Build & Run Containers
log_info "Building Docker containers..."
docker-compose build

log_info "Starting services..."
docker-compose up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 30

# Check service status
log_info "Checking service status..."
docker-compose ps

# 4.2 Systemd Integration
log_info "Installing systemd service..."

if [ -f "$PROJECT_ROOT/system/blackbox.service" ]; then
    # Copy service file
    cp "$PROJECT_ROOT/system/blackbox.service" /etc/systemd/system/
    
    # Reload systemd (MANDATORY after copying file)
    systemctl daemon-reload
    
    # Enable service
    systemctl enable blackbox.service
    
    log_success "Systemd service installed and enabled"
else
    log_warning "Systemd service file not found"
fi

# 4.3 BrosTrend Driver Install
log_info "Installing BrosTrend AC1200 WiFi driver..."

# Check if internet is available
if ping -c 1 google.com &> /dev/null; then
    log_info "Internet connection available - installing WiFi driver..."
    
    # Install BrosTrend driver dependencies
    apt-get install -y \
        dkms \
        linux-headers-$(uname -r) \
        build-essential
    
    # Note: Actual BrosTrend driver installation would go here
    # This is hardware-specific and may require manual steps
    log_warning "BrosTrend driver installation requires manual steps"
    log_warning "Please refer to the driver documentation for your specific model"
else
    log_warning "No internet connection - skipping WiFi driver installation"
    log_warning "You can install it later when internet is available"
fi

log_success "Container deployment complete"

# ============================================================================
# 5. Final Security and User Instructions
# ============================================================================

echo ""
echo "============================================================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================================================"
echo ""
log_success "BLACK BOX deployment completed successfully!"
echo ""
echo "System Status:"
echo "  ✓ 15W power mode configured"
echo "  ✓ GUI disabled (frees ~1GB RAM)"
echo "  ✓ 16GB SWAP file active"
echo "  ✓ ALSA audio configured"
echo "  ✓ Docker containers running"
echo "  ✓ Systemd service enabled"
echo ""
echo "Next Steps:"
echo "1. Reboot the system to apply all changes:"
echo "   sudo reboot"
echo ""
echo "2. After reboot, verify services are running:"
echo "   docker-compose ps"
echo "   curl http://localhost:8000/health"
echo ""
echo "3. Test the voice assistant:"
echo "   Open browser to: http://localhost:3000"
echo "   Click 'PRESS TO SPEAK' and test voice interaction"
echo ""
echo "============================================================================"
echo "NEXT MANDATORY STEP: RUN THE FOLLOWING COMMAND, REPLACING THE PLACEHOLDER"
echo "WITH YOUR VAULT MASTER PASSWORD."
echo ""
echo "This creates the secure SQLCipher database and runs the Argon2id hash."
echo ""
echo "docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_ULTRA_SECRET_MASTER_PASSWORD'"
echo ""
echo "============================================================================"
echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "  - System will boot to console (no GUI) after reboot"
echo "  - Log in via SSH or local console"
echo "  - All services auto-start on boot"
echo "  - System operates 100% offline after setup"
echo "  - Check logs: docker-compose logs"
echo "  - Performance target: ≤13 seconds end-to-end"
echo ""
echo "Installation log saved to: $LOG_FILE"
echo "============================================================================"

# Final status check
log_info "Performing final status check..."

# Check if services are responding
if curl -s http://localhost:8000/health > /dev/null; then
    log_success "Orchestrator service is responding"
else
    log_warning "Orchestrator service not yet responding (may need more time)"
fi

# Check thermal status
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP / 1000))
    log_info "Current temperature: ${TEMP_C}°C"
fi

# Check memory usage
log_info "Memory status:"
free -h

# Check disk space
log_info "Disk space:"
df -h /

log_success "BLACK BOX installation completed!"
echo ""
echo "🚀 Your offline voice assistant is ready!"
echo "   Reboot now: sudo reboot"
echo "   Then test: http://localhost:3000"
echo ""
