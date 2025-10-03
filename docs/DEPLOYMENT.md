# BLACK BOX - Deployment Guide

Complete step-by-step deployment instructions for the BLACK BOX voice assistant on NVIDIA Jetson Orin Nano.

---

## Prerequisites

### Hardware Requirements
- ✅ NVIDIA Jetson Orin Nano Developer Kit (8GB)
- ✅ SK Hynix Gold P31 NVMe SSD (500GB) - installed
- ✅ Externally Powered USB 3.0 Hub
- ✅ Lielongren USB Mini Soundbar
- ✅ MilISO/JOUNIVO USB Gooseneck Microphone
- ✅ 2x Wathai USB Fans (40x10mm)
- ✅ BrosTrend AC1200 WiFi USB Adapter (for initial setup)
- ✅ Display, keyboard, mouse (for initial setup)

### Software Requirements
- Ubuntu 22.04 + JetPack SDK (pre-installed on Jetson)
- Minimum 50GB free space on NVMe SSD

---

## Phase 1: Hardware Setup

### 1.1 Physical Assembly

1. **Install NVMe SSD**
   - Power off Jetson
   - Install SK Hynix Gold P31 in M.2 slot
   - Secure with provided screw
   - Power on and verify detection: `lsblk`

2. **Connect USB Hub**
   - Connect externally powered USB 3.0 hub to Jetson
   - Ensure hub has its own power adapter connected
   - Verify power indicator on hub

3. **Connect Audio Devices**
   - Connect USB microphone to hub
   - Connect USB soundbar to hub
   - Connect USB fans to hub
   - Verify all devices: `lsusb`

4. **Identify Audio Devices**
   ```bash
   # List output devices
   aplay -l
   
   # List input devices
   arecord -l
   
   # Note the card numbers for your devices
   # Update .env file accordingly
   ```

5. **Connect WiFi Adapter**
   - Connect BrosTrend WiFi adapter
   - Configure network (for initial setup only)
   - Will be disconnected after deployment

### 1.2 Verify Hardware

```bash
# Check NVMe SSD
lsblk | grep nvme

# Check USB devices
lsusb

# Check audio devices
aplay -l
arecord -l

# Check thermal zones
cat /sys/class/thermal/thermal_zone*/temp

# Check GPU
nvidia-smi
```

---

## Phase 2: System Configuration

### 2.1 Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/blackbox
cd /opt/blackbox

# Clone repository (or copy files)
git clone <repository-url> .

# Alternatively, if copying from USB drive:
# cp -r /media/usb/blackbox/* /opt/blackbox/
```

### 2.2 Run System Configuration Script

```bash
# Make script executable
chmod +x system/setup-jetson.sh

# Run configuration script (requires sudo)
sudo ./system/setup-jetson.sh
```

This script will:
- Disable GUI (frees ~1GB RAM)
- Create 16GB SWAP file
- Set 15W power mode
- Configure ALSA audio
- Install Docker and dependencies
- Set up application directories

**⚠️ IMPORTANT: Reboot after this step**

```bash
sudo reboot
```

### 2.3 Post-Reboot Verification

After reboot, system will boot to console (no GUI).

```bash
# Verify GUI is disabled
systemctl get-default
# Should output: multi-user.target

# Verify SWAP
free -h
# Should show ~16GB swap

# Verify power mode
sudo nvpmodel -q
# Should show mode 0 (15W)

# Verify Docker
docker --version
docker-compose --version
```

---

## Phase 3: Application Configuration

### 3.1 Configure Environment Variables

```bash
cd /opt/blackbox

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Critical Settings to Configure:**

```bash
# Generate encryption key
DATABASE_ENCRYPTION_KEY=$(openssl rand -hex 32)

# Update audio device paths (from Phase 1.1 step 4)
ALSA_INPUT_DEVICE=hw:1,0    # Your microphone card:device
ALSA_OUTPUT_DEVICE=hw:2,0   # Your soundbar card:device

# Verify other settings match your hardware
```

### 3.2 Update ALSA Configuration

```bash
# Edit ALSA config with your audio device numbers
sudo nano /etc/asound.conf

# Update card numbers based on your devices:
# - hw:1,0 for microphone
# - hw:2,0 for soundbar
```

---

## Phase 4: Model Preparation

### 4.1 Download Whisper Models

```bash
# Whisper models are automatically downloaded by Docker build
# Or manually download:
mkdir -p asr-service/models/whisper
cd asr-service/models/whisper

wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

cd /opt/blackbox
```

### 4.2 Build TensorRT-LLM Engine

**⚠️ CRITICAL: This step requires TensorRT-LLM installation**

Option A: Use Pre-built Engine (if available)
```bash
# Copy pre-built engine to models directory
cp /path/to/engine/* llm-service/models/engines/
```

Option B: Build Engine (recommended)
```bash
# This requires TensorRT-LLM to be installed on Jetson
# Follow the build script instructions:
cd llm-service
./build-trtllm.sh

# This will take 20-40 minutes
# Result: Engine in llm-service/models/engines/
```

