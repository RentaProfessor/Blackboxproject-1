# BLACK BOX Project - Offline Voice Assistant for Seniors

## ⚠️ CRITICAL: Reference Document - DO NOT DEVIATE

This README serves as the **authoritative reference** for all implementation decisions. Every component, configuration, and optimization detailed here is **mandatory** and has been carefully specified to meet strict performance and resilience requirements.

---

## Project Overview

**Mission**: Build a fully offline, highly resilient, voice-activated assistant for senior users, combining ASR, LLM, TTS, media playback, and secure memory, running exclusively on the NVIDIA Jetson Orin Nano (8GB) developer kit.

**Performance Budget (Total: ≤13 seconds)**:
- ASR (Speech Recognition): ≤2.5 seconds
- LLM (AI Response): ≤7.5 seconds (≥25 tokens/second)
- TTS (Voice Synthesis): ≤1.5 seconds
- Orchestration Overhead: ≤0.5 seconds

---

## I. Hardware and Physical Environment Specifications

### Core Compute Unit
- **Device**: NVIDIA Jetson Orin Nano Developer Kit (8GB)
- **Power Mode**: 15W sustained (mandatory for required GPU clock speeds)
- **Storage**: SK Hynix Gold P31 NVMe SSD (500GB)
  - OS installation
  - AI model storage
  - Encrypted database

### Peripheral Hardware
- **USB Hub**: Externally Powered USB 3.0 Hub (confirmed model)
  - **Purpose**: Stabilize power delivery during peak GPU load
  - **Connected Devices**:
    - Lielongren USB Mini Soundbar (audio output)
    - MilISO/JOUNIVO USB Gooseneck Microphones (audio input)
    - Wathai USB fans (2x 40x10mm - thermal management)

### Cooling System
- **Primary**: Jetson Orin Nano onboard fan
- **Secondary**: 2x Wathai USB fans (40x10mm) running continuously
- **Rationale**: Sustained thermal management for 15W power mode

### Network Adapter
- **Device**: BrosTrend AC1200 WiFi USB Adapter
- **Purpose**: Software updates ONLY
- **Operating Mode**: Offline-first (disconnect after updates)
- **Setup**: Must install all required Linux dependencies during provisioning

---

## II. Mandatory Optimized AI Software Stack (The Core Pivot)

### ⚠️ STRICT REQUIREMENT: No Generic Runtimes
**FORBIDDEN**: Ollama, generic llama.cpp, any 7B models  
**REQUIRED**: TensorRT-LLM optimization pipeline

### Containerization Framework
- **Base**: Docker + NVIDIA L4T JetPack Containers
- **GPU Access**: CUDA passthrough enabled for all AI services
- **IPC**: Shared memory volumes / UNIX sockets (not TCP networking)

### 1. LLM Runtime: TensorRT-LLM (TRT-LLM)
- **Engine**: TensorRT-LLM (optimized inference)
- **Purpose**: Maximize tokens-per-second throughput
- **Target Performance**: ≥25 tokens/second sustained

### 2. LLM Model: Llama 3.2 3B or Phi 3.5 3B
- **Architecture**: 3B parameter models ONLY
- **Quantization**: INT4 via TRT-LLM compilation
- **Performance Target**: ≥25 tokens/second (non-negotiable)
- **Budget Allocation**: ≤7.5 seconds for response generation

### 3. LLM Function Calling
- **Fine-tuning**: LoRA techniques for function calling capabilities
- **Output Format**: Strict JSON/Pydantic schemas
- **Commands**: set_reminder, access_vault, play_media, etc.
- **Validation**: Orchestrator enforces schema compliance

### 4. ASR Component: Whisper.cpp
- **Runtime**: GPU-optimized Whisper.cpp build
- **Model**: `tiny.en` or `base.en` (efficiency-optimized)
- **Performance Target**: ≤2.5 seconds transcription
- **Integration**: CUDA-accelerated build required

### 5. TTS Component: Piper TTS
- **Runtime**: Piper TTS with persistent warm container
- **Optimization**: Eliminate cold-start latency
- **Streaming**: Implement streamed audio playback
- **Performance Target**: ≤1.5 seconds to first audio

### 6. Orchestrator: FastAPI
- **Framework**: FastAPI (async Python)
- **Pipeline Flow**: ASR → LLM → TTS
- **State Management**: User context and conversation history
- **Thermal Monitoring**: Proactive monitoring for 15W power mode
- **IPC**: High-speed inter-container communication

---

## III. Mandatory System and Resilience Configuration

### 1. Memory Reclamation
```bash
# Disable GUI permanently to free ~1GB RAM
sudo systemctl set-default multi-user.target
```
- **Rationale**: GUI consumes critical RAM needed for AI inference
- **Impact**: Frees approximately 1GB of contested memory

### 2. SWAP Configuration
- **Size**: 16GB SWAP file on NVMe SSD
- **Location**: `/swapfile` on NVMe
- **Steps**:
  1. Disable default ZRAM configuration
  2. Create 16GB SWAP file on NVMe
  3. Add persistent entry to `/etc/fstab`
