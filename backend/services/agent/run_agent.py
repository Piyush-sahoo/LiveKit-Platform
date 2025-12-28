#!/usr/bin/env python
"""Run the LiveKit agent worker."""
import sys
import os

# Add /app to path for container context
sys.path.insert(0, "/app")
# Add backend root for local dev
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from services.agent.worker import run_agent

if __name__ == "__main__":
    run_agent()
