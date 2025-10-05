# BLACK BOX - Scripts Documentation

## 📋 Overview

This document provides comprehensive documentation for all scripts in the BLACK BOX project. These scripts handle system deployment, configuration, maintenance, and troubleshooting for the offline voice assistant running on NVIDIA Jetson Orin Nano.

---

## 🚀 Master Deployment Script

### `install.sh` - Complete System Deployment

**Purpose**: Transforms a fresh Jetson OS installation into a fully optimized BLACK BOX prototype with a single command.

**Location**: `/install.sh` (project root)

**Usage**:
```bash
sudo ./install.sh
```

**What it does**:
1. **NVMe Migration**: Ensures system boots from high-speed NVMe SSD
2. **System Cleanup**: Removes unnecessary packages and Docker artifacts
3. **Health Checks**: Validates system requirements and network connectivity
4. **Dependency Installation**: Installs all required tools and libraries
5. **System Hardening**: Configures 15W power mode, disables GUI, sets up 16GB SWAP
6. **LLM Compilation**: Builds TensorRT-LLM engine (30-60 minutes)
7. **Container Deployment**: Builds and starts all Docker services
8. **Service Integration**: Configures systemd for auto-start

**Prerequisites**:
- NVIDIA Jetson Orin Nano (8GB)
- NVMe SSD installed
- Internet connection (for initial setup)
- Root/sudo access

**Estimated Time**: 2-4 hours (most time is LLM compilation)

**Output**: 
- Installation log: `/var/log/blackbox-install.log`
- All services running and configured
- System ready for voice assistant operation

---

## 🔧 System Configuration Scripts

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

**Key Features**:
- Interactive prompts for user confirmation
- Backup of original configurations
- Validation of hardware compatibility
- Automatic service restart after changes

---

## 🗄️ Database and Vault Scripts

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

## 🎛️ Service Management Scripts

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

## 🔧 Troubleshooting Scripts

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

**Installation Log**:
```bash
# View installation log
tail -f /var/log/blackbox-install.log

# Search for errors
grep -i error /var/log/blackbox-install.log
grep -i warning /var/log/blackbox-install.log
```

---

## 📊 Performance Monitoring Scripts

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

## 🔄 Update and Maintenance Scripts

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

## 🚨 Emergency Recovery Scripts

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

# Re-run installation
sudo ./install.sh
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

## 📝 Script Development Guidelines

### Creating New Scripts

**Script Template**:
```bash
#!/bin/bash
# Script Name - Brief Description
# Detailed description of what the script does

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/blackbox-$(basename "$0" .sh).log"

# Logging functions
log_info() { echo -e "\033[0;34m[INFO]\033[0m $1" | tee -a "$LOG_FILE"; }
log_success() { echo -e "\033[0;32m[SUCCESS]\033[0m $1" | tee -a "$LOG_FILE"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1" | tee -a "$LOG_FILE"; }

# Main script logic here
log_info "Starting script execution..."
# ... script content ...
log_success "Script completed successfully"
```

**Python Script Template**:
```python
#!/usr/bin/env python3
"""
Script Name - Brief Description
Detailed description of what the script does
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("--required-arg", required=True, help="Required argument")
    parser.add_argument("--optional-arg", default="default", help="Optional argument")
    
    args = parser.parse_args()
    
    # Script logic here
    print("Script execution completed")

if __name__ == "__main__":
    main()
```

### Best Practices

1. **Error Handling**: Always use `set -e` in bash scripts
2. **Logging**: Include comprehensive logging with timestamps
3. **Validation**: Validate inputs and prerequisites
4. **Documentation**: Include detailed help and usage examples
5. **Testing**: Test scripts in isolated environments
6. **Permissions**: Use appropriate file permissions
7. **Dependencies**: Document all dependencies clearly

---

## 🔗 Script Dependencies and Workflows

### Installation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    BLACK BOX Installation Workflow          │
└─────────────────────────────────────────────────────────────┘

