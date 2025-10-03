"""
BLACK BOX TTS Service - Health Check
"""

import sys
import os

try:
    # Check if IPC files exist
    shm_input = os.getenv("SHM_TTS_INPUT", "/dev/shm/blackbox_tts_in")
    shm_output = os.getenv("SHM_TTS_OUTPUT", "/dev/shm/blackbox_tts_out")
    
    if os.path.exists(shm_input) and os.path.exists(shm_output):
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)