- **Rationale**: Prevent OOM crashes during peak inference

### 3. Service Persistence
- **Definition**: Single `docker-compose.yml` file
- **Services**: 5 core containers
  1. FastAPI Orchestrator
  2. TensorRT-LLM Inference
  3. Whisper.cpp ASR
  4. Piper TTS
  5. Chromium Kiosk UI
- **Configuration**: `restart: always` for all services
- **Auto-start**: Systemd service unit for boot-time initialization
- **Rationale**: Autonomous recovery and system resilience

### 4. Inter-Process Communication (IPC)
- **Method**: Shared Memory volumes or UNIX sockets
- **Forbidden**: TCP networking between containers (too slow)
- **Performance Target**: ≤0.5 seconds orchestration overhead
- **Implementation**: Docker volume mounts with tmpfs

### 5. Audio Optimization
- **Audio Server**: ALSA (direct)
- **Forbidden**: PulseAudio (higher latency)
- **Rationale**: Lower latency for USB audio I/O paths
- **Configuration**: Direct ALSA device mapping to containers

---

## IV. Security and User Experience Requirements

### Database Security
- **Engine**: SQLite with SQLCipher extension
- **Encryption**: AES-256 for all local data
- **Protected Data**:
  - Reminders
  - Media metadata
  - Vault contents
- **Password Hashing**: Argon2id for Vault passwords

### User Interface
- **Delivery**: Chromium in kiosk mode (fullscreen)
- **Design Principles** (Senior-Friendly):
  - **Large Buttons**: Minimum 80px height
  - **High Contrast**: WCAG AAA compliance
  - **Non-Color Dependent**: Text labels accompany all visual cues
  - **Confirmation Scheme**: Green/Red with "SAVE"/"RETRY" text labels
  - **Font Size**: Minimum 18px body, 24px+ for headings

---

## V. Performance and Resilience Guarantees

### Latency Budget Breakdown
| Component      | Budget   | Optimization Strategy                    |
|----------------|----------|------------------------------------------|
| ASR            | ≤2.5s    | Whisper tiny.en + GPU acceleration       |
| LLM            | ≤7.5s    | TRT-LLM INT4 @ ≥25 tok/s                 |
| TTS            | ≤1.5s    | Piper warm container + streaming         |
| Orchestration  | ≤0.5s    | Shared memory IPC, async pipeline        |
| **TOTAL**      | **≤13s** | End-to-end voice interaction             |

### Thermal Management
- **Target**: Sustained 15W power mode without throttling
- **Monitoring**: Proactive thermal checks in Orchestrator
- **Cooling**: Active fan cooling (onboard + 2x USB fans)
- **Mitigation**: Graceful degradation if thermal limits approached

### Autonomy and Resilience
- **Boot Recovery**: Systemd service ensures all containers restart
- **Crash Recovery**: `restart: always` policy on all Docker services
- **Data Durability**: SQLCipher database with write-ahead logging (WAL)
- **Offline Operation**: Zero external dependencies after provisioning

---

