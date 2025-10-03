# BLACK BOX - Quick Start Guide

Get up and running in under 2 hours (excluding model downloads/builds).

---

## Prerequisites Checklist

Hardware:
- [ ] NVIDIA Jetson Orin Nano (8GB) - powered on
- [ ] NVMe SSD installed
- [ ] USB hub (externally powered) connected
- [ ] USB microphone connected to hub
- [ ] USB soundbar connected to hub  
- [ ] USB fans (2x) connected to hub
- [ ] WiFi adapter connected (for setup only)
- [ ] Display, keyboard, mouse connected

Software:
- [ ] Ubuntu 22.04 + JetPack SDK installed
- [ ] Internet connection active

---

## Step 1: Clone Repository (5 min)

```bash
# Create directory
sudo mkdir -p /opt/blackbox
cd /opt/blackbox

# Clone repo
git clone <repository-url> .

# Or copy from USB
# cp -r /media/usb/blackbox/* .
```

---

## Step 2: System Configuration (15 min)

```bash
# Run setup script
chmod +x system/setup-jetson.sh
sudo ./system/setup-jetson.sh

# Follow prompts and REBOOT when complete
sudo reboot
```

After reboot, log in via SSH or console (GUI is now disabled).

---

## Step 3: Configure Environment (5 min)

```bash
cd /opt/blackbox

# Copy environment template
cp .env.example .env

# Generate encryption key
echo "DATABASE_ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env

# Check your audio device numbers
aplay -l   # Note soundbar card number
arecord -l # Note microphone card number

# Edit .env with your audio devices
nano .env
# Update ALSA_INPUT_DEVICE and ALSA_OUTPUT_DEVICE
```

---

## Step 4: Download Models (20 min)

### Whisper (automatic in Docker build)
```bash
# Will download automatically during build
# tiny.en: ~75MB
# base.en: ~142MB
```

### Piper (automatic in Docker build)
```bash
# Will download automatically during build
# en_US-lessac-medium: ~60MB
```

### TensorRT-LLM Engine (CRITICAL - Manual Step)

**Option A: Use Pre-built Engine (Recommended)**
```bash
# If you have a pre-built engine:
mkdir -p llm-service/models/engines/llama-3.2-3b-int4
cp /path/to/engine/* llm-service/models/engines/llama-3.2-3b-int4/
```

**Option B: Build Engine (30-40 minutes)**
```bash
# Download model weights first
# Follow instructions in llm-service/build-trtllm.sh
cd llm-service
./build-trtllm.sh
cd ..
```

---

## Step 5: Build Docker Images (30-60 min)

```bash
cd /opt/blackbox

# Build all services (this takes time on first build)
docker-compose build

# Get coffee while this runs...
```

---

## Step 6: Start Services (2 min)

```bash
# Start all services
docker-compose up -d

# Check status (all should be "healthy" after ~60 seconds)
docker-compose ps

# Watch logs
docker-compose logs -f
# Press Ctrl+C to exit log view
```

---

## Step 7: Test System (5 min)

### Test Health
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

### Test Text Query
```bash
curl -X POST http://localhost:8000/text/interact \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?"}'

# Should return transcription, response, and timing
```

### Test Voice (via UI)
1. Open browser: `http://localhost:3000`
2. Click "PRESS TO SPEAK"
3. Say: "What time is it?"
4. Should see transcription and hear response

---

## Step 8: Enable Auto-Start (2 min)

```bash
# Install systemd service
sudo cp system/blackbox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable blackbox
sudo systemctl start blackbox

# Verify
sudo systemctl status blackbox
```

---

## Step 9: Go Offline (1 min)

```bash
# System is now fully functional
# Disconnect WiFi adapter if desired

# Or disable network:
sudo systemctl stop NetworkManager

# System continues to work 100% offline
```

---

## Verification Checklist

- [ ] All Docker services running: `docker-compose ps`
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Text queries work: Test with curl command above
- [ ] Voice interaction works: Test via UI
- [ ] Audio output works: Hear TTS response
- [ ] Performance within target: Check metrics
- [ ] Temperature acceptable: `curl http://localhost:8000/thermal/status`
- [ ] Auto-start enabled: `systemctl status blackbox`
- [ ] Works offline: Disconnect network and test

---

## Quick Troubleshooting

### Services won't start
```bash
docker-compose logs <service-name>
sudo systemctl restart docker
docker-compose up -d
```

### Audio not working
```bash
# Check devices
aplay -l
arecord -l

# Update .env with correct device numbers
nano .env

# Restart services
docker-compose restart
```

### Slow performance
```bash
# Check power mode (should be 15W)
sudo nvpmodel -q

# Check temperature
cat /sys/class/thermal/thermal_zone*/temp

# Check metrics
curl http://localhost:8000/metrics
```

### LLM too slow
```bash
# Verify INT4 engine was built
ls -lh llm-service/models/engines/

# Check if using TensorRT-LLM
docker-compose logs llm-service | grep -i tensorrt
```

---

## Next Steps

- Review full documentation: `README.md`
- Detailed deployment: `docs/DEPLOYMENT.md`
- Performance tuning: `docs/PERFORMANCE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

---

## Performance Expectations

With proper configuration on Jetson Orin Nano 15W:

- **ASR**: ~1.2s (Whisper tiny.en)
- **LLM**: ~5.5s (Llama 3.2 3B INT4, 150 tokens @ 27 tok/s)
- **TTS**: ~0.9s (Piper medium)
- **Total**: ~7.9s (well under 13s target) ✓

---

## Need Help?

1. Check logs: `docker-compose logs`
2. Review troubleshooting: `docs/TROUBLESHOOTING.md`
3. Verify all prerequisites met
4. Check system requirements

---

**You're all set!** Your BLACK BOX offline voice assistant is ready to serve.

