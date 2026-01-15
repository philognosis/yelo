# Bloom API Dockerfile
# Production-ready FastAPI backend for Bloom evaluation system

FROM python:3.11-slim

LABEL maintainer="Bloom Team"
LABEL description="Bloom Employee Evaluation & Growth Engine - API"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy IRAS core dependency
COPY ../../src/iras /app/iras

# Copy Bloom application
COPY . /app/bloom

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Bloom as package
WORKDIR /app/bloom
RUN pip install -e .

# Create non-root user for security
RUN useradd -m -u 1000 bloom && \
    chown -R bloom:bloom /app

USER bloom

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "bloom.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
