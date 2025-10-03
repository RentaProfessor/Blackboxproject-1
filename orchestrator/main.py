"""
BLACK BOX Orchestrator - Main FastAPI Application
Coordinates ASR → LLM → TTS pipeline with thermal monitoring
"""

import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from pipeline import VoicePipeline
from thermal import ThermalMonitor
from database.db import Database
from config import Settings

# ============================================================================
# Configuration
# ============================================================================

# Load settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Global instances
# ============================================================================

pipeline: Optional[VoicePipeline] = None
thermal_monitor: Optional[ThermalMonitor] = None
database: Optional[Database] = None

# ============================================================================
# Lifespan management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic for the application
    """
    global pipeline, thermal_monitor, database
    
    logger.info("=" * 80)
    logger.info("BLACK BOX Orchestrator Starting")
    logger.info("=" * 80)
    
    try:
        # Initialize database
        logger.info("Initializing encrypted database...")
        database = Database(
            db_path=settings.database_path,
            encryption_key=settings.database_encryption_key
        )
        await database.initialize()
        logger.info("✓ Database initialized")
        
        # Initialize thermal monitor
        logger.info("Starting thermal monitoring...")
        thermal_monitor = ThermalMonitor(
            warning_temp=settings.thermal_warning_temp,
            critical_temp=settings.thermal_critical_temp,
            cooldown_temp=settings.thermal_cooldown_temp
        )
        thermal_monitor.start()
        logger.info("✓ Thermal monitoring active")
        
        # Initialize voice pipeline
        logger.info("Initializing voice pipeline (ASR → LLM → TTS)...")
        pipeline = VoicePipeline(
            database=database,
            thermal_monitor=thermal_monitor,
            settings=settings
        )
        await pipeline.initialize()
        logger.info("✓ Voice pipeline ready")
        
        logger.info("=" * 80)
        logger.info("BLACK BOX Orchestrator Ready")
        logger.info(f"Listening on {settings.orchestrator_host}:{settings.orchestrator_port}")
        logger.info("=" * 80)
        
        yield  # Application runs
        
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down BLACK BOX Orchestrator...")
        
        if pipeline:
            await pipeline.shutdown()
            logger.info("✓ Pipeline shutdown complete")
        
        if thermal_monitor:
            thermal_monitor.stop()
            logger.info("✓ Thermal monitoring stopped")
        
        if database:
            await database.close()
            logger.info("✓ Database closed")
        
        logger.info("BLACK BOX Orchestrator stopped")

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="BLACK BOX Orchestrator",
    description="Offline Voice Assistant for Seniors - Pipeline Controller",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Offline-only, no external access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class VoiceRequest(BaseModel):
    """Voice interaction request"""
    user_id: str = Field(default="default_user")
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class VoiceResponse(BaseModel):
    """Voice interaction response"""
    success: bool
    transcription: str
    response_text: str
    audio_url: Optional[str] = None
    function_calls: Optional[list] = None
    timing: Dict[str, float]
    session_id: str

class TextRequest(BaseModel):
    """Text-only request (for testing)"""
    text: str
    user_id: str = Field(default="default_user")
    session_id: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, bool]
    thermal: Dict[str, Any]
    memory: Dict[str, Any]
    uptime_seconds: float

# ============================================================================
# Health and Status Endpoints
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "BLACK BOX Orchestrator",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check
    Returns status of all services and system resources
    """
    try:
        # Check service availability
        services = {
            "database": database.is_connected() if database else False,
            "pipeline": pipeline.is_ready() if pipeline else False,
            "thermal_monitor": thermal_monitor.is_running() if thermal_monitor else False,
        }
        
        # Get thermal status
        thermal_status = thermal_monitor.get_status() if thermal_monitor else {}
        
        # Get memory info
        import psutil
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
        
        # Calculate uptime
        uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        
        # Overall status
        all_healthy = all(services.values())
        status = "healthy" if all_healthy else "degraded"
        
        return HealthResponse(
            status=status,
            services=services,
            thermal=thermal_status,
            memory=memory_info,
            uptime_seconds=round(uptime, 2)
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/metrics", response_model=dict)
async def get_metrics():
    """
    Get performance metrics
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    return await pipeline.get_metrics()

# ============================================================================
# Voice Interaction Endpoints
# ============================================================================

@app.post("/voice/interact", response_model=VoiceResponse)
async def voice_interact(
    audio: UploadFile = File(...),
    user_id: str = "default_user",
    session_id: Optional[str] = None
):
    """
    Main voice interaction endpoint
    Processes audio through ASR → LLM → TTS pipeline
    
    Target latency: ≤13 seconds
    """
    start_time = time.time()
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Read audio data
        audio_data = await audio.read()
        logger.info(f"Received audio: {len(audio_data)} bytes from user {user_id}")
        
        # Process through pipeline
        result = await pipeline.process_voice_input(
            audio_data=audio_data,
            user_id=user_id,
            session_id=session_id
        )
        
        # Calculate total time
        total_time = time.time() - start_time
        result["timing"]["total"] = round(total_time, 3)
        
        # Log performance
        if total_time > settings.orchestrator_total_timeout:
            logger.warning(
                f"Pipeline exceeded target latency: {total_time:.2f}s > "
                f"{settings.orchestrator_total_timeout}s"
            )
        else:
            logger.info(f"✓ Pipeline completed in {total_time:.2f}s (target: {settings.orchestrator_total_timeout}s)")
        
        return VoiceResponse(**result)
    
    except Exception as e:
        logger.error(f"Voice interaction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice interaction failed: {str(e)}")

@app.post("/voice/transcribe", response_model=dict)
async def transcribe_only(audio: UploadFile = File(...)):
    """
    Transcribe audio only (no LLM processing)
    For testing and debugging ASR
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        audio_data = await audio.read()
        result = await pipeline.transcribe_audio(audio_data)
        return result
    
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/text/interact", response_model=VoiceResponse)
async def text_interact(request: TextRequest):
    """
    Text-only interaction (bypasses ASR, useful for testing)
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        result = await pipeline.process_text_input(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id
        )
        return VoiceResponse(**result)
    
    except Exception as e:
        logger.error(f"Text interaction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text interaction failed: {str(e)}")

# ============================================================================
# Context Management
# ============================================================================

@app.get("/context/{user_id}", response_model=dict)
async def get_user_context(user_id: str):
    """Get conversation context for a user"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    context = await database.get_user_context(user_id)
    return {"user_id": user_id, "context": context}

@app.delete("/context/{user_id}")
async def clear_user_context(user_id: str):
    """Clear conversation context for a user"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    await database.clear_user_context(user_id)
    return {"message": f"Context cleared for user {user_id}"}

# ============================================================================
# Thermal Management
# ============================================================================

@app.get("/thermal/status", response_model=dict)
async def get_thermal_status():
    """Get current thermal status"""
    if not thermal_monitor:
        raise HTTPException(status_code=503, detail="Thermal monitor not initialized")
    
    return thermal_monitor.get_status()

@app.post("/thermal/cooldown")
async def trigger_cooldown():
    """Manually trigger thermal cooldown"""
    if not thermal_monitor:
        raise HTTPException(status_code=503, detail="Thermal monitor not initialized")
    
    thermal_monitor.trigger_cooldown()
    return {"message": "Cooldown triggered"}

# ============================================================================
# Application Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Record startup time for uptime calculation"""
    app.state.start_time = time.time()
    logger.info("Application startup event completed")

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.orchestrator_host,
        port=settings.orchestrator_port,
        workers=settings.orchestrator_workers,
        log_level=settings.log_level.lower()
    )

