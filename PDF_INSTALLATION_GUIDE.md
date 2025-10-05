# BLACK BOX - PDF-Based Installation Guide

## 🎯 Overview

This guide integrates the PDF Jetson setup steps with BLACK BOX deployment. The PDF provides a solid, tested foundation, and this guide adds the specific optimizations needed for BLACK BOX performance.

## 📋 Prerequisites

- NVIDIA Jetson Orin Nano (8GB)
- NVMe SSD (500GB recommended)
- USB Hub with peripherals (microphones, soundbar, fans)
- JetPack 6.0 SD card (flashed and ready)

## 🚀 Installation Process

### Phase 1: PDF Foundation Setup

**Follow the PDF guide exactly for Phases 1-3:**

#### PDF Phase 1: Initial Boot & Network Setup
- Boot from JetPack 6.0 microSD
- Connect to WiFi
- Update system packages
- Basic system configuration

#### PDF Phase 2: Install JetPack SDK
- Install NVIDIA JetPack 6.0 with CUDA 12.4
- This provides the CUDA foundation needed for TensorRT-LLM

#### PDF Phase 3: Install Docker & NVIDIA Container Toolkit
- Install Docker
- Install NVIDIA Container Toolkit
- Configure Docker for GPU access

### Phase 2: BLACK BOX System Optimizations

**After completing PDF Phase 3, apply these optimizations:**

```bash
# 1. Set 15W Power Mode (Critical for performance)
sudo nvpmodel -m 0
echo "✓ Set to 15W power mode"

# 2. Disable GUI (Frees ~1GB RAM)
sudo systemctl set-default multi-user.target
echo "✓ GUI will be disabled on next boot"

# 3. Configure 16GB SWAP (Prevents OOM crashes)
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
echo "✓ 16GB SWAP configured"

# 4. Prepare TensorRT-LLM Environment
git clone https://github.com/dusty-nv/jetson-containers.git
cd jetson-containers
./scripts/install_build_dependencies.sh
cd ..
echo "✓ TensorRT-LLM build environment ready"
```

### Phase 3: Continue PDF Setup

**Continue with PDF Phases 4-6:**

#### PDF Phase 4: Install Python Dependencies
- Install Python 3.10, pip, virtual environments
- Install additional Python packages as needed

#### PDF Phase 5: Install Development Tools
- Install Git, VS Code, build tools
- Install any additional development dependencies

#### PDF Phase 6: Configure Audio System
- **MODIFY THIS STEP** for BLACK BOX hardware:
  - Configure ALSA for MilISO/JOUNIVO USB microphones
  - Configure ALSA for Lielongren USB soundbar
  - Test audio input/output

### Phase 4: BLACK BOX Deployment

**Replace PDF Phase 7 with BLACK BOX deployment:**

```bash
# 1. Clone BLACK BOX repository
cd /opt
sudo git clone <your-repository-url> blackbox
cd blackbox

# 2. Configure environment
cp .env.example .env
nano .env  # Edit configuration as needed

# 3. Build TensorRT-LLM Engine (30-60 minutes)
cd llm-service
./build-trtllm.sh
cd ..

# 4. Build and start services
docker-compose build
docker-compose up -d

# 5. Wait for services to be healthy
sleep 30
docker-compose ps

# 6. Initialize secure database
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_SECURE_PASSWORD'

# 7. Enable auto-start
sudo cp system/blackbox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blackbox.service
```

### Phase 5: Final Configuration

```bash
# 1. Reboot to apply all changes
sudo reboot

# 2. After reboot, verify services
docker-compose ps
curl http://localhost:8000/health

# 3. Test the system
# Open browser to: http://localhost:3000
# Test voice interaction

# 4. Verify installation
./verify-install.sh
```

## 🔧 Audio Configuration (Modified PDF Step 6)

Since BLACK BOX uses specific USB audio devices, modify the PDF's audio configuration:

```bash
# Create ALSA configuration for BLACK BOX hardware
sudo tee /etc/asound.conf > /dev/null <<EOF
# BLACK BOX Audio Configuration
# Input: MilISO/JOUNIVO USB Gooseneck Microphones
# Output: Lielongren USB Mini Soundbar

pcm.!default {
    type asym
    playback.pcm "soundbar"
    capture.pcm "microphone"
}

pcm.soundbar {
    type hw
    card 1
    device 0
}

pcm.microphone {
    type hw
    card 1
    device 0
}

ctl.!default {
    type hw
    card 1
}
EOF

# Test audio configuration
aplay -l  # List playback devices
arecord -l  # List capture devices

# Test audio input
arecord -f cd -d 5 test.wav
aplay test.wav
rm test.wav
```

## 📊 Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| PDF Phases 1-3 | ~1 hour | Foundation setup |
| BLACK BOX Optimizations | ~30 minutes | System tuning |
| PDF Phases 4-6 | ~45 minutes | Development environment |
| BLACK BOX Deployment | ~2-3 hours | Service deployment |
| **Total** | **~4-5 hours** | Complete setup |

## ✅ Verification Checklist

After installation, verify:

- [ ] System boots to console (no GUI)
- [ ] 15W power mode active: `nvpmodel -q`
- [ ] 16GB SWAP active: `free -h`
- [ ] Docker services running: `docker-compose ps`
- [ ] Audio devices detected: `aplay -l && arecord -l`
- [ ] Web UI accessible: `http://localhost:3000`
- [ ] API responding: `curl http://localhost:8000/health`
- [ ] Voice interaction working

## 🚨 Troubleshooting

### Common Issues:

1. **Audio not working**: Check USB device connections and ALSA config
2. **Services not starting**: Check Docker logs: `docker-compose logs`
3. **Performance issues**: Verify 15W power mode and SWAP configuration
4. **GUI still showing**: Reboot required after `systemctl set-default multi-user.target`

### Getting Help:

1. Check logs: `docker-compose logs -f`
2. Run diagnostics: `./verify-install.sh`
3. Check system status: `make status && make health`
4. Review documentation: `README.md`, `TROUBLESHOOTING.md`

## 🎯 Success Criteria

Your BLACK BOX installation is successful when:

- ✅ All services running without errors
- ✅ Voice interaction responds in ≤13 seconds
- ✅ System operates 100% offline
- ✅ Audio input/output working correctly
- ✅ Web UI accessible and functional
- ✅ Auto-start configured for boot

---

**Next Steps**: After successful installation, see `README.md` for usage instructions and `TROUBLESHOOTING.md` for common issues.
