"""
BLACK BOX Orchestrator - Health Check Script
Quick health check for Docker container
"""

import sys
import requests

try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") in ["healthy", "degraded"]:
            sys.exit(0)
    sys.exit(1)
except Exception:
    sys.exit(1)