1. install.sh (Master Script)
   ├── Phase 0: NVMe Migration Check
   │   └── Manual intervention if needed (reboot required)
   │
   ├── Phase 1: System Cleanup
   │   ├── Docker cleanup
   │   ├── Package cache cleanup
   │   └── Log file cleanup
   │
   ├── Phase 2: Health Checks
   │   ├── Network connectivity
   │   ├── System requirements
   │   ├── Package manager health
   │   └── Essential tools check
   │
   ├── Phase 3: System Hardening
   │   ├── DNS resolution fix
   │   ├── Repository cleanup
   │   ├── Core tool installation
   │   └── Docker configuration
   │
   ├── Phase 4: System Configuration
   │   └── system/setup-jetson.sh
   │       ├── 15W power mode
   │       ├── GUI disable
   │       ├── 16GB SWAP setup
   │       └── ALSA configuration
   │
   ├── Phase 5: LLM Compilation
   │   └── llm-service/build-trtllm.sh
   │       ├── TensorRT-LLM setup
   │       ├── Model download
   │       ├── Engine compilation
   │       └── Performance validation
   │
   ├── Phase 6: Container Deployment
   │   ├── Docker build
   │   ├── Service startup
   │   ├── Systemd integration
   │   └── WiFi driver setup
   │
   └── Phase 7: Final Instructions
       └── Manual database initialization required

2. Manual Steps (After install.sh)
   └── scripts/init_vault_setup.py
       ├── Database creation
       ├── Schema setup
       ├── User profile creation
       └── Vault system initialization

3. Verification
   └── verify-install.sh
       ├── Service status check
       ├── Health endpoint validation
       ├── Audio device verification
       ├── GPU status check
       └── Performance validation
```

### Daily Operations Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Operations Workflow                │
└─────────────────────────────────────────────────────────────┘

Startup:
├── make start (or systemd auto-start)
│   ├── docker-compose up -d
│   ├── Service health checks
│   └── Status verification
│
├── make status
│   ├── docker-compose ps
│   └── Health endpoint check
│
└── make health
    ├── Performance metrics
    ├── Thermal status
    └── Resource usage

Monitoring:
├── make logs (real-time monitoring)
├── make metrics (performance data)
├── make thermal (temperature check)
└── ./verify-install.sh (comprehensive check)

Maintenance:
├── make backup (database backup)
├── make clean (cleanup containers)
└── make restart (service restart)

Testing:
└── make test (voice assistant test)
```

### Troubleshooting Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Troubleshooting Workflow                 │
└─────────────────────────────────────────────────────────────┘

Issue Detection:
├── ./verify-install.sh (comprehensive diagnostics)
├── make status (service status)
├── make health (system health)
└── make logs (error investigation)

Service Issues:
├── docker-compose ps (container status)
├── docker-compose logs [service] (specific logs)
├── make restart (service restart)
└── docker-compose down && docker-compose up -d (full restart)

Audio Issues:
├── Check ALSA configuration
├── Verify USB device detection
├── Test audio devices manually
└── Review audio service logs

GPU Issues:
├── nvidia-smi (GPU status)
├── Check CUDA installation
├── Monitor GPU memory usage
└── Review AI service logs

Performance Issues:
├── make metrics (performance data)
├── make thermal (temperature check)
├── Monitor system resources
└── Check for thermal throttling

Database Issues:
├── Check encryption key
├── Verify database permissions
├── Review database logs
└── Re-run init_vault_setup.py if needed
```

### Installation Order

1. **`install.sh`** - Master deployment script
2. **`system/setup-jetson.sh`** - System configuration (called by install.sh)
3. **`llm-service/build-trtllm.sh`** - LLM engine build (called by install.sh)
4. **`asr-service/build-whisper.sh`** - ASR engine build (called by install.sh)
5. **`scripts/init_vault_setup.py`** - Database initialization (manual step)
6. **`verify-install.sh`** - Installation verification

### Runtime Dependencies

- **Docker**: All services require Docker and docker-compose
- **CUDA**: AI services require CUDA runtime
- **ALSA**: Audio services require ALSA configuration
- **Systemd**: Auto-start requires systemd service

---

## 📞 Support and Troubleshooting

### Comprehensive Troubleshooting Guide

#### 1. Installation Issues

**Problem**: `install.sh` fails during execution
```bash
# Check installation log
tail -f /var/log/blackbox-install.log

