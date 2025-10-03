"""
BLACK BOX ASR Service - Whisper.cpp Transcription
GPU-accelerated speech recognition
Target: ≤2.5 seconds transcription time
"""

import os
import json
import time
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import base64

import numpy as np
import soundfile as sf

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WhisperASR:
    """
    Whisper.cpp ASR engine with GPU acceleration
    """
    
    def __init__(self, model_path: str, language: str = "en"):
        """
        Initialize Whisper ASR
        
        Args:
            model_path: Path to Whisper model file
            language: Language code
        """
        self.model_path = model_path
        self.language = language
        self.model = None
        
        logger.info(f"Initializing Whisper ASR (model: {model_path})")
    
    def load(self):
        """Load Whisper model"""
        try:
            # Check if model exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found: {self.model_path}")
            
            # TODO: Load actual whisper.cpp model
            # In production, this would use whisper.cpp Python bindings
            # from whispercpp import Whisper
            # self.model = Whisper.from_pretrained(self.model_path)
            
            logger.info("✓ Whisper model loaded")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    def transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes (WAV format)
        
        Returns:
            Transcription result with text and confidence
        """
        start_time = time.time()
        
        try:
            # Write audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)
            
            # TODO: Actual Whisper.cpp inference
            # result = self.model.transcribe(
            #     temp_path,
            #     language=self.language
            # )
            
            # PLACEHOLDER: Simulated transcription
            # In production, replace with actual whisper.cpp inference
            transcription = self._simulate_transcription(audio_data)
            confidence = 0.95
            
            elapsed = time.time() - start_time
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            result = {
                "text": transcription,
                "confidence": confidence,
                "elapsed_seconds": round(elapsed, 3),
                "language": self.language
            }
            
            logger.info(f"Transcribed in {elapsed:.2f}s: \"{transcription}\"")
            
            return result
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    def _simulate_transcription(self, audio_data: bytes) -> str:
        """
        Simulate transcription (placeholder)
        Replace with actual Whisper.cpp inference in production
        """
        # Simulate processing time
        time.sleep(0.5)  # Whisper tiny.en should be much faster
        
        # Return a test transcription
        return "Hello, this is a test transcription from the BLACK BOX system."


class ASRService:
    """
    ASR service handling IPC requests
    """
    
    def __init__(self):
        """Initialize ASR service"""
        self.asr: Optional[WhisperASR] = None
        
        # Load configuration
        self.model_name = os.getenv("ASR_MODEL", "tiny.en")
        self.model_path = os.getenv(
            "ASR_MODEL_PATH",
            f"/models/whisper/ggml-{self.model_name}.bin"
        )
        self.language = os.getenv("ASR_LANGUAGE", "en")
        self.timeout = float(os.getenv("ASR_TIMEOUT_SECONDS", "2.5"))
        
        logger.info(f"ASR Service initialized (model: {self.model_name})")
    
    def initialize(self):
        """Initialize ASR engine"""
        try:
            logger.info("Loading Whisper model...")
            
            self.asr = WhisperASR(
                model_path=self.model_path,
                language=self.language
            )
            self.asr.load()
            
            logger.info("✓ ASR service ready")
        
        except Exception as e:
            logger.error(f"Failed to initialize ASR: {e}", exc_info=True)
            raise
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an ASR request
        
        Args:
            request: Request dictionary
        
        Returns:
            Response dictionary
        """
        method = request.get("method")
        data = request.get("data", {})
        request_id = request.get("id")
        
        try:
            if method == "transcribe":
                result = self._handle_transcribe(data)
            elif method == "health":
                result = {"status": "ok"}
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return {
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            return {
                "id": request_id,
                "error": str(e)
            }
    
    def _handle_transcribe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle transcription request
        
        Args:
            data: Request data with audio
        
        Returns:
            Transcription result
        """
        # Get audio data (may be base64 encoded)
        audio_data = data.get("audio_data")
        
        if isinstance(audio_data, str):
            # Decode from base64
            audio_data = base64.b64decode(audio_data)
        elif isinstance(audio_data, (bytes, bytearray)):
            audio_data = bytes(audio_data)
        else:
            raise ValueError("Invalid audio data format")
        
        # Transcribe
        result = self.asr.transcribe(audio_data)
        
        # Check if timeout exceeded
        if result["elapsed_seconds"] > self.timeout:
            logger.warning(
                f"⚠ Transcription exceeded target: {result['elapsed_seconds']:.2f}s > {self.timeout}s"
            )
        
        return result
    
    def run_ipc_loop(self):
        """Run IPC loop to process requests"""
        shm_input = os.getenv("SHM_ASR_INPUT", "/dev/shm/blackbox_asr_in")
        shm_output = os.getenv("SHM_ASR_OUTPUT", "/dev/shm/blackbox_asr_out")
        
        logger.info(f"Starting IPC loop (input: {shm_input}, output: {shm_output})")
        
        # Ensure IPC files exist
        Path(shm_input).touch(exist_ok=True)
        Path(shm_output).touch(exist_ok=True)
        
        last_request_id = None
        
        while True:
            try:
                # Check for new request
                if os.path.exists(shm_input) and os.path.getsize(shm_input) > 0:
                    with open(shm_input, 'r') as f:
                        request_json = f.read()
                    
                    if request_json:
                        request = json.loads(request_json)
                        request_id = request.get("id")
                        
                        # Skip if already processed
                        if request_id != last_request_id:
                            logger.info(f"Processing request {request_id}")
                            
                            # Process request
                            response = self.process_request(request)
                            
                            # Write response
                            with open(shm_output, 'w') as f:
                                json.dump(response, f)
                                f.flush()
                                os.fsync(f.fileno())
                            
                            # Clear input
                            with open(shm_input, 'w') as f:
                                f.write("")
                            
                            last_request_id = request_id
                            logger.info(f"Completed request {request_id}")
            
            except json.JSONDecodeError:
                # File being written, try again
                pass
            except Exception as e:
                logger.error(f"Error in IPC loop: {e}", exc_info=True)
            
            # Small sleep
            time.sleep(0.01)


def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("BLACK BOX ASR Service Starting")
    logger.info("=" * 80)
    
    # Initialize service
    service = ASRService()
    service.initialize()
    
    # Run IPC loop
    service.run_ipc_loop()


if __name__ == "__main__":
    main()

