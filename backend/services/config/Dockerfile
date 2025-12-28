FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install uv
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Copy shared modules
COPY shared ./shared

# Copy for backwards compatibility (old imports like 'from database.models')
COPY shared/database ./database
COPY shared/auth ./auth

# Copy all services (needed for imports)
COPY services ./services

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run config service
CMD ["uvicorn", "services.config.main:app", "--host", "0.0.0.0", "--port", "8002"]
