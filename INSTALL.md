# BLACK BOX - Installation Guide

## Single Command Deployment

The BLACK BOX project includes a master deployment script that transforms a fresh Jetson OS install into a fully optimized voice assistant in one command.

## Prerequisites

### Hardware
- NVIDIA Jetson Orin Nano Developer Kit (8GB)
- SK Hynix Gold P31 NVMe SSD (500GB) - installed
- Externally powered USB 3.0 hub
- USB microphone and soundbar connected to hub
- USB cooling fans (2x) connected to hub
- Display, keyboard, mouse (for initial setup)

### Software
- Fresh Ubuntu 22.04 + JetPack SDK installation
- Internet connection (for initial setup only)

## Installation

### Step 1: Clone Repository
```bash
# Create application directory
sudo mkdir -p /opt/blackbox
cd /opt/blackbox

# Clone repository
git clone <repository-url> .

# Or copy from USB drive
# cp -r /media/usb/blackbox/* .
```

### Step 2: Run Master Installation Script
```bash
# Make script executable
chmod +x install.sh

# Run the master installation script
sudo ./install.sh
```

**That's it!** The script will:
- Install all dependencies
- Configure system for optimal performance
- Build TensorRT-LLM engine (30-60 minutes)
- Deploy all services
- Set up auto-start

### Step 3: Reboot and Initialize
```bash
# Reboot to apply all changes
sudo reboot

# After reboot, initialize the database
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_SECURE_PASSWORD'
```

### Step 4: Test System
```bash
# Check services are running
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health

# Open UI in browser
# Navigate to: http://localhost:3000
```

## What the Install Script Does

### 1. Dependencies Installation
- Installs Docker, git, build tools
- Configures NVIDIA Docker runtime
- Installs audio utilities

### 2. System Optimization
- Sets 15W power mode for maximum GPU performance
- Disables GUI to free ~1GB RAM
- Creates 16GB SWAP file on NVMe
- Configures ALSA audio (disables PulseAudio)
- Sets up thermal management

### 3. LLM Engine Compilation
- Clones jetson-containers repository
- Builds TensorRT-LLM with INT4 quantization
- Compiles Llama 3.2 3B or Phi 3.5 3B model
- Optimizes for ≥25 tokens/second performance

### 4. Service Deployment
- Builds all Docker containers
- Starts all services with restart policies
- Configures systemd for auto-start
- Sets up shared memory IPC

### 5. Security Setup
- Creates encrypted SQLCipher database
- Initializes Argon2id password hashing
- Sets up secure vault system

## Installation Time

- **Total time**: 2-4 hours
- **System setup**: 15 minutes
- **LLM compilation**: 30-60 minutes (longest step)
- **Service deployment**: 30 minutes
- **Final configuration**: 5 minutes

## Troubleshooting

### If Installation Fails
```bash
# Check installation log
tail -f /var/log/blackbox-install.log

# Check Docker status
sudo systemctl status docker

# Check services
docker-compose ps
```

### Common Issues
1. **Out of disk space**: Ensure 50GB+ free space
2. **GPU not detected**: Verify JetPack SDK installed
3. **Audio issues**: Check USB device connections
4. **LLM build fails**: Check TensorRT-LLM requirements

### Manual Recovery
If the install script fails, you can run individual components:
```bash
# System configuration
sudo ./system/setup-jetson.sh

# Build services
docker-compose build

# Start services
docker-compose up -d
```

## Post-Installation

### System Status
After installation, the system will:
- Boot to console (no GUI)
- Auto-start all services
- Operate 100% offline
- Monitor thermal status
- Provide voice assistant functionality

### Performance Verification
```bash
# Check performance metrics
curl http://localhost:8000/metrics

# Expected performance:
# - ASR: ≤2.5 seconds
# - LLM: ≤7.5 seconds (≥25 tok/s)
# - TTS: ≤1.5 seconds
# - Total: ≤13 seconds
```

### Maintenance
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Update system
git pull && docker-compose build && docker-compose up -d
```

## Security Notes

- Database is encrypted with AES-256
- All data stored locally (no cloud)
- Vault protected with Argon2id hashing
- System operates offline after setup

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Review troubleshooting guide: `docs/TROUBLESHOOTING.md`
3. Check system status: `curl http://localhost:8000/health`

---

**Your BLACK BOX offline voice assistant is ready!** 🎉
