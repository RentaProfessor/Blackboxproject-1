#!/bin/bash
# BLACK BOX - Installation Verification Script
# Verifies that all components are properly installed and configured

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "============================================================================"
echo "BLACK BOX - Installation Verification"
echo "============================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_warning "Some checks require root privileges (use sudo)"
fi

# ============================================================================
# System Configuration Checks
# ============================================================================

log_info "Checking system configuration..."

# Check power mode
if command -v nvpmodel &> /dev/null; then
    POWER_MODE=$(nvpmodel -q | grep "NV Power Mode" | awk '{print $4}')
    if [ "$POWER_MODE" = "MODE_15W" ]; then
        log_success "15W power mode configured"
    else
        log_warning "Power mode: $POWER_MODE (should be MODE_15W)"
    fi
else
    log_warning "nvpmodel not found"
fi

# Check GUI disabled
BOOT_TARGET=$(systemctl get-default)
if [ "$BOOT_TARGET" = "multi-user.target" ]; then
    log_success "GUI disabled (multi-user.target)"
else
    log_warning "Boot target: $BOOT_TARGET (should be multi-user.target)"
fi

# Check SWAP
SWAP_SIZE=$(free -h | grep Swap | awk '{print $2}')
if [[ "$SWAP_SIZE" == *"16G"* ]] || [[ "$SWAP_SIZE" == *"16.0G"* ]]; then
    log_success "16GB SWAP configured"
else
    log_warning "SWAP size: $SWAP_SIZE (should be ~16G)"
fi

# Check ZRAM disabled
if ! systemctl is-enabled nvzramconfig &> /dev/null; then
    log_success "ZRAM disabled"
else
    log_warning "ZRAM still enabled"
fi

# Check ALSA configuration
if [ -f /etc/asound.conf ]; then
    log_success "ALSA configuration present"
else
    log_warning "ALSA configuration not found"
fi

# ============================================================================
# Docker and Services Checks
# ============================================================================

log_info "Checking Docker and services..."

# Check Docker
if systemctl is-active --quiet docker; then
    log_success "Docker service running"
else
    log_error "Docker service not running"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    log_success "Docker Compose available"
else
    log_error "Docker Compose not found"
fi

# Check NVIDIA Docker runtime
if docker info | grep -q "nvidia"; then
    log_success "NVIDIA Docker runtime configured"
else
    log_warning "NVIDIA Docker runtime not detected"
fi

# Check services
if [ -f docker-compose.yml ]; then
    log_info "Checking service status..."
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Services are running"
        
        # Check individual services
        SERVICES=("orchestrator" "llm-service" "asr-service" "tts-service" "ui")
        for service in "${SERVICES[@]}"; do
            if docker-compose ps | grep -q "$service.*Up"; then
                log_success "$service is running"
            else
                log_error "$service is not running"
            fi
        done
    else
        log_error "No services are running"
    fi
else
    log_error "docker-compose.yml not found"
fi

# ============================================================================
# Health Endpoint Checks
# ============================================================================

log_info "Checking service health..."

# Check orchestrator health
if curl -s http://localhost:8000/health > /dev/null; then
    log_success "Orchestrator health endpoint responding"
    
    # Get health details
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
        log_success "All services healthy"
    else
        log_warning "Some services may not be healthy"
    fi
else
    log_error "Orchestrator health endpoint not responding"
fi

# Check UI
if curl -s http://localhost:3000 > /dev/null; then
    log_success "UI service responding"
else
    log_error "UI service not responding"
fi

# ============================================================================
# Performance Checks
# ============================================================================

log_info "Checking performance metrics..."

