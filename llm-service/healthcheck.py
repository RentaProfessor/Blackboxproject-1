"""
BLACK BOX LLM Service - Health Check
"""

import sys
import os
import json

try:
    # Check if IPC files exist
    shm_input = os.getenv("SHM_LLM_INPUT", "/dev/shm/blackbox_llm_in")
    shm_output = os.getenv("SHM_LLM_OUTPUT", "/dev/shm/blackbox_llm_out")
    
    if os.path.exists(shm_input) and os.path.exists(shm_output):
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)

