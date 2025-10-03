"""
BLACK BOX Orchestrator - Voice Pipeline
Manages ASR → LLM → TTS pipeline with timing and context management
"""

import time
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from uuid import uuid4

from ipc import IPCManager
from thermal import ThermalMonitor, ThermalState


logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Coordinates the complete voice interaction pipeline:
    Audio Input → ASR → LLM → TTS → Audio Output
    
    Performance targets:
    - ASR: ≤2.5 seconds
    - LLM: ≤7.5 seconds (≥25 tokens/second)
    - TTS: ≤1.5 seconds
    - Orchestration: ≤0.5 seconds
    - Total: ≤13 seconds
    """
    
    def __init__(self, database, thermal_monitor: ThermalMonitor, settings):
        """
        Initialize voice pipeline
        
        Args:
            database: Database instance for context/state management
            thermal_monitor: Thermal monitoring instance
            settings: Application settings
        """
        self.database = database
        self.thermal_monitor = thermal_monitor
        self.settings = settings
        
        # IPC manager for service communication
        self.ipc: Optional[IPCManager] = None
        
        # Pipeline state
        self._ready = False
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency": 0.0,
            "asr_average": 0.0,
            "llm_average": 0.0,
            "tts_average": 0.0
        }
        self._latencies = []
        
        # Register thermal callbacks
        self.thermal_monitor.register_callback(
            ThermalState.CRITICAL,
            self._on_thermal_critical
        )
        
        logger.info("Voice pipeline initialized")
    
    async def initialize(self):
        """Initialize all pipeline components"""
        try:
            # Initialize IPC manager
            logger.info("Initializing IPC manager...")
            self.ipc = IPCManager(self.settings)
            await self.ipc.initialize()
            logger.info("✓ IPC manager ready")
            
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            await self._wait_for_services()
            logger.info("✓ All services ready")
            
            self._ready = True
            logger.info("✓ Voice pipeline ready")
        
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
            raise
    
    async def _wait_for_services(self, timeout: float = 60.0):
        """
        Wait for all services to be ready
        
        Args:
            timeout: Maximum time to wait (seconds)
        """
        start_time = time.time()
        services = ["asr", "llm", "tts"]
        ready_services = set()
        
        while len(ready_services) < len(services):
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Services not ready after {timeout}s: {set(services) - ready_services}")
            
            for service in services:
                if service not in ready_services:
                    try:
                        # Try to ping service
                        is_ready = await self.ipc.health_check(service)
                        if is_ready:
                            ready_services.add(service)
                            logger.info(f"✓ {service.upper()} service ready")
                    except Exception as e:
                        logger.debug(f"{service.upper()} not ready: {e}")
            
            if len(ready_services) < len(services):
                await asyncio.sleep(1.0)
    
    def _on_thermal_critical(self, state: ThermalState, temps: Dict[str, float]):
        """
        Callback for critical thermal state
        Implement graceful degradation
        """
        max_temp = max(temps.values())
        logger.error(
            f"⚠ CRITICAL THERMAL STATE: {max_temp:.1f}°C - "
            f"Pipeline may throttle or reject requests"
        )
        # In production, could implement request queuing or rejection here
    
    async def process_voice_input(
        self,
        audio_data: bytes,
        user_id: str = "default_user",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process complete voice interaction through the pipeline
        
        Args:
            audio_data: Raw audio bytes
            user_id: User identifier
            session_id: Session identifier (created if None)
        
        Returns:
            Dictionary with transcription, response, audio, and timing
        """
        if not self._ready:
            raise RuntimeError("Pipeline not ready")
        
        # Check thermal state
        if self.thermal_monitor.should_throttle():
            logger.warning("System in thermal throttle mode")
            # Could implement queue or delay here
        
        # Generate session ID if needed
        if session_id is None:
            session_id = str(uuid4())
        
        # Initialize timing
        timing = {}
        pipeline_start = time.time()
        
        try:
            # ================================================================
            # STEP 1: ASR (Automatic Speech Recognition)
            # Target: ≤2.5 seconds
            # ================================================================
            logger.info(f"[{session_id}] Starting ASR...")
            asr_start = time.time()
            
            transcription_result = await self.ipc.call_service(
                service="asr",
                method="transcribe",
                data={"audio_data": audio_data},
                timeout=self.settings.asr_timeout_seconds
            )
            
            asr_time = time.time() - asr_start
            timing["asr"] = round(asr_time, 3)
            
            transcription = transcription_result.get("text", "")
            logger.info(f"[{session_id}] ASR complete ({asr_time:.2f}s): \"{transcription}\"")
            
            if asr_time > self.settings.asr_timeout_seconds:
                logger.warning(f"⚠ ASR exceeded target: {asr_time:.2f}s > {self.settings.asr_timeout_seconds}s")
            
            # ================================================================
            # STEP 2: Retrieve Context
            # Target: <0.1 seconds
            # ================================================================
            context_start = time.time()
            user_context = await self.database.get_user_context(user_id)
            timing["context_retrieval"] = round(time.time() - context_start, 3)
            
            # ================================================================
            # STEP 3: LLM (Language Model Inference)
            # Target: ≤7.5 seconds @ ≥25 tokens/second
            # ================================================================
            logger.info(f"[{session_id}] Starting LLM inference...")
            llm_start = time.time()
            
            llm_result = await self.ipc.call_service(
                service="llm",
                method="generate",
                data={
                    "prompt": transcription,
                    "context": user_context,
                    "max_tokens": self.settings.llm_max_tokens,
                    "user_id": user_id
                },
                timeout=self.settings.llm_timeout_seconds
            )
            
            llm_time = time.time() - llm_start
            timing["llm"] = round(llm_time, 3)
            
            response_text = llm_result.get("text", "")
            function_calls = llm_result.get("function_calls", [])
            tokens_generated = llm_result.get("tokens", 0)
            
            # Calculate tokens per second
            if llm_time > 0 and tokens_generated > 0:
                tokens_per_second = tokens_generated / llm_time
                timing["llm_tokens_per_second"] = round(tokens_per_second, 2)
                
                logger.info(
                    f"[{session_id}] LLM complete ({llm_time:.2f}s, "
                    f"{tokens_per_second:.1f} tok/s): \"{response_text[:50]}...\""
                )
                
                if tokens_per_second < self.settings.llm_target_tps:
                    logger.warning(
                        f"⚠ LLM below target throughput: {tokens_per_second:.1f} < "
                        f"{self.settings.llm_target_tps} tok/s"
                    )
            
            # ================================================================
            # STEP 4: Execute Function Calls (if any)
            # Target: <0.5 seconds
            # ================================================================
            if function_calls:
                func_start = time.time()
                logger.info(f"[{session_id}] Executing {len(function_calls)} function calls...")
                await self._execute_function_calls(function_calls, user_id)
                timing["function_execution"] = round(time.time() - func_start, 3)
            
            # ================================================================
            # STEP 5: Update Context
            # Target: <0.1 seconds
            # ================================================================
            context_update_start = time.time()
            await self.database.add_message(user_id, "user", transcription)
            await self.database.add_message(user_id, "assistant", response_text)
            timing["context_update"] = round(time.time() - context_update_start, 3)
            
            # ================================================================
            # STEP 6: TTS (Text-to-Speech)
            # Target: ≤1.5 seconds
            # ================================================================
            logger.info(f"[{session_id}] Starting TTS...")
            tts_start = time.time()
            
            tts_result = await self.ipc.call_service(
                service="tts",
                method="synthesize",
                data={"text": response_text},
                timeout=self.settings.tts_timeout_seconds
            )
            
            tts_time = time.time() - tts_start
            timing["tts"] = round(tts_time, 3)
            
            audio_data = tts_result.get("audio_data")
            logger.info(f"[{session_id}] TTS complete ({tts_time:.2f}s)")
            
            if tts_time > self.settings.tts_timeout_seconds:
                logger.warning(f"⚠ TTS exceeded target: {tts_time:.2f}s > {self.settings.tts_timeout_seconds}s")
            
            # ================================================================
            # Calculate total time
            # ================================================================
            total_time = time.time() - pipeline_start
            timing["total"] = round(total_time, 3)
            timing["orchestration_overhead"] = round(
                total_time - (asr_time + llm_time + tts_time),
                3
            )
            
            # Update metrics
            self._update_metrics(timing)
            
            # Log summary
            logger.info(
                f"[{session_id}] Pipeline complete: {total_time:.2f}s "
                f"(ASR: {asr_time:.2f}s, LLM: {llm_time:.2f}s, TTS: {tts_time:.2f}s)"
            )
            
            # Return result
            return {
                "success": True,
                "transcription": transcription,
                "response_text": response_text,
                "audio_url": f"/audio/{session_id}",  # TODO: Implement audio storage
                "function_calls": function_calls,
                "timing": timing,
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"[{session_id}] Pipeline failed: {e}", exc_info=True)
            self._metrics["failed_requests"] += 1
            raise
    
    async def transcribe_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe audio only (no LLM or TTS)
        
        Args:
            audio_data: Raw audio bytes
        
        Returns:
            Transcription result with timing
        """
        start_time = time.time()
        
        result = await self.ipc.call_service(
            service="asr",
            method="transcribe",
            data={"audio_data": audio_data},
            timeout=self.settings.asr_timeout_seconds
        )
        
        elapsed = time.time() - start_time
        
        return {
            "transcription": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "timing": {"asr": round(elapsed, 3)}
        }
    
    async def process_text_input(
        self,
        text: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process text input (bypasses ASR, for testing)
        
        Args:
            text: Input text
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            Response with timing
        """
        if session_id is None:
            session_id = str(uuid4())
        
        timing = {}
        start_time = time.time()
        
        # Get context
        user_context = await self.database.get_user_context(user_id)
        
        # LLM inference
        llm_start = time.time()
        llm_result = await self.ipc.call_service(
            service="llm",
            method="generate",
            data={
                "prompt": text,
                "context": user_context,
                "max_tokens": self.settings.llm_max_tokens,
                "user_id": user_id
            },
            timeout=self.settings.llm_timeout_seconds
        )
        timing["llm"] = round(time.time() - llm_start, 3)
        
        response_text = llm_result.get("text", "")
        function_calls = llm_result.get("function_calls", [])
        
        # Execute functions if any
        if function_calls:
            await self._execute_function_calls(function_calls, user_id)
        
        # Update context
        await self.database.add_message(user_id, "user", text)
        await self.database.add_message(user_id, "assistant", response_text)
        
        # TTS
        tts_start = time.time()
        tts_result = await self.ipc.call_service(
            service="tts",
            method="synthesize",
            data={"text": response_text},
            timeout=self.settings.tts_timeout_seconds
        )
        timing["tts"] = round(time.time() - tts_start, 3)
        
        timing["total"] = round(time.time() - start_time, 3)
        
        return {
            "success": True,
            "transcription": text,
            "response_text": response_text,
            "audio_url": f"/audio/{session_id}",
            "function_calls": function_calls,
            "timing": timing,
            "session_id": session_id
        }
    
    async def _execute_function_calls(self, function_calls: list, user_id: str):
        """
        Execute function calls returned by LLM
        
        Args:
            function_calls: List of function call dictionaries
            user_id: User identifier
        """
        for func_call in function_calls:
            func_name = func_call.get("name")
            func_args = func_call.get("arguments", {})
            
            logger.info(f"Executing function: {func_name}({func_args})")
            
            try:
                if func_name == "set_reminder":
                    await self.database.create_reminder(user_id, **func_args)
                elif func_name == "access_vault":
                    # Vault access handled separately for security
                    logger.info("Vault access requested")
                elif func_name == "play_media":
                    # Media playback integration
                    logger.info(f"Media playback requested: {func_args}")
                else:
                    logger.warning(f"Unknown function call: {func_name}")
            
            except Exception as e:
                logger.error(f"Function execution failed ({func_name}): {e}", exc_info=True)
    
    def _update_metrics(self, timing: Dict[str, float]):
        """
        Update pipeline metrics
        
        Args:
            timing: Timing dictionary from request
        """
        self._metrics["total_requests"] += 1
        self._metrics["successful_requests"] += 1
        
        # Store latency
        self._latencies.append(timing["total"])
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        
        # Calculate averages
        self._metrics["average_latency"] = round(sum(self._latencies) / len(self._latencies), 3)
        
        # Component averages (rolling)
        for component in ["asr", "llm", "tts"]:
            if component in timing:
                key = f"{component}_average"
                # Simple exponential moving average
                alpha = 0.2
                if self._metrics[key] == 0:
                    self._metrics[key] = timing[component]
                else:
                    self._metrics[key] = round(
                        alpha * timing[component] + (1 - alpha) * self._metrics[key],
                        3
                    )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get pipeline performance metrics
        
        Returns:
            Dictionary of metrics
        """
        return {
            **self._metrics,
            "thermal_status": self.thermal_monitor.get_status(),
            "pipeline_ready": self._ready
        }
    
    def is_ready(self) -> bool:
        """Check if pipeline is ready"""
        return self._ready
    
    async def shutdown(self):
        """Shutdown pipeline and cleanup"""
        logger.info("Shutting down voice pipeline...")
        
        if self.ipc:
            await self.ipc.shutdown()
        
        self._ready = False
        logger.info("Voice pipeline shutdown complete")

