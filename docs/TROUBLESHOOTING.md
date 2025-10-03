# BLACK BOX - Troubleshooting Guide

Common issues and their solutions.

---

## Quick Diagnosis

```bash
# Run diagnostic script
cd /opt/blackbox
./system/diagnose.sh

# Check all services
docker-compose ps

# Check orchestrator health
curl http://localhost:8000/health

# Check logs
docker-compose logs --tail=100
```

---

## Services Won't Start

### Symptom: Docker Compose Fails
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Try starting services again
docker-compose up -d
```

### Symptom: GPU Not Accessible
```bash
# Test GPU access
docker run --rm --runtime=nvidia nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If this fails:
sudo systemctl restart docker

# Verify NVIDIA runtime configuration
cat /etc/docker/daemon.json
```

### Symptom: Services Exit Immediately
```bash
# Check specific service logs
docker-compose logs <service-name>

# Common issues:
# - Missing models
# - Permission errors
# - Port conflicts
```

---

## Audio Issues

### Microphone Not Working
```bash
# List audio input devices
arecord -l

# Test microphone recording
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 test.wav
# Speak for 5 seconds, then Ctrl+C

# Play back to verify
aplay test.wav

# If device not found:
# - Check USB connections
# - Check USB hub power
# - Try different USB port
# - Check dmesg for USB errors: dmesg | grep -i usb
```

### Soundbar Not Playing
```bash
# List audio output devices
aplay -l

# Test soundbar
speaker-test -D hw:2,0 -c 2

# If no sound:
# - Check USB connections
# - Check volume: alsamixer
# - Check mute status: amixer
# - Verify ALSA config: cat /etc/asound.conf
```

### Audio Device Numbers Changed
```bash
# Devices may change order after reboot
# Check current device numbers
aplay -l
arecord -l

# Update .env file
nano /opt/blackbox/.env
# Update ALSA_INPUT_DEVICE and ALSA_OUTPUT_DEVICE

# Restart services
docker-compose restart
```

---

## Performance Issues

### Slow Transcription (ASR > 2.5s)
```bash
# Check if Whisper is using GPU
docker-compose logs asr-service | grep -i cuda

# Verify tiny.en model is being used
docker-compose logs asr-service | grep -i model

# Try base.en if tiny.en gives poor accuracy but is fast enough
# Edit .env:
ASR_MODEL=base.en
docker-compose restart asr-service
```

### Slow LLM Inference (< 25 tok/s)
```bash
# Most common issue: Not using TensorRT-LLM with INT4

# Verify engine was built correctly
ls -lh llm-service/models/engines/

# Check GPU utilization during inference
watch -n 1 nvidia-smi

# If GPU usage is low:
# - Engine may not be optimized
# - Rebuild with INT4 quantization
# - Check power mode: sudo nvpmodel -q

# Check LLM logs
docker-compose logs llm-service
```

### Slow TTS (> 1.5s)
```bash
# Check if model is preloaded (warm startup)
docker-compose logs tts-service | grep -i preload

# Verify service started with --preload flag
docker-compose ps tts-service

# If not, edit docker-compose.yml and restart
```

### Total Pipeline > 13s
```bash
# Get detailed timing breakdown
curl http://localhost:8000/metrics

# Identify bottleneck:
# - ASR > 2.5s: See "Slow Transcription" above
# - LLM > 7.5s: See "Slow LLM Inference" above
# - TTS > 1.5s: See "Slow TTS" above
# - Orchestration > 0.5s: IPC issue

# For IPC issues:
# - Check shared memory: df -h /dev/shm
# - Verify IPC method: echo $IPC_METHOD
```

---

## Thermal Issues

### Temperature Too High
```bash
# Check current temperature
cat /sys/class/thermal/thermal_zone*/temp

# Check thermal status via API
curl http://localhost:8000/thermal/status

# If > 75°C:
# 1. Check fan operation
cat /sys/devices/pwm-fan/target_pwm
# Should be 255 (maximum)

# 2. Set fan to maximum
echo 255 | sudo tee /sys/devices/pwm-fan/target_pwm

# 3. Check USB fans are running
# - They should be spinning continuously
# - Check USB hub power

# 4. Verify power mode
sudo nvpmodel -q
# Should be mode 0 (15W)

# 5. Check heatsink contact
# - Power off and check thermal paste
# - Ensure heatsink is properly mounted
```

### System Throttling
```bash
# Check for throttling
# If temperature > 85°C, system may throttle

# Symptoms:
# - Performance degrades over time
# - GPU clock speed reduces

# Solutions:
# 1. Improve cooling (add more fans)
# 2. Reduce ambient temperature
# 3. Add heatsinks to VRM
# 4. Consider active cooling case
```

---

## Memory Issues

### Out of Memory Errors
```bash
# Check memory usage
free -h

# Check SWAP usage
swapon --show

# Check Docker memory
docker stats

# If RAM is full:
# 1. Verify GUI is disabled
systemctl get-default
# Should be multi-user.target

# 2. Verify SWAP is active
swapon --show
# Should show 16GB

# 3. Restart services to clear memory
docker-compose restart

# 4. If persistent, check for memory leaks
docker-compose logs | grep -i "memory"
```

### SWAP Not Working
```bash
# Check SWAP status
swapon --show
free -h

# If SWAP not active:
sudo swapon /swapfile

# Verify SWAP in fstab
grep swap /etc/fstab

# If not present, add:
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
```

---

## Database Issues

### Database Locked
```bash
# Stop all services
docker-compose down

# Check for stale locks
ls -la /opt/blackbox/data/

# Remove lock files if present
rm /opt/blackbox/data/*.lock

# Restart services
docker-compose up -d
```

### Encryption Key Error
```bash
# Error: "Invalid encryption key"
# Cause: DATABASE_ENCRYPTION_KEY changed or missing

# If lost, database cannot be decrypted
# Must regenerate and lose data:

# 1. Backup old database
cp /opt/blackbox/data/blackbox.db /opt/blackbox/data/blackbox.db.old

# 2. Generate new key
NEW_KEY=$(openssl rand -hex 32)

# 3. Update .env
nano /opt/blackbox/.env
# Set DATABASE_ENCRYPTION_KEY=$NEW_KEY

# 4. Restart (will create new empty database)
docker-compose restart
```

---

## UI Issues

### UI Not Loading
```bash
# Check UI service
docker-compose logs ui

# Check if port 3000 is accessible
curl http://localhost:3000

# Check if Chromium is running
docker-compose exec ui ps aux | grep chromium

# If not running, check X11 display
docker-compose exec ui echo $DISPLAY
```

### Voice Button Not Working
```bash
# Check browser console (F12)
# Look for JavaScript errors

# Common issues:
# - Microphone permissions not granted
# - HTTPS required (use localhost)
# - Browser not compatible (use Chromium)

# Check orchestrator is reachable
curl http://localhost:8000/health
```

---

## Network Issues (For Updates Only)

### Can't Connect to Internet
```bash
# Check WiFi adapter
lsusb | grep -i wireless

# Check network status
ip link show

# Restart NetworkManager
sudo systemctl restart NetworkManager

# Manually configure WiFi
nmcli device wifi list
nmcli device wifi connect "SSID" password "password"
```

### Docker Can't Pull Images
```bash
# Check internet connectivity
ping -c 3 google.com

# Check Docker daemon
sudo systemctl status docker

# Try with explicit DNS
# Edit /etc/docker/daemon.json:
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

sudo systemctl restart docker
```

---

## Systemd Service Issues

### Service Won't Start on Boot
```bash
# Check service status
sudo systemctl status blackbox

# Check service logs
sudo journalctl -u blackbox -n 50

# Verify service is enabled
sudo systemctl is-enabled blackbox

# If not enabled:
sudo systemctl enable blackbox

# Check dependencies
sudo systemctl list-dependencies blackbox
```

### Service Crashes
```bash
# Check logs
sudo journalctl -u blackbox -n 100 --no-pager

# Common causes:
# - Docker not started
# - Permissions issues
# - Missing .env file

# Restart service
sudo systemctl restart blackbox
```

---

## Recovery Procedures

### Complete System Reset
```bash
# 1. Stop all services
docker-compose down

# 2. Remove containers and volumes
docker-compose down -v

# 3. Remove Docker images (optional)
docker system prune -a

# 4. Rebuild and restart
docker-compose build
docker-compose up -d
```

### Restore from Backup
```bash
# Assuming backup at /opt/blackbox/backups/

# 1. Stop services
docker-compose down

# 2. Restore database
cp /opt/blackbox/backups/blackbox_YYYYMMDD.db /opt/blackbox/data/blackbox.db

# 3. Restart services
docker-compose up -d
```

### Factory Reset Jetson (Last Resort)
```bash
# This will erase everything!
# Only if system is completely broken

# 1. Flash Jetson with JetPack
# - Use NVIDIA SDK Manager from another PC
# - Follow NVIDIA's flashing guide

# 2. After flash, redeploy BLACK BOX
# - Follow DEPLOYMENT.md from start
```

---

## Getting Help

### Collect Diagnostic Information
```bash
# Run diagnostics
cd /opt/blackbox
./system/diagnose.sh > diagnostics.txt

# Collect logs
docker-compose logs > docker-logs.txt

# System information
uname -a > system-info.txt
nvidia-smi > gpu-info.txt
free -h >> system-info.txt
df -h >> system-info.txt
```

### Log Files Locations
- Docker logs: `docker-compose logs`
- System logs: `/opt/blackbox/logs/`
- Systemd logs: `sudo journalctl -u blackbox`
- Kernel logs: `dmesg`

---

## Preventive Maintenance

### Regular Checks
```bash
# Weekly health check
curl http://localhost:8000/health

# Monthly cleanup
docker system prune

# Check disk space
df -h

# Check temperatures
cat /sys/class/thermal/thermal_zone*/temp
```

---

**Still Having Issues?**

1. Check README.md for system requirements
2. Review DEPLOYMENT.md for setup steps
3. Check PERFORMANCE.md for optimization tips
4. Collect diagnostics and review logs