## VI. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NVIDIA Jetson Orin Nano                  │
│                    Ubuntu 22.04 + JetPack                   │
│                    (GUI Disabled, 16GB SWAP)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            Docker Compose Service Stack             │  │
│  │                                                     │  │
│  │  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │  Whisper.cpp │→ │   FastAPI    │               │  │
│  │  │  ASR Service │  │ Orchestrator │               │  │
│  │  └──────────────┘  └───────┬──────┘               │  │
│  │         ↑                   ↓                      │  │
│  │         │          ┌──────────────┐               │  │
│  │    [Audio In]      │  TensorRT    │               │  │
│  │                    │  LLM Service │               │  │
│  │                    └───────┬──────┘               │  │
│  │                            ↓                      │  │
│  │                   ┌──────────────┐               │  │
│  │                   │  Piper TTS   │               │  │
│  │                   │   Service    │               │  │
│  │                   └───────┬──────┘               │  │
│  │                           ↓                      │  │
│  │                     [Audio Out]                  │  │
│  │                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │  Chromium    │  │  SQLCipher   │            │  │
│  │  │  Kiosk UI    │  │   Database   │            │  │
│  │  └──────────────┘  └──────────────┘            │  │
│  │                                                 │  │
│  │  IPC: Shared Memory / UNIX Sockets             │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  Audio I/O: ALSA → USB Hub → Soundbar/Microphone     │
└────────────────────────────────────────────────────────┘
```

---

## VII. Critical Implementation Notes

### ⚠️ Non-Negotiable Requirements
1. **TensorRT-LLM**: Must use TRT-LLM, not generic llama.cpp or Ollama
2. **3B Models**: Must use Llama 3.2 3B or Phi 3.5 3B (no 7B models)
3. **INT4 Quantization**: Required for ≥25 tok/s performance
4. **Shared Memory IPC**: No TCP networking between containers
5. **15W Power Mode**: Mandatory for GPU clock speeds
6. **GUI Disabled**: Required for memory reclamation
7. **16GB SWAP**: Required to prevent OOM crashes
8. **ALSA Audio**: PulseAudio forbidden for latency reasons

### Testing Validation Criteria
- [ ] ASR latency ≤2.5 seconds (measured with `tiny.en` model)
- [ ] LLM throughput ≥25 tokens/second (sustained)
- [ ] TTS latency ≤1.5 seconds (first audio output)
- [ ] Total pipeline ≤13 seconds (end-to-end)
- [ ] System survives 72-hour stress test without crash
- [ ] All services auto-restart after power cycle
- [ ] Temperature stays below throttling threshold

---

## VIII. Directory Structure

```
BLACK-BOX-PROJECT/
├── README.md                          # This file
├── docker-compose.yml                 # All services definition
├── .env.example                       # Environment variables template
├── system/
│   ├── setup-jetson.sh               # System configuration script
│   ├── blackbox.service              # Systemd service unit
│   └── alsa.conf                     # ALSA configuration
├── orchestrator/
│   ├── Dockerfile                    # FastAPI container
│   ├── requirements.txt              # Python dependencies
│   ├── main.py                       # FastAPI application
│   ├── pipeline.py                   # ASR→LLM→TTS pipeline
│   ├── thermal.py                    # Thermal monitoring
│   └── ipc.py                        # Inter-process communication
├── llm-service/
│   ├── Dockerfile                    # TensorRT-LLM container
│   ├── build-trtllm.sh              # TRT-LLM engine builder
│   ├── inference.py                  # Inference server
│   └── models/                       # Model storage
├── asr-service/
│   ├── Dockerfile                    # Whisper.cpp container
│   ├── build-whisper.sh             # GPU-optimized build
│   └── transcribe.py                 # ASR server
├── tts-service/
│   ├── Dockerfile                    # Piper TTS container
│   ├── server.py                     # TTS server (warm start)
│   └── models/                       # Piper voice models
├── database/
│   ├── schema.sql                    # Database schema
│   ├── db.py                         # SQLCipher wrapper
│   └── migrations/                   # Schema migrations
├── ui/
│   ├── Dockerfile                    # Chromium kiosk container
│   ├── index.html                    # Main UI
│   ├── styles.css                    # Senior-friendly styles
│   ├── app.js                        # Frontend logic
│   └── assets/                       # Images, icons
└── docs/
    ├── DEPLOYMENT.md                 # Deployment instructions
    ├── TROUBLESHOOTING.md           # Common issues
    └── PERFORMANCE.md                # Performance tuning guide
```

---

## IX. Quick Start (After Hardware Setup)

**NEW: Single Command Deployment**

```bash
# 1. Clone repository
cd /opt
git clone <repository-url> blackbox
cd blackbox

# 2. Run master installation script (does everything)
sudo ./install.sh

# 3. Reboot and initialize
sudo reboot
# After reboot:
docker-compose exec orchestrator python3 /app/scripts/init_vault_setup.py --master-password 'YOUR_SECURE_PASSWORD'

# 4. Test system
curl http://localhost:8000/health
# Open browser: http://localhost:3000
```

**Alternative: Manual Setup**

```bash
# 1. Clone repository
cd /opt
git clone <repository-url> blackbox
cd blackbox

# 2. Run system configuration
sudo ./system/setup-jetson.sh

# 3. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 4. Build TensorRT-LLM engine (one-time, ~30 minutes)
cd llm-service
./build-trtllm.sh

# 5. Start all services
cd /opt/blackbox
docker-compose up -d

# 6. Verify services
docker-compose ps
docker-compose logs -f

# 7. Enable auto-start
sudo systemctl enable blackbox
sudo systemctl start blackbox
```

---

## X. Maintenance and Updates

### Software Updates (Online Mode)
1. Connect BrosTrend WiFi adapter
2. Run update script: `./system/update.sh`
3. Disconnect WiFi adapter
4. System returns to offline mode

### Model Updates
- Models stored in: `/opt/blackbox/models/`
- TRT-LLM engines: `/opt/blackbox/llm-service/models/engines/`
- Rebuild engines after model updates

### Database Backups
- Automatic: Daily backups to `/opt/blackbox/backups/`
- Manual: `docker-compose exec orchestrator python -m database.backup`

---

## XI. Support and Troubleshooting

See `docs/TROUBLESHOOTING.md` for:
- Audio device configuration
- GPU memory errors
- Container startup failures
- Performance optimization
- Thermal throttling mitigation

---

**Version**: 1.0.0  
**Last Updated**: October 3, 2025  
**Target Hardware**: NVIDIA Jetson Orin Nano (8GB)  
**Target OS**: Ubuntu 22.04 + JetPack SDK

---

## ⚠️ CRITICAL REMINDER

Every specification in this document exists for a reason:
- **Performance**: Meeting the 13-second latency budget
- **Stability**: Preventing crashes and thermal issues
- **Resilience**: Ensuring autonomous operation
- **User Experience**: Serving senior users effectively

**DO NOT DEVIATE** from these specifications without thorough testing and validation.

