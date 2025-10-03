# Contributing to BLACK BOX

Thank you for your interest in contributing to the BLACK BOX project!

---

## Code of Conduct

This project is built to serve senior users with respect, care, and reliability. All contributions should uphold these values:

- **Reliability**: Code must be stable and well-tested
- **Performance**: Must meet or exceed performance targets
- **Accessibility**: Maintain senior-friendly design principles
- **Privacy**: Preserve offline-first, zero-telemetry architecture
- **Documentation**: All changes must be well-documented

---

## How to Contribute

### Reporting Issues

When reporting issues, please include:
- Hardware configuration (Jetson model, memory, etc.)
- Software versions (JetPack, Docker, etc.)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (`docker-compose logs`)
- System metrics (temperature, memory, timing)

### Suggesting Features

Feature suggestions should consider:
- Alignment with offline-first architecture
- Performance impact (must stay within 13s budget)
- Senior-user accessibility
- Hardware constraints (8GB Jetson Orin Nano)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** with clear commit messages
4. **Test thoroughly** on Jetson Orin Nano hardware
5. **Update documentation** for any user-facing changes
6. **Submit PR** with detailed description

---

## Development Guidelines

### Performance Requirements

All changes must maintain performance targets:
- ASR: ≤2.5 seconds
- LLM: ≤7.5 seconds (≥25 tokens/second)
- TTS: ≤1.5 seconds
- Total: ≤13 seconds

Test with: `make test` and `curl http://localhost:8000/metrics`

### Code Style

- **Python**: Follow PEP 8, use type hints
- **JavaScript**: ES6+, consistent formatting
- **Docker**: Multi-stage builds, minimal layers
- **Shell**: ShellCheck compliant

### Testing

Before submitting:
- [ ] Test on actual Jetson Orin Nano hardware
- [ ] Verify all services start: `docker-compose ps`
- [ ] Check health endpoint: `curl http://localhost:8000/health`
- [ ] Run performance tests
- [ ] Verify thermal behavior under load
- [ ] Test offline operation (disconnect network)

### Documentation

Update documentation for:
- New features → README.md, DEPLOYMENT.md
- Performance changes → PERFORMANCE.md
- Bug fixes → TROUBLESHOOTING.md
- Breaking changes → CHANGELOG.md

---

## Architecture Constraints

### Non-Negotiable Requirements

These requirements **cannot be compromised**:

1. **TensorRT-LLM with INT4**: No generic llama.cpp or Ollama
2. **3B Models Only**: No 7B+ models (too slow)
3. **Shared Memory IPC**: No HTTP between services
4. **15W Power Mode**: Required for performance
5. **ALSA Direct**: No PulseAudio
6. **GUI Disabled**: Required for memory
7. **16GB SWAP**: Required for stability
8. **Offline-First**: Zero external dependencies

### Approved Changes

Acceptable areas for contribution:
- Performance optimizations (within architecture)
- Bug fixes
- Documentation improvements
- UI/UX enhancements (maintaining accessibility)
- Additional features (offline-compatible)
- Testing improvements
- Hardware compatibility (similar ARM platforms)

### Requires Discussion

Changes requiring community discussion:
- Major architecture changes
- New external dependencies
- Changes to core performance targets
- Security-related changes
- Breaking changes

---

## Development Setup

### Requirements
- NVIDIA Jetson Orin Nano (8GB)
- Ubuntu 22.04 + JetPack SDK
- Docker + NVIDIA runtime
- 50GB+ free space

### Setup
```bash
git clone <repository>
cd blackbox
make setup  # Run system configuration
make build  # Build Docker images
make start  # Start services
```

### Testing
```bash
make test    # Basic functionality test
make health  # Health check
make metrics # Performance metrics
```

---

## Priority Areas

We especially welcome contributions in:

1. **Performance Optimization**
   - TensorRT-LLM engine tuning
   - IPC optimization
   - Thermal management improvements

2. **Testing**
   - Unit tests for core components
   - Integration tests
   - Performance benchmarks
   - Stress tests

3. **Documentation**
   - Deployment guides for specific hardware
   - Troubleshooting scenarios
   - Performance tuning tips
   - Video tutorials

4. **Accessibility**
   - UI improvements for seniors
   - Voice command expansion
   - Alternative input methods

5. **Model Optimization**
   - Fine-tuning for senior use cases
   - Function calling improvements
   - Context management

---

## Review Process

1. **Submission**: Create pull request with description
2. **Automated Checks**: CI/CD runs (if configured)
3. **Code Review**: Maintainers review code
4. **Testing**: Test on real hardware
5. **Documentation**: Verify docs updated
6. **Merge**: Approved PRs are merged

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

- Open an issue for questions
- Review existing documentation
- Check troubleshooting guide

Thank you for helping make BLACK BOX better! 🎉

