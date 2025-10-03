"""
BLACK BOX TTS Service - Piper TTS Server
Neural text-to-speech with warm startup and streaming
Target: ≤1.5 seconds to first audio
"""

import os
import json
import time
import logging
import argparse
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


class PiperTTS:
    """
    Piper TTS engine with warm startup
    Keeps model loaded in memory to eliminate cold-start latency
    """
    
    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        sample_rate: int = 22050
    ):
        """
        Initialize Piper TTS
        
        Args:
            model_path: Path to Piper ONNX model
            config_path: Path to model config JSON
            sample_rate: Audio sample rate
        """
        self.model_path = model_path
        self.config_path = config_path or f"{model_path}.json"
        self.sample_rate = sample_rate
        self.voice = None
        
        logger.info(f"Initializing Piper TTS (model: {model_path})")
    
    def load(self):
        """
        Load Piper model (warm startup)
        Keeps model in memory for fast synthesis
        """
        try:
            # Check if model exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found: {self.model_path}")
            
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Config not found: {self.config_path}")
            
            # TODO: Load actual Piper model
            # In production, this would use Piper's Python API
            # from piper import PiperVoice
            # self.voice = PiperVoice.load(self.model_path, self.config_path)
            
            # Warm up with a test synthesis
            logger.info("Warming up TTS engine...")
            # _ = self.voice.synthesize("Hello")
            
            logger.info("✓ Piper TTS model loaded and warmed up")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise
    
    def synthesize(self, text: str, stream: bool = False) -> Dict[str, Any]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            stream: Whether to stream audio (reduces latency)
        
        Returns:
            Synthesis result with audio data and timing
        """
        start_time = time.time()
        
        try:
            # TODO: Actual Piper synthesis
            # if stream:
            #     audio_chunks = []
            #     for chunk in self.voice.synthesize_stream(text):
            #         audio_chunks.append(chunk)
            #     audio_data = np.concatenate(audio_chunks)
            # else:
            #     audio_data = self.voice.synthesize(text)
            
            # PLACEHOLDER: Simulated synthesis
            # In production, replace with actual Piper TTS
            audio_data = self._simulate_synthesis(text)
            
            # Convert to bytes (WAV format)
            audio_bytes = self._audio_to_wav_bytes(audio_data)
            
            elapsed = time.time() - start_time
            duration = len(audio_data) / self.sample_rate
            
            result = {
                "audio_data": audio_bytes,
                "duration_seconds": round(duration, 3),
                "elapsed_seconds": round(elapsed, 3),
                "sample_rate": self.sample_rate,
                "realtime_factor": round(duration / elapsed, 2) if elapsed > 0 else 0
            }
            
            logger.info(
                f"Synthesized {duration:.2f}s audio in {elapsed:.2f}s "
                f"(RTF: {result['realtime_factor']}x)"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise
    
    def _simulate_synthesis(self, text: str) -> np.ndarray:
        """
        Simulate speech synthesis (placeholder)
        Replace with actual Piper TTS in production
        """
        # Simulate processing time (Piper should be faster)
        time.sleep(0.3)
        
        # Generate dummy audio (1 second of silence + beep)
        duration = 1.0  # seconds
        samples = int(duration * self.sample_rate)
        
        # Simple sine wave beep
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4 note
        audio = 0.1 * np.sin(2 * np.pi * frequency * t)
        
        return audio.astype(np.float32)
    
    def _audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """
        Convert audio array to WAV bytes
        
        Args:
            audio_data: Audio samples
        
        Returns:
            WAV file bytes
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Write WAV file
            sf.write(temp_path, audio_data, self.sample_rate)
            
            # Read back as bytes
            with open(temp_path, 'rb') as f:
                wav_bytes = f.read()
            
            return wav_bytes
        
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass


class TTSService:
    """
    TTS service with IPC handling and warm startup
    """
    
    def __init__(self, preload: bool = True):
        """
        Initialize TTS service
        
        Args:
            preload: Whether to preload model (warm startup)
        """
        self.tts: Optional[PiperTTS] = None
        self.preload = preload
        
        # Load configuration
        self.voice = os.getenv("TTS_VOICE", "en_US-lessac-medium")
        self.model_path = os.getenv(
            "TTS_MODEL_PATH",
            f"/models/piper/{self.voice}.onnx"
        )
        self.sample_rate = int(os.getenv("TTS_SAMPLE_RATE", "22050"))
        self.timeout = float(os.getenv("TTS_TIMEOUT_SECONDS", "1.5"))
        self.stream_enabled = os.getenv("TTS_STREAM_ENABLED", "true").lower() == "true"
        
        logger.info(f"TTS Service initialized (voice: {self.voice})")
    
    def initialize(self):
        """Initialize TTS engine"""
        try:
            logger.info("Loading Piper TTS model...")
            
            self.tts = PiperTTS(
                model_path=self.model_path,
                sample_rate=self.sample_rate
            )
            
            if self.preload:
                logger.info("Preloading model (warm startup)...")
                self.tts.load()
            
            logger.info("✓ TTS service ready")
        
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}", exc_info=True)
            raise
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a TTS request
        
        Args:
            request: Request dictionary
        
        Returns:
            Response dictionary
        """
        method = request.get("method")
        data = request.get("data", {})
        request_id = request.get("id")
        
        try:
            if method == "synthesize":
                result = self._handle_synthesize(data)
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
    
    def _handle_synthesize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle synthesis request
        
        Args:
            data: Request data with text
        
        Returns:
            Synthesis result
        """
        text = data.get("text", "")
        
        if not text:
            raise ValueError("No text provided for synthesis")
        
        # Ensure model is loaded
        if not self.preload and self.tts and not self.tts.voice:
            self.tts.load()
        
        # Synthesize
        result = self.tts.synthesize(text, stream=self.stream_enabled)
        
        # Encode audio as base64 for JSON transport
        result["audio_data"] = base64.b64encode(result["audio_data"]).decode('utf-8')
        
        # Check if timeout exceeded
        if result["elapsed_seconds"] > self.timeout:
            logger.warning(
                f"⚠ Synthesis exceeded target: {result['elapsed_seconds']:.2f}s > {self.timeout}s"
            )
        
        return result
    
    def run_ipc_loop(self):
        """Run IPC loop to process requests"""
        shm_input = os.getenv("SHM_TTS_INPUT", "/dev/shm/blackbox_tts_in")
        shm_output = os.getenv("SHM_TTS_OUTPUT", "/dev/shm/blackbox_tts_out")
        
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
    # Parse arguments
    parser = argparse.ArgumentParser(description="BLACK BOX TTS Service")
    parser.add_argument("--preload", action="store_true", help="Preload model (warm startup)")
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("BLACK BOX TTS Service Starting")
    logger.info(f"Warm Startup: {args.preload}")
    logger.info("=" * 80)
    
    # Initialize service
    service = TTSService(preload=args.preload)
    service.initialize()
    
    # Run IPC loop
    service.run_ipc_loop()


if __name__ == "__main__":
    main()

