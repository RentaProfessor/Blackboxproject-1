"""
BLACK BOX Orchestrator - Configuration Management
Loads and validates all environment variables
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # ========================================================================
    # Orchestrator Configuration
    # ========================================================================
    orchestrator_host: str = Field(default="0.0.0.0", env="ORCHESTRATOR_HOST")
    orchestrator_port: int = Field(default=8000, env="ORCHESTRATOR_PORT")
    orchestrator_workers: int = Field(default=1, env="ORCHESTRATOR_WORKERS")
    orchestrator_total_timeout: float = Field(default=13.0, env="ORCHESTRATOR_TOTAL_TIMEOUT")
    
    # ========================================================================
    # Database Configuration
    # ========================================================================
    database_path: str = Field(default="/data/blackbox.db", env="DATABASE_PATH")
    database_encryption_key: str = Field(..., env="DATABASE_ENCRYPTION_KEY")
    
    @validator("database_encryption_key")
    def validate_encryption_key(cls, v):
        if v == "CHANGE_ME_USE_OPENSSL_RAND_HEX_32" or len(v) < 32:
            raise ValueError(
                "DATABASE_ENCRYPTION_KEY must be changed from default and at least 32 characters. "
                "Generate with: openssl rand -hex 32"
            )
        return v
    
    # ========================================================================
    # LLM Service Configuration
    # ========================================================================
    llm_model: str = Field(default="llama-3.2-3b", env="LLM_MODEL")
    llm_engine_path: str = Field(
        default="/models/engines/llama-3.2-3b-int4",
        env="LLM_ENGINE_PATH"
    )
    llm_max_tokens: int = Field(default=150, env="LLM_MAX_TOKENS")
    llm_target_tps: int = Field(default=25, env="LLM_TARGET_TPS")
    llm_timeout_seconds: float = Field(default=7.5, env="LLM_TIMEOUT_SECONDS")
    llm_gpu_memory: int = Field(default=4096, env="LLM_GPU_MEMORY")
    
    # ========================================================================
    # ASR Service Configuration
    # ========================================================================
    asr_model: str = Field(default="tiny.en", env="ASR_MODEL")
    asr_model_path: str = Field(
        default="/models/whisper/tiny.en.bin",
        env="ASR_MODEL_PATH"
    )
    asr_timeout_seconds: float = Field(default=2.5, env="ASR_TIMEOUT_SECONDS")
    asr_language: str = Field(default="en", env="ASR_LANGUAGE")
    asr_sample_rate: int = Field(default=16000, env="ASR_SAMPLE_RATE")
    
    # ========================================================================
    # TTS Service Configuration
    # ========================================================================
    tts_voice: str = Field(default="en_US-lessac-medium", env="TTS_VOICE")
    tts_model_path: str = Field(
        default="/models/piper/en_US-lessac-medium.onnx",
        env="TTS_MODEL_PATH"
    )
    tts_timeout_seconds: float = Field(default=1.5, env="TTS_TIMEOUT_SECONDS")
    tts_sample_rate: int = Field(default=22050, env="TTS_SAMPLE_RATE")
    tts_stream_chunk_size: int = Field(default=1024, env="TTS_STREAM_CHUNK_SIZE")
    
    # ========================================================================
    # IPC Configuration
    # ========================================================================
    ipc_method: str = Field(default="shared_memory", env="IPC_METHOD")
    shm_asr_input: str = Field(default="/dev/shm/blackbox_asr_in", env="SHM_ASR_INPUT")
    shm_asr_output: str = Field(default="/dev/shm/blackbox_asr_out", env="SHM_ASR_OUTPUT")
    shm_llm_input: str = Field(default="/dev/shm/blackbox_llm_in", env="SHM_LLM_INPUT")
    shm_llm_output: str = Field(default="/dev/shm/blackbox_llm_out", env="SHM_LLM_OUTPUT")
    shm_tts_input: str = Field(default="/dev/shm/blackbox_tts_in", env="SHM_TTS_INPUT")
    shm_tts_output: str = Field(default="/dev/shm/blackbox_tts_out", env="SHM_TTS_OUTPUT")
    
    # ========================================================================
    # Context Configuration
    # ========================================================================
    context_max_messages: int = Field(default=10, env="CONTEXT_MAX_MESSAGES")
    context_max_tokens: int = Field(default=2048, env="CONTEXT_MAX_TOKENS")
    
    # ========================================================================
    # Thermal Configuration
    # ========================================================================
    thermal_warning_temp: float = Field(default=75.0, env="THERMAL_WARNING_TEMP")
    thermal_critical_temp: float = Field(default=85.0, env="THERMAL_CRITICAL_TEMP")
    thermal_cooldown_temp: float = Field(default=70.0, env="THERMAL_COOLDOWN_TEMP")
    
    # ========================================================================
    # Logging and Monitoring
    # ========================================================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_path: str = Field(default="/var/log/blackbox", env="LOG_PATH")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    timing_logs: bool = Field(default=True, env="TIMING_LOGS")
    
    # ========================================================================
    # Security Configuration
    # ========================================================================
    argon2_time_cost: int = Field(default=3, env="ARGON2_TIME_COST")
    argon2_memory_cost: int = Field(default=65536, env="ARGON2_MEMORY_COST")
    argon2_parallelism: int = Field(default=4, env="ARGON2_PARALLELISM")
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # ========================================================================
    # Backup Configuration
    # ========================================================================
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_path: str = Field(default="/backups", env="BACKUP_PATH")
    backup_interval_hours: int = Field(default=24, env="BACKUP_INTERVAL_HOURS")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    
    # ========================================================================
    # Debug Flags
    # ========================================================================
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

