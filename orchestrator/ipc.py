"""
BLACK BOX Orchestrator - Inter-Process Communication
High-speed IPC using shared memory for service communication
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class IPCManager:
    """
    Manages inter-process communication between services using shared memory
    
    This implementation uses shared memory files (tmpfs) for maximum speed,
    avoiding TCP/IP overhead. Target overhead: ≤0.5 seconds total.
    """
    
    def __init__(self, settings):
        """
        Initialize IPC manager
        
        Args:
            settings: Application settings with IPC configuration
        """
        self.settings = settings
        self.method = settings.ipc_method
        
        # Shared memory paths for each service
        self.shm_paths = {
            "asr": {
                "input": settings.shm_asr_input,
                "output": settings.shm_asr_output
            },
            "llm": {
                "input": settings.shm_llm_input,
                "output": settings.shm_llm_output
            },
            "tts": {
                "input": settings.shm_tts_input,
                "output": settings.shm_tts_output
            }
        }
        
        # Request tracking
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        
        logger.info(f"IPC manager initialized (method: {self.method})")
    
    async def initialize(self):
        """Initialize IPC channels"""
        try:
            # Ensure shared memory directory exists
            os.makedirs("/dev/shm", exist_ok=True)
            
            # Create/clear shared memory files
            for service, paths in self.shm_paths.items():
                for direction, path in paths.items():
                    # Create empty file
                    Path(path).touch(exist_ok=True)
                    logger.debug(f"Initialized {service} {direction}: {path}")
            
            logger.info("✓ IPC channels initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize IPC: {e}", exc_info=True)
            raise
    
    async def call_service(
        self,
        service: str,
        method: str,
        data: Dict[str, Any],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Call a service method via IPC
        
        Args:
            service: Service name (asr, llm, tts)
            method: Method to call
            data: Method arguments
            timeout: Request timeout (seconds)
        
        Returns:
            Response data from service
        
        Raises:
            TimeoutError: If request times out
            RuntimeError: If request fails
        """
        request_id = self._get_next_request_id()
        
        # Prepare request
        request = {
            "id": request_id,
            "method": method,
            "data": data
        }
        
        try:
            # Write request to service input
            await self._write_request(service, request)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(
                self._wait_for_response(service, request_id),
                timeout=timeout
            )
            
            # Check for errors
            if "error" in response:
                raise RuntimeError(f"{service} error: {response['error']}")
            
            return response.get("result", {})
        
        except asyncio.TimeoutError:
            logger.error(f"{service}.{method} timed out after {timeout}s")
            raise TimeoutError(f"{service}.{method} timed out")
        
        except Exception as e:
            logger.error(f"{service}.{method} failed: {e}", exc_info=True)
            raise
    
    async def _write_request(self, service: str, request: Dict[str, Any]):
        """
        Write request to service input channel
        
        Args:
            service: Service name
            request: Request data
        """
        input_path = self.shm_paths[service]["input"]
        
        try:
            # Serialize request
            request_json = json.dumps(request)
            
            # Write to shared memory file
            async with asyncio.Lock():  # Ensure atomic writes
                with open(input_path, 'w') as f:
                    f.write(request_json)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            
            logger.debug(f"Wrote request to {service}: {request['id']}")
        
        except Exception as e:
            logger.error(f"Failed to write request to {service}: {e}")
            raise
    
    async def _wait_for_response(
        self,
        service: str,
        request_id: int,
        poll_interval: float = 0.01
    ) -> Dict[str, Any]:
        """
        Wait for response from service
        
        Args:
            service: Service name
            request_id: Request ID to match
            poll_interval: Polling interval (seconds)
        
        Returns:
            Response data
        """
        output_path = self.shm_paths[service]["output"]
        
        while True:
            try:
                # Check if response file has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, 'r') as f:
                        response_json = f.read()
                    
                    if response_json:
                        response = json.loads(response_json)
                        
                        # Check if this is our response
                        if response.get("id") == request_id:
                            # Clear the response file
                            with open(output_path, 'w') as f:
                                f.write("")
                            
                            logger.debug(f"Received response from {service}: {request_id}")
                            return response
            
            except json.JSONDecodeError:
                # File being written, try again
                pass
            except Exception as e:
                logger.debug(f"Error reading response from {service}: {e}")
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
    
    async def health_check(self, service: str) -> bool:
        """
        Check if a service is responding
        
        Args:
            service: Service name
        
        Returns:
            True if service is healthy
        """
        try:
            # Try a simple ping
            result = await self.call_service(
                service=service,
                method="health",
                data={},
                timeout=2.0
            )
            return result.get("status") == "ok"
        
        except Exception as e:
            logger.debug(f"{service} health check failed: {e}")
            return False
    
    def _get_next_request_id(self) -> int:
        """Get next request ID"""
        self._request_id += 1
        return self._request_id
    
    async def shutdown(self):
        """Cleanup IPC resources"""
        try:
            # Clean up shared memory files
            for service, paths in self.shm_paths.items():
                for path in paths.values():
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                            logger.debug(f"Removed {path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {path}: {e}")
            
            logger.info("IPC shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during IPC shutdown: {e}")


class HTTPIPCManager(IPCManager):
    """
    Alternative IPC implementation using HTTP (fallback)
    Less efficient but easier for development/debugging
    """
    
    def __init__(self, settings):
        super().__init__(settings)
        
        # Service URLs (for Docker internal networking)
        self.service_urls = {
            "asr": "http://blackbox-asr:8001",
            "llm": "http://blackbox-llm:8002",
            "tts": "http://blackbox-tts:8003"
        }
    
    async def call_service(
        self,
        service: str,
        method: str,
        data: Dict[str, Any],
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Call service via HTTP"""
        import aiohttp
        
        url = f"{self.service_urls[service]}/{method}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result
        
        except Exception as e:
            logger.error(f"HTTP IPC call failed ({service}.{method}): {e}")
            raise

