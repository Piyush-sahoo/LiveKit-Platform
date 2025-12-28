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

# Copy for backwards compatibility
COPY shared/database ./database
COPY shared/auth ./auth

# Copy all services
COPY services ./services

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run orchestration service
CMD ["uvicorn", "services.orchestration.main:app", "--host", "0.0.0.0", "--port", "8003"]