# Common fixes:
# - Ensure running as root: sudo ./install.sh
# - Check internet connection
# - Verify Jetson device compatibility
# - Ensure sufficient disk space (20GB+)
```

**Problem**: NVMe migration required
```bash
# Follow the manual steps in install.sh output:
# 1. Edit /boot/extlinux/extlinux.conf
# 2. Change root=/dev/mmcblk0p1 to root=/dev/nvme0n1p1
# 3. Reboot and run install.sh again
```

**Problem**: Docker installation fails
```bash
# Clean up and retry
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

#### 2. Service Issues

**Problem**: Services won't start
```bash
# Check Docker status
sudo systemctl status docker
docker --version
docker-compose --version

# Check service status
docker-compose ps
docker-compose logs

# Restart services
make restart
# or
docker-compose down && docker-compose up -d
```

**Problem**: Specific service failing
```bash
# Check individual service logs
docker-compose logs orchestrator
docker-compose logs llm-service
docker-compose logs asr-service
docker-compose logs tts-service
docker-compose logs ui

# Restart specific service
docker-compose restart [service-name]
```

**Problem**: Services start but not responding
```bash
# Check health endpoints
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # ASR
curl http://localhost:8002/health  # LLM
curl http://localhost:8003/health  # TTS
curl http://localhost:3000         # UI

# Check port conflicts
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000
```

#### 3. Audio Issues

**Problem**: No audio input/output
```bash
# Check ALSA devices
aplay -l
arecord -l

# Test audio devices
speaker-test -c 2 -t wav
arecord -f cd -d 5 test.wav && aplay test.wav

# Check USB audio devices
lsusb | grep -i audio
lsusb | grep -i sound

# Restart audio services
sudo systemctl restart alsa-state
```

**Problem**: Audio latency issues
```bash
# Check ALSA configuration
cat /etc/asound.conf

# Verify direct ALSA routing (no PulseAudio)
ps aux | grep pulseaudio
sudo systemctl stop pulseaudio
sudo systemctl disable pulseaudio
```

**Problem**: USB audio not detected
```bash
# Check USB hub power
# Ensure externally powered USB 3.0 hub
# Check USB device connections
# Try different USB ports
```

#### 4. GPU and AI Issues

**Problem**: CUDA not working
```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Check GPU memory
nvidia-smi -q -d MEMORY

# Restart NVIDIA services
sudo systemctl restart nvidia-persistenced
```

**Problem**: LLM service GPU errors
```bash
# Check GPU memory usage
nvidia-smi

# Check LLM service logs
docker-compose logs llm-service

# Verify TensorRT-LLM installation
docker-compose exec llm-service nvidia-smi

# Rebuild LLM engine if needed
cd llm-service
./build-trtllm.sh
```

**Problem**: ASR service GPU errors
```bash
# Check ASR service logs
docker-compose logs asr-service

# Verify Whisper build
docker-compose exec asr-service ls -la /app/models/

# Rebuild Whisper if needed
cd asr-service
./build-whisper.sh
```

#### 5. Performance Issues

**Problem**: Slow response times
```bash
# Check system resources
htop
free -h
df -h

# Check thermal status
cat /sys/class/thermal/thermal_zone*/temp
make thermal

# Check GPU utilization
nvidia-smi -l 1

# Monitor performance metrics
make metrics
```

**Problem**: Thermal throttling
```bash
# Check temperature
cat /sys/class/thermal/thermal_zone*/temp

# Check fan status
cat /sys/class/hwmon/hwmon*/fan*_input

# Verify USB fans are running
# Check power mode
nvpmodel -q
```

**Problem**: Memory issues
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Check SWAP usage
swapon -s
cat /proc/swaps

# Verify 16GB SWAP is active
ls -la /swapfile
```

#### 6. Database Issues

**Problem**: Database initialization fails
```bash
# Check encryption key
echo $DATABASE_ENCRYPTION_KEY

# Verify .env file
cat .env | grep DATABASE_ENCRYPTION_KEY

