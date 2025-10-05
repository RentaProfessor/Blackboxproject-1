# BLACK BOX - Scripts Documentation

## 📋 Overview

This document provides documentation for the key scripts in the BLACK BOX project. These scripts handle system configuration, maintenance, and troubleshooting for the offline voice assistant running on NVIDIA Jetson Orin Nano.

**Note**: BLACK BOX now uses a PDF-guided installation approach. See `PDF_INSTALLATION_GUIDE.md` for complete installation instructions.

---

## 🚀 System Configuration Scripts

### `setup-blackbox.sh` - BLACK BOX System Optimizations

**Purpose**: Applies BLACK BOX-specific system optimizations after PDF setup phases.

**Location**: `/setup-blackbox.sh` (project root)

**Usage**:
```bash
sudo ./setup-blackbox.sh
```

**What it does**:
1. **Power Mode**: Sets to 15W sustained mode (`nvpmodel -m 0`)
2. **GUI Disable**: Disables desktop environment to free ~1GB RAM
3. **SWAP Configuration**: Creates 16GB SWAP file on NVMe
4. **TensorRT-LLM Environment**: Prepares build environment

**Prerequisites**:
- PDF Phases 1-3 completed
- NVIDIA Jetson Orin Nano (8GB)
- Root/sudo access

**Estimated Time**: 30 minutes

---

### `system/setup-jetson.sh` - Jetson-Specific Configuration

**Purpose**: Configures Jetson-specific settings for optimal performance.

**Location**: `/system/setup-jetson.sh`

**Usage**:
```bash
sudo ./system/setup-jetson.sh
```

**Configuration Changes**:
- **Power Mode**: Sets to 15W sustained mode (`nvpmodel -m 0`)
- **GUI Disable**: Disables desktop environment to free ~1GB RAM
- **SWAP Configuration**: Creates 16GB SWAP file on NVMe
- **ALSA Audio**: Configures direct ALSA audio routing
- **Thermal Management**: Sets up fan control and monitoring

**Note**: This script is now optional since `setup-blackbox.sh` handles the same optimizations.

---

## 🗄️ Database Scripts

### `scripts/init_vault_setup.py` - Database Initialization

**Purpose**: Creates the secure SQLCipher database and initializes the vault system.

**Location**: `/scripts/init_vault_setup.py`

**Usage**:
```bash
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_SECURE_PASSWORD'
```

**What it does**:
1. **Database Creation**: Creates encrypted SQLCipher database
2. **Schema Setup**: Initializes all required tables and indexes
3. **User Profile**: Creates default user profile
4. **Vault System**: Sets up secure storage with Argon2id hashing
5. **Testing**: Validates all functionality with test data

**Security Features**:
- AES-256 encryption for all data
- Argon2id password hashing
- Secure key derivation
- Encrypted vault storage

**Requirements**:
- All services must be running (`docker-compose up -d`)
- `DATABASE_ENCRYPTION_KEY` must be set in `.env` file
- Master password must be 8-128 characters

---

## 🏗️ Build Scripts

### `llm-service/build-trtllm.sh` - TensorRT-LLM Engine Builder

**Purpose**: Compiles and optimizes the LLM inference engine for maximum performance.

**Location**: `/llm-service/build-trtllm.sh`

**Usage**:
```bash
cd llm-service
./build-trtllm.sh
```

**What it does**:
1. **Model Download**: Downloads Llama 3.2 3B or Phi 3.5 3B model
2. **TRT-LLM Setup**: Configures TensorRT-LLM compilation environment
3. **Engine Compilation**: Builds optimized INT4 quantized engine
4. **Performance Validation**: Tests for ≥25 tokens/second throughput
5. **Storage**: Saves compiled engine for production use

**Performance Targets**:
- **Throughput**: ≥25 tokens/second sustained
- **Memory Usage**: ~2.5GB GPU memory
- **Quantization**: INT4 for optimal speed/size ratio
- **Compilation Time**: 30-60 minutes (one-time)

**Requirements**:
- NVIDIA Jetson with JetPack SDK
- 8GB+ GPU memory available
- Internet connection for model download
- Sufficient disk space (~15GB for models)