if curl -s http://localhost:8000/metrics > /dev/null; then
    log_success "Metrics endpoint responding"
    
    # Check if we can get metrics
    METRICS=$(curl -s http://localhost:8000/metrics)
    if echo "$METRICS" | grep -q "pipeline_ready"; then
        log_success "Pipeline is ready"
    else
        log_warning "Pipeline may not be ready"
    fi
else
    log_warning "Metrics endpoint not responding"
fi

# ============================================================================
# Thermal Status
# ============================================================================

log_info "Checking thermal status..."

if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP / 1000))
    
    if [ $TEMP_C -lt 75 ]; then
        log_success "Temperature: ${TEMP_C}°C (normal)"
    elif [ $TEMP_C -lt 85 ]; then
        log_warning "Temperature: ${TEMP_C}°C (warm)"
    else
        log_error "Temperature: ${TEMP_C}°C (hot - may throttle)"
    fi
else
    log_warning "Thermal sensors not accessible"
fi

# ============================================================================
# Model Files Check
# ============================================================================

log_info "Checking model files..."

# Check LLM engine
if [ -d "llm-service/models/engines" ]; then
    ENGINE_COUNT=$(find llm-service/models/engines -name "*.engine" -o -name "*.trt" | wc -l)
    if [ $ENGINE_COUNT -gt 0 ]; then
        log_success "LLM engine files found ($ENGINE_COUNT files)"
    else
        log_warning "No LLM engine files found - you may need to build the engine"
    fi
else
    log_warning "LLM models directory not found"
fi

# Check Whisper models
if [ -d "asr-service/models" ]; then
    WHISPER_COUNT=$(find asr-service/models -name "*.bin" | wc -l)
    if [ $WHISPER_COUNT -gt 0 ]; then
        log_success "Whisper model files found ($WHISPER_COUNT files)"
    else
        log_warning "No Whisper model files found"
    fi
else
    log_warning "ASR models directory not found"
fi

# Check Piper models
if [ -d "tts-service/models" ]; then
    PIPER_COUNT=$(find tts-service/models -name "*.onnx" | wc -l)
    if [ $PIPER_COUNT -gt 0 ]; then
        log_success "Piper model files found ($PIPER_COUNT files)"
    else
        log_warning "No Piper model files found"
    fi
else
    log_warning "TTS models directory not found"
fi

# ============================================================================
# Database Check
# ============================================================================

log_info "Checking database..."

if [ -f "data/blackbox.db" ]; then
    log_success "Database file exists"
    
    # Check if database is accessible
    if docker-compose exec -T orchestrator python3 -c "import sqlite3; sqlite3.connect('/data/blackbox.db')" 2>/dev/null; then
        log_success "Database is accessible"
    else
        log_warning "Database may not be properly initialized"
    fi
else
    log_warning "Database file not found - run vault initialization"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "============================================================================"
echo "Verification Summary"
echo "============================================================================"
echo ""

# Count successes and failures
SUCCESS_COUNT=$(grep -c "\[✓\]" <<< "$(history | tail -n +2)")
WARNING_COUNT=$(grep -c "\[⚠\]" <<< "$(history | tail -n +2)")
ERROR_COUNT=$(grep -c "\[✗\]" <<< "$(history | tail -n +2)")

echo "Results:"
echo "  ✓ Successes: $SUCCESS_COUNT"
echo "  ⚠ Warnings: $WARNING_COUNT"
echo "  ✗ Errors: $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    if [ $WARNING_COUNT -eq 0 ]; then
        log_success "All checks passed! BLACK BOX is ready to use."
        echo ""
        echo "Next steps:"
        echo "  1. Test voice interaction: http://localhost:3000"
        echo "  2. Check performance: curl http://localhost:8000/metrics"
        echo "  3. Monitor thermal: curl http://localhost:8000/thermal/status"
    else
        log_warning "Installation mostly successful with some warnings."
        echo ""
        echo "Review warnings above and address as needed."
    fi
else
    log_error "Installation has errors that need to be addressed."
    echo ""
    echo "Please:"
    echo "  1. Review errors above"
    echo "  2. Check logs: docker-compose logs"
    echo "  3. Re-run installation if needed: sudo ./install.sh"
fi

echo ""
echo "============================================================================"
