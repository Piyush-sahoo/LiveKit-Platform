#!/usr/bin/env python
"""Run the API Gateway server."""
import uvicorn
import os
import sys

# Add /app to path for container context
sys.path.insert(0, "/app")

# For local dev, add parent dirs
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.settings import config

if __name__ == "__main__":
    uvicorn.run(
        "services.gateway.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
    )
