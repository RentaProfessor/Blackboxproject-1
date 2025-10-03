# BLACK BOX - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2025-10-03

### Added
- Initial release of BLACK BOX offline voice assistant
- TensorRT-LLM integration for optimized LLM inference (Llama 3.2 3B / Phi 3.5 3B)
- Whisper.cpp ASR service with GPU acceleration
- Piper TTS service with warm startup
- FastAPI orchestrator with thermal monitoring
- SQLCipher encrypted database for secure local storage
- Chromium kiosk UI with senior-friendly design
- Docker Compose multi-service architecture
- Shared memory IPC for low-latency service communication
- Systemd service for auto-start and resilience
- Complete documentation suite (README, DEPLOYMENT, TROUBLESHOOTING, PERFORMANCE)

### System Optimizations
- GUI disabled to free ~1GB RAM
- 16GB SWAP file on NVMe SSD
- 15W power mode for optimal GPU performance
- ALSA audio configuration (PulseAudio disabled)
- Proactive thermal monitoring and management

### Performance Targets
- ASR (Whisper): ≤2.5 seconds
- LLM (TensorRT): ≤7.5 seconds @ ≥25 tokens/second
- TTS (Piper): ≤1.5 seconds
- Total pipeline: ≤13 seconds (typical: ~7.9s)

### Security Features
- AES-256 database encryption (SQLCipher)
- Argon2id password hashing for vault
- Fully offline operation (zero external dependencies)
- Isolated Docker containers

### Hardware Support
- NVIDIA Jetson Orin Nano (8GB) - primary target
- NVMe SSD for fast storage
- USB audio I/O (soundbar + microphone)
- USB cooling fans
- WiFi adapter (setup only)

### Documentation
- Comprehensive README with project overview
- Step-by-step deployment guide
- Performance tuning guide
- Troubleshooting guide
- Quick start guide

---

## [Unreleased]

### Planned Features
- Multi-user support with voice recognition
- Media playback integration
- Calendar integration for reminders
- Voice-activated vault access
- Custom wake word detection
- Expanded language support
- Mobile companion app
- Voice activity detection (VAD) for hands-free operation

### Planned Improvements
- Further LLM optimization (FP8 quantization if supported)
- Model fine-tuning for senior-specific use cases
- Enhanced thermal management with predictive throttling
- Database backup automation improvements
- Web-based administration interface
- Performance metrics dashboard

---

## Version History

- **1.0.0** (2025-10-03): Initial release

