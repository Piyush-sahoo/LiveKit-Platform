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

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run gateway
CMD ["uvicorn", "services.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