**Note:** TensorRT-LLM engine building is the most complex step.
See `llm-service/build-trtllm.sh` for detailed instructions.

### 4.3 Download Piper Voice Model

```bash
# Piper models are automatically downloaded by Docker build
# Or manually:
mkdir -p tts-service/models/piper
cd tts-service/models/piper

wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

cd /opt/blackbox
```

---

## Phase 5: Build and Deploy

### 5.1 Build Docker Images

```bash
cd /opt/blackbox

# Build all services
docker-compose build

# This will take 30-60 minutes on first build
# Be patient - this builds:
# - TensorRT-LLM service
# - Whisper.cpp with CUDA
# - Piper TTS
# - FastAPI orchestrator
# - Chromium UI
```

### 5.2 Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Expected output: All services should show "healthy"
```

### 5.3 Verify Services

```bash
# Check orchestrator health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Check UI
# Open browser to: http://localhost:3000
```

---

## Phase 6: Enable Auto-Start

### 6.1 Install Systemd Service

```bash
# Copy service file
sudo cp system/blackbox.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable blackbox

# Start service
sudo systemctl start blackbox

# Check status
sudo systemctl status blackbox
```

### 6.2 Test Auto-Start

```bash
# Reboot to test
sudo reboot

# After reboot, verify services started
docker-compose ps
```

---

## Phase 7: Final Testing

### 7.1 Test Voice Pipeline

```bash
# Test transcription only
# Record a test audio file and upload via UI

# Or use curl:
curl -X POST http://localhost:8000/voice/transcribe \
  -F "audio=@test.wav"
```

### 7.2 Test Complete Pipeline

1. Open UI in browser: `http://localhost:3000`
2. Click "PRESS TO SPEAK" button
3. Say: "What time is it?"
4. Verify transcription appears
5. Verify response is generated
6. Verify audio plays back

### 7.3 Performance Validation

```bash
# Check metrics
curl http://localhost:8000/metrics

# Verify performance targets:
# - ASR: ≤2.5 seconds
# - LLM: ≥25 tokens/second
# - TTS: ≤1.5 seconds
# - Total: ≤13 seconds
```

### 7.4 Thermal Validation

```bash
# Run continuous load test (10 requests)
for i in {1..10}; do
  curl -X POST http://localhost:8000/text/interact \
    -H "Content-Type: application/json" \
    -d '{"text": "Tell me a story"}'
  sleep 5
done

# Monitor thermal status
watch -n 2 'curl -s http://localhost:8000/thermal/status'

# Temperature should stay below 85°C
```

---

## Phase 8: Offline Mode

### 8.1 Disconnect Network

```bash
# Disable WiFi adapter
sudo systemctl stop NetworkManager

# Or physically disconnect WiFi adapter

# System should continue functioning offline
```

### 8.2 Verify Offline Operation

- All voice interactions should work
- No external network calls
- All processing local

---

## Troubleshooting

### Common Issues

#### 1. Audio Devices Not Detected
```bash
# Check USB devices
lsusb

# Check ALSA devices
aplay -l
arecord -l

# Restart ALSA
sudo alsa force-reload
```

#### 2. Docker Services Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Check GPU access
docker run --rm --runtime=nvidia nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Rebuild service
docker-compose build --no-cache <service-name>
```

#### 3. Thermal Throttling
```bash
# Check temperatures
cat /sys/class/thermal/thermal_zone*/temp

# Check fan status
cat /sys/devices/pwm-fan/target_pwm

# Set fan to maximum
echo 255 | sudo tee /sys/devices/pwm-fan/target_pwm
```

#### 4. LLM Too Slow
```bash
# Verify INT4 quantization was used
# Verify 15W power mode:
sudo nvpmodel -q

# Check GPU utilization:
nvidia-smi
```

#### 5. Out of Memory Errors
```bash
# Check memory usage
free -h

# Check SWAP
swapon --show

# Restart services
docker-compose restart
```

---

## Maintenance

### Regular Tasks

#### Daily
- Check system logs: `docker-compose logs`
- Verify thermal status: `curl http://localhost:8000/thermal/status`

#### Weekly
- Database backup: Automatic (configured in .env)
- Check disk space: `df -h`

#### Monthly
- Update models (if needed)
- Review and clean logs
- Test backup restoration

### Updates

```bash
# Pull latest code
cd /opt/blackbox
git pull

# Rebuild services
docker-compose build

# Restart with new version
docker-compose down
docker-compose up -d
```

---

## Performance Optimization

### If Performance Below Target

1. **Verify Power Mode**: `sudo nvpmodel -m 0`
2. **Check Thermal**: May be throttling
3. **Verify Models**: Ensure INT4 quantization
4. **Check GPU Utilization**: `nvidia-smi`
5. **Review Logs**: Look for bottlenecks

---

## Support

For issues, see:
- `docs/TROUBLESHOOTING.md`
- `docs/PERFORMANCE.md`
- System logs: `/opt/blackbox/logs/`

---

**Deployment Complete! 🎉**

Your BLACK BOX offline voice assistant is now running and ready to serve senior users with fast, private, and resilient voice interactions.

