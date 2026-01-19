# Bloom API Dockerfile
# Production-ready FastAPI backend for Bloom evaluation system

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

LABEL maintainer="Bloom Team"
LABEL description="Bloom Employee Evaluation & Growth Engine - API"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy IRAS framework (from repository root context)
COPY src/iras /app/iras
WORKDIR /app/iras
RUN uv pip install -e .

# Copy Bloom application
WORKDIR /app
COPY apps/bloom /app/bloom

# Install Bloom dependencies using uv
WORKDIR /app/bloom
RUN uv pip install -e .

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/iras /app/iras
COPY --from=builder /app/bloom /app/bloom

# Set working directory
WORKDIR /app/bloom

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