# Check database permissions
ls -la /data/
sudo chown -R 1000:1000 /data/

# Re-run initialization
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_PASSWORD'
```

**Problem**: Vault access issues
```bash
# Check database logs
docker-compose logs orchestrator | grep -i database

# Verify database file
ls -la /data/blackbox.db

# Test database connection
docker-compose exec orchestrator python3 -c "
from database.db import Database
db = Database('/data/blackbox.db', 'your_key')
print('Database connection OK')
"
```

#### 7. Network and Connectivity Issues

**Problem**: No internet during setup
```bash
# Check network connectivity
ping -c 1 8.8.8.8
ping -c 1 google.com

# Check DNS resolution
nslookup google.com

# Fix DNS if needed
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
```

**Problem**: WiFi driver issues
```bash
# Check WiFi adapter
lsusb | grep -i wifi
lsusb | grep -i brostrend

# Check driver status
lsmod | grep rtl
dmesg | grep -i wifi

# Install driver manually if needed
# (Refer to BrosTrend documentation)
```

#### 8. System Configuration Issues

**Problem**: GUI not disabled
```bash
# Check current target
systemctl get-default

# Set to multi-user target
sudo systemctl set-default multi-user.target

# Reboot to apply
sudo reboot
```

**Problem**: Power mode not set
```bash
# Check current power mode
nvpmodel -q

# Set to 15W mode
sudo nvpmodel -m 0

# Verify
nvpmodel -q
```

**Problem**: SWAP not configured
```bash
# Check SWAP status
swapon -s
free -h

# Create SWAP if missing
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
```

### Diagnostic Commands

**Quick System Check**:
```bash
# Run comprehensive diagnostics
./verify-install.sh

# Check all services
make status && make health

# View recent logs
make logs | tail -100
```

**Performance Monitoring**:
```bash
# Real-time monitoring
watch -n 1 'nvidia-smi && echo "---" && free -h && echo "---" && cat /sys/class/thermal/thermal_zone*/temp'

# Performance metrics
make metrics | python3 -m json.tool
```

**Log Analysis**:
```bash
# Search for errors
docker-compose logs | grep -i error
docker-compose logs | grep -i warning
docker-compose logs | grep -i failed

# Installation log analysis
grep -i error /var/log/blackbox-install.log
grep -i warning /var/log/blackbox-install.log
```

### Emergency Recovery

**Complete System Reset**:
```bash
# Stop all services
docker-compose down

# Remove all data
sudo rm -rf /data/blackbox.db
sudo rm -rf /opt/blackbox/models/

# Clean Docker
docker system prune -a -f

# Re-run installation
sudo ./install.sh
```

**Service Recovery**:
```bash
# Restart all services
make restart

# If that fails, full restart
docker-compose down
docker-compose build
docker-compose up -d
```

**Database Recovery**:
```bash
# Stop orchestrator
docker-compose stop orchestrator

# Remove database
sudo rm -f /data/blackbox.db

# Restart orchestrator
docker-compose start orchestrator

# Re-initialize database
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_PASSWORD'
```

### Getting Help

1. **Check logs**: `make logs` or `docker-compose logs`
2. **Run diagnostics**: `./verify-install.sh`
3. **Check documentation**: README.md, SCRIPT_README.md, and TROUBLESHOOTING.md
4. **Review installation log**: `/var/log/blackbox-install.log`
5. **Search for specific errors**: Use grep to find error patterns
6. **Check system resources**: Monitor CPU, memory, GPU, and thermal status

---

## 🎯 Script Performance Targets

| Script | Purpose | Target Time | Success Criteria |
|--------|---------|-------------|------------------|
| `install.sh` | Full deployment | 2-4 hours | All services running |
| `build-trtllm.sh` | LLM compilation | 30-60 min | ≥25 tok/s throughput |
| `build-whisper.sh` | ASR compilation | 10-20 min | ≤2.5s transcription |
| `init_vault_setup.py` | DB initialization | <30 seconds | Encrypted DB created |
| `verify-install.sh` | System verification | <2 minutes | All checks pass |

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