---

### `asr-service/build-whisper.sh` - Whisper.cpp GPU Build

**Purpose**: Builds GPU-accelerated Whisper.cpp for speech recognition.

**Location**: `/asr-service/build-whisper.sh`

**Usage**:
```bash
cd asr-service
./build-whisper.sh
```

**What it does**:
1. **CUDA Setup**: Configures CUDA compilation environment
2. **Whisper Build**: Compiles Whisper.cpp with GPU acceleration
3. **Model Download**: Downloads `tiny.en` or `base.en` model
4. **Optimization**: Applies Jetson-specific optimizations
5. **Testing**: Validates ASR performance

**Performance Targets**:
- **Latency**: ≤2.5 seconds transcription
- **Memory Usage**: ~1GB GPU memory
- **Accuracy**: Optimized for English speech
- **Real-time**: Streaming audio processing

---

## 🎛️ Service Scripts

### `ui/start-ui.sh` - UI Service Launcher

**Purpose**: Starts the Chromium kiosk UI in fullscreen mode.

**Location**: `/ui/start-ui.sh`

**Usage**:
```bash
cd ui
./start-ui.sh
```

**What it does**:
1. **Display Setup**: Configures display for kiosk mode
2. **Chromium Launch**: Starts Chromium in fullscreen
3. **UI Loading**: Loads the senior-friendly interface
4. **Auto-refresh**: Handles connection issues gracefully

**UI Features**:
- Fullscreen kiosk mode
- Large, high-contrast buttons
- Voice interaction interface
- Status indicators and feedback

---

## 🔍 Health Check Scripts

### `verify-install.sh` - Installation Verification

**Purpose**: Verifies that all components are properly installed and configured.

**Location**: `/verify-install.sh`

**Usage**:
```bash
./verify-install.sh
```

**Verification Checks**:
1. **Service Status**: All Docker containers running
2. **Health Endpoints**: API endpoints responding
3. **Audio Devices**: USB audio devices detected
4. **GPU Status**: CUDA and GPU memory available
5. **Performance**: Basic latency measurements
6. **Database**: Encrypted database accessible
7. **Thermal**: Temperature within safe limits

**Output**: Detailed report of system status and any issues found.

---

## 🛠️ Maintenance Scripts

### Makefile Commands

**Location**: `/Makefile`

**Available Commands**:

```bash
# Service Management
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make status         # Check service status
make logs           # View all service logs

# Health and Monitoring
make health         # Check system health
make metrics        # View performance metrics
make thermal        # Check thermal status

# Development
make build          # Build all Docker images
make test           # Run test suite
make clean          # Clean up containers and volumes

# Backup and Maintenance
make backup         # Backup database
make setup          # Run system setup (requires sudo)
make install-service # Install systemd service
```

**Usage Examples**:
```bash
# Check if everything is working
make status && make health

# View real-time logs
make logs

# Test the voice assistant
make test

# Create database backup
make backup
```

---

## 🔧 Troubleshooting Commands

### Service Health Checks

**Individual Service Health**:
```bash
# Check orchestrator
curl http://localhost:8000/health

# Check ASR service
curl http://localhost:8001/health

# Check LLM service
curl http://localhost:8002/health

# Check TTS service
curl http://localhost:8003/health

# Check UI service
curl http://localhost:3000
```

**System Diagnostics**:
```bash
# Check Docker status
docker-compose ps
docker-compose logs

# Check GPU status
nvidia-smi

# Check thermal status
cat /sys/class/thermal/thermal_zone*/temp

# Check memory usage
free -h

# Check disk space
df -h
```

### Log Analysis

**View Service Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
docker-compose logs -f llm-service
docker-compose logs -f asr-service
docker-compose logs -f tts-service
docker-compose logs -f ui
```

---

## 📊 Performance Monitoring

### Real-time Monitoring

**Performance Metrics**:
```bash
# Get current performance metrics
curl http://localhost:8000/metrics | python3 -m json.tool

# Check thermal status
curl http://localhost:8000/thermal/status | python3 -m json.tool

# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor system resources
htop
```

**Latency Testing**:
```bash
# Test ASR latency
curl -X POST http://localhost:8000/audio/transcribe \
  -F "audio=@test_audio.wav" \
  -w "Time: %{time_total}s\n"

# Test LLM response time
curl -X POST http://localhost:8000/text/interact \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?"}' \
  -w "Time: %{time_total}s\n"
```

---

## 🔄 Update and Maintenance

### System Updates

**Software Updates** (when internet available):
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker-compose pull
docker-compose build
docker-compose restart
```

**Model Updates**:
```bash
# Update LLM model
cd llm-service
./build-trtllm.sh

# Update ASR model
cd asr-service
./build-whisper.sh

# Restart services
make restart
```

### Backup and Recovery

**Database Backup**:
```bash
# Manual backup
make backup

# Automated backup (daily)
# Add to crontab:
0 2 * * * cd /opt/blackbox && make backup
```

**Full System Backup**:
```bash
# Backup entire system
sudo tar -czf blackbox-backup-$(date +%Y%m%d).tar.gz \
  /opt/blackbox \
  /etc/systemd/system/blackbox.service \
  /etc/asound.conf
```

---

## 🚨 Emergency Recovery

### Service Recovery

**Restart All Services**:
```bash
# Stop everything
docker-compose down

# Clean up
docker system prune -f

# Rebuild and start
docker-compose build
docker-compose up -d
```

**Reset to Factory State**:
```bash
# Stop services
docker-compose down

# Remove all data
sudo rm -rf /data/blackbox.db
sudo rm -rf /opt/blackbox/models/

# Follow PDF_INSTALLATION_GUIDE.md to reinstall
```

### Database Recovery

**Reset Database**:
```bash
# Stop services
docker-compose stop orchestrator

# Remove database
sudo rm -f /data/blackbox.db

# Restart services
docker-compose start orchestrator

# Re-initialize database
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_PASSWORD'
```

---

## 🎯 Script Performance Targets

| Script | Purpose | Target Time | Success Criteria |
|--------|---------|-------------|------------------|
| `setup-blackbox.sh` | System optimization | 30 minutes | System optimized |
| `build-trtllm.sh` | LLM compilation | 30-60 min | ≥25 tok/s throughput |
| `build-whisper.sh` | ASR compilation | 10-20 min | ≤2.5s transcription |
| `init_vault_setup.py` | DB initialization | <30 seconds | Encrypted DB created |
| `verify-install.sh` | System verification | <2 minutes | All checks pass |

---

## 📞 Support and Troubleshooting

### Getting Help

1. **Check logs**: `make logs` or `docker-compose logs`
2. **Run diagnostics**: `./verify-install.sh`
3. **Check documentation**: README.md, PDF_INSTALLATION_GUIDE.md, and TROUBLESHOOTING.md
4. **Search for specific errors**: Use grep to find error patterns
5. **Check system resources**: Monitor CPU, memory, GPU, and thermal status

### Common Issues

**Services not starting**:
```bash
# Check Docker status
sudo systemctl status docker
docker-compose ps
docker-compose logs
```

**Audio issues**:
```bash
# Check ALSA devices
aplay -l
arecord -l

# Test audio devices
speaker-test -c 2 -t wav
arecord -f cd -d 5 test.wav && aplay test.wav
```

**GPU issues**:
```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Check GPU memory
nvidia-smi -q -d MEMORY
```

**Performance issues**:
```bash
# Check system resources
htop
free -h
df -h

# Check thermal status
cat /sys/class/thermal/thermal_zone*/temp
```

---

**Version**: 1.0.0  
**Last Updated**: October 3, 2025  
**Target Hardware**: NVIDIA Jetson Orin Nano (8GB)  
**Status**: Production Ready

---

## ⚠️ Important Notes

- **Root Access**: Most scripts require sudo/root access
- **Internet Required**: Initial setup requires internet for downloads
- **Hardware Specific**: Scripts are optimized for Jetson Orin Nano
- **Backup First**: Always backup before running major scripts
- **Read Logs**: Check logs for detailed error information

**DO NOT** run scripts without understanding their purpose and requirements.