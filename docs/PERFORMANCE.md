# BLACK BOX - Performance Tuning Guide

Optimizations and troubleshooting for meeting performance targets.

---

## Performance Targets

| Component      | Target      | Critical Path                          |
|----------------|-------------|----------------------------------------|
| ASR (Whisper)  | ≤2.5s       | Audio → Text transcription             |
| LLM (TRT-LLM)  | ≤7.5s       | Context → Response (≥25 tokens/second) |
| TTS (Piper)    | ≤1.5s       | Text → Audio synthesis                 |
| Orchestration  | ≤0.5s       | IPC + context management               |
| **TOTAL**      | **≤13s**    | End-to-end voice interaction           |

---

## ASR Performance Tuning

### Target: ≤2.5 seconds

#### Model Selection
```bash
# tiny.en: Fastest (recommended)
ASR_MODEL=tiny.en
# Expected: 0.5-1.5s on 5-10 second audio

# base.en: Better accuracy, slightly slower
ASR_MODEL=base.en
# Expected: 1.0-2.0s on 5-10 second audio
```

#### GPU Optimization
```bash
# Verify CUDA build
docker-compose exec asr-service python3 -c "import whisper; print(whisper.__version__)"

# Check GPU usage during transcription
watch -n 0.5 nvidia-smi

# Should see GPU utilization spike during processing
```

#### Audio Format
```bash
# Whisper prefers 16kHz mono
# Ensure microphone is configured correctly in ALSA:
pcm.microphone {
    type plug
    slave {
        pcm "hw:1,0"
        rate 16000    # Critical for performance
        channels 1
    }
}
```

#### Troubleshooting Slow ASR
- [ ] Verify GPU CUDA build: Check logs for "CUDA not available"
- [ ] Check model size: tiny.en should be ~75MB
- [ ] Verify audio duration: Very long audio takes longer
- [ ] Check GPU memory: `nvidia-smi` during inference
- [ ] Thermal throttling: Check temperature
- [ ] Power mode: Should be 15W

---

## LLM Performance Tuning

### Target: ≥25 tokens/second (≤7.5s for 150 tokens)

#### Critical: INT4 Quantization
```bash
# MUST use INT4 quantized TensorRT-LLM engine
# Check engine build:
ls -lh llm-service/models/engines/

# Engine should be significantly smaller than FP16:
# - FP16: ~6GB
# - INT4: ~1.5GB

# Verify quantization in build script
cat llm-service/build-trtllm.sh | grep -i int4
```

#### Model Selection
```bash
# Llama 3.2 3B (recommended)
LLM_MODEL=llama-3.2-3b
# Expected: 25-35 tokens/second with INT4

# Phi 3.5 3B (alternative)
LLM_MODEL=phi-3.5-3b
# Expected: 25-30 tokens/second with INT4

# Never use 7B models - too slow for target
```

#### GPU Memory Allocation
```bash
# Allocate sufficient GPU memory
LLM_GPU_MEMORY=4096  # 4GB for 3B INT4 model

# Check actual GPU usage
nvidia-smi
# Should see ~4GB allocated during inference
```

#### Context Management
```bash
# Limit context window to prevent slowdown
CONTEXT_MAX_MESSAGES=10     # Last 10 messages
CONTEXT_MAX_TOKENS=2048     # Max 2K tokens

# Shorter context = faster inference
```

#### Token Limit
```bash
# Limit max generation length
LLM_MAX_TOKENS=150  # Target 150 tokens

# Shorter responses = faster completion
# 150 tokens @ 25 tok/s = 6 seconds
```

#### Troubleshooting Slow LLM
- [ ] **Verify INT4 quantization**: Most common issue!
- [ ] Check power mode: `sudo nvpmodel -q` (should be mode 0)
- [ ] GPU clock speed: `nvidia-smi` (should not be throttled)
- [ ] Thermal state: Temperature < 85°C
- [ ] Engine optimization: Check build logs
- [ ] Batch size: Should be 1 for single user
- [ ] KV cache: Should be enabled in TRT-LLM build

---

## TTS Performance Tuning

### Target: ≤1.5 seconds

#### Warm Startup (Critical)
```bash
# MUST use --preload flag to keep model in memory
# Check docker-compose.yml:
command: ["python", "/app/server.py", "--preload"]

# Verify in logs:
docker-compose logs tts-service | grep -i preload
# Should see: "Preloading model (warm startup)..."
```

#### Model Selection
```bash
# en_US-lessac-medium: Good balance (recommended)
TTS_VOICE=en_US-lessac-medium
# Expected: 0.5-1.2s for typical responses

# Faster alternatives (lower quality):
TTS_VOICE=en_US-lessac-low
# Expected: 0.3-0.8s
```

#### Streaming Mode
```bash
# Enable streaming for lower perceived latency
TTS_STREAM_ENABLED=true
TTS_STREAM_CHUNK_SIZE=1024

# Audio starts playing before complete synthesis
```

#### Troubleshooting Slow TTS
- [ ] Verify warm startup: Check logs for preload
- [ ] Model loaded: Should see "model loaded" in logs
- [ ] Very long text: Split into sentences
- [ ] CPU usage: Piper is CPU-bound, check `htop`
- [ ] Cold start: First request may be slow

---

## Orchestration Performance

### Target: ≤0.5 seconds overhead

#### IPC Method
```bash
# Use shared memory (fastest)
IPC_METHOD=shared_memory

# Avoid TCP networking between containers
# Check docker-compose.yml:
ipc: shareable  # Should be set for all services
```

#### Shared Memory Optimization
```bash
# Ensure sufficient shared memory
# In docker-compose.yml:
volumes:
  - type: tmpfs
    target: /dev/shm
    tmpfs:
      size: 512m  # Sufficient for most requests

# Check usage:
df -h /dev/shm
```

#### Context Retrieval
```bash
# Database queries should be fast
# Enable WAL mode (already in db.py):
PRAGMA journal_mode=WAL

# Monitor query times:
docker-compose logs orchestrator | grep "context"
```

#### Troubleshooting Slow Orchestration
- [ ] IPC method: Should be shared_memory
- [ ] Shared memory full: `df -h /dev/shm`
- [ ] Database locked: Check for concurrent access
- [ ] Network latency: Services should use IPC, not HTTP
- [ ] Async issues: Check FastAPI logs

---

## System-Wide Optimizations

### Power Mode (Critical)
```bash
# MUST be in 15W mode for target GPU clocks
sudo nvpmodel -m 0

# Verify:
sudo nvpmodel -q
# Output should show: "NV Power Mode: MODE_15W"

# Check GPU clocks:
nvidia-smi --query-gpu=clocks.gr,clocks.mem --format=csv
```

### Memory Configuration
```bash
# GUI disabled (saves ~1GB)
systemctl get-default
# Should output: multi-user.target

# 16GB SWAP active
free -h
# Should show ~16GB swap

# If not enough RAM:
docker system prune  # Clean up unused images
```

### Thermal Management
```bash
# Temperature affects performance significantly
# Target: Stay below 75°C (warning), definitely below 85°C (critical)

# Check current temperature:
cat /sys/class/thermal/thermal_zone*/temp

# Ensure fan at maximum:
echo 255 | sudo tee /sys/devices/pwm-fan/target_pwm

# Monitor during load:
watch -n 1 'cat /sys/class/thermal/thermal_zone*/temp'
```

### Cooling Enhancements
If thermal throttling occurs:
1. **Verify all fans running**: Onboard + 2x USB fans
2. **Check heatsink contact**: May need new thermal paste
3. **Improve airflow**: Remove obstructions
4. **Ambient temperature**: Keep room cool
5. **Consider upgrades**: Active cooling case, larger heatsink

---

## Performance Monitoring

### Real-Time Monitoring
```bash
# Watch system metrics
watch -n 2 'curl -s http://localhost:8000/metrics'

# Monitor GPU
watch -n 1 nvidia-smi

# Monitor CPU/Memory
htop

# Monitor temperatures
watch -n 2 'cat /sys/class/thermal/thermal_zone*/temp'
```

### Logging Performance Metrics
```bash
# Enable detailed timing logs
TIMING_LOGS=true

# Check logs
docker-compose logs orchestrator | grep -i timing
```

### Benchmark Script
```bash
# Create benchmark test
cat > benchmark.sh <<'EOF'
#!/bin/bash
echo "BLACK BOX Performance Benchmark"
echo "================================"

for i in {1..5}; do
  echo "Test $i/5:"
  START=$(date +%s.%N)
  
  curl -s -X POST http://localhost:8000/text/interact \
    -H "Content-Type: application/json" \
    -d '{"text": "What time is it?"}' | jq -r '.timing.total'
  
  END=$(date +%s.%N)
  TOTAL=$(echo "$END - $START" | bc)
  echo "Total: ${TOTAL}s"
  echo
  
  sleep 2
done
EOF

chmod +x benchmark.sh
./benchmark.sh
```

---

## Performance Validation Checklist

### Pre-Flight Checks
- [ ] Power mode: 15W (`sudo nvpmodel -q`)
- [ ] GUI disabled (`systemctl get-default` = multi-user)
- [ ] 16GB SWAP active (`free -h`)
- [ ] All fans running (onboard + USB)
- [ ] Temperature < 75°C at idle
- [ ] Docker NVIDIA runtime configured

### ASR Checks
- [ ] Whisper.cpp built with CUDA (`docker-compose logs asr-service | grep CUDA`)
- [ ] Using tiny.en or base.en model
- [ ] GPU utilized during transcription
- [ ] Audio format: 16kHz mono

### LLM Checks
- [ ] TensorRT-LLM engine built with INT4 quantization ⚠️ CRITICAL
- [ ] Using 3B model (not 7B)
- [ ] GPU memory allocated (~4GB)
- [ ] Tokens/second ≥ 25
- [ ] Context limited (≤10 messages)

### TTS Checks
- [ ] Model preloaded (warm startup)
- [ ] Streaming enabled
- [ ] Using medium quality voice

### Orchestration Checks
- [ ] IPC method: shared_memory
- [ ] Shared memory available (`df -h /dev/shm`)
- [ ] FastAPI async workers configured

---

## Expected Performance by Component

### Typical Timings (on properly configured Jetson Orin Nano 15W)

```
Audio Input (5 seconds of speech):
├─ ASR (Whisper tiny.en):        1.2s  ✓
├─ Context Retrieval:             0.05s ✓
├─ LLM (Llama 3.2 3B INT4):       5.5s  ✓ (150 tokens @ 27 tok/s)
├─ Context Update:                0.03s ✓
├─ TTS (Piper):                   0.9s  ✓
└─ Orchestration Overhead:        0.22s ✓
                                  ────
Total:                            7.9s  ✓ (target: ≤13s)
```

### Performance Degradation Indicators
- ASR > 2.5s: GPU not being used or thermal throttling
- LLM < 25 tok/s: Not using INT4 or thermal throttling
- TTS > 1.5s: Model not preloaded (cold start)
- Orchestration > 0.5s: IPC issues or database locks

---

## Performance Optimization Priority

If not meeting targets, optimize in this order:

1. **LLM INT4 Quantization** ⚠️ HIGHEST PRIORITY
   - This is the most critical optimization
   - Without INT4, target is impossible to meet
   
2. **Power Mode (15W)**
   - Required for proper GPU clocks
   
3. **TTS Warm Startup**
   - Eliminates cold start penalty
   
4. **Whisper CUDA Build**
   - GPU acceleration essential
   
5. **Thermal Management**
   - Prevents throttling
   
6. **Memory Optimization**
   - Prevents swapping during inference

---

## Advanced Tuning

### If Still Below Target After Above

#### GPU Overclocking (Use Caution)
```bash
# Increase GPU clock (requires testing for stability)
# Only if thermal headroom available

# Not recommended unless absolutely necessary
# May reduce hardware lifespan
```

#### Model Optimization
```bash
# Further optimize TRT-LLM engine:
# - Increase batch size (if memory available)
# - Enable FP8 (if supported)
# - Tune KV cache size
# - Profile with nsys
```

#### Code Optimization
```bash
# Profile Python code
python -m cProfile orchestrator/main.py

# Identify bottlenecks in orchestration
# Optimize hot paths
```

---

**Remember**: The specified hardware and software stack is designed to meet the 13-second target. If properly configured with INT4 quantization and all optimizations applied, the target should be achievable with margin.

