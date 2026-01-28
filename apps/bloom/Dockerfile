# Bloom API Dockerfile
# Production-ready FastAPI backend for Bloom evaluation system
# Optimized for fast rebuilds with layer caching and uv sync

# syntax=docker/dockerfile:1.4
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

LABEL maintainer="Bloom Team"
LABEL description="Bloom Employee Evaluation & Growth Engine - API"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# LAYER 1: Install IRAS framework dependencies
# ============================================================================
WORKDIR /app/iras

# Copy only dependency files first for better caching
COPY src/iras/pyproject.toml ./
RUN touch README.md

# Install IRAS dependencies using uv sync for faster builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e .

# ============================================================================
# LAYER 2: Install Bloom dependencies
# ============================================================================
WORKDIR /app/bloom

# Copy Bloom dependency files
COPY apps/bloom/pyproject.toml ./

# Generate or copy lock file if it exists
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f "uv.lock" ]; then \
        uv sync --frozen --no-dev; \
    else \
        uv pip install -e .; \
    fi

# ============================================================================
# LAYER 3: Copy application code (changes frequently, so done last)
# ============================================================================
# Copy IRAS source code
COPY src/iras /app/iras

# Copy Bloom application code
COPY apps/bloom /app/bloom

# ============================================================================
# Production stage - minimal, security-hardened
# ============================================================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/bloom/.local/bin:$PATH"

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user early (before copying files)
RUN useradd -m -u 1000 bloom

# Set working directory
WORKDIR /app/bloom

# Copy installed packages from builder (as root, then chown once)
COPY --from=builder --chown=bloom:bloom /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=bloom:bloom /usr/local/bin /usr/local/bin

# Copy application code (already owned by bloom user)
COPY --from=builder --chown=bloom:bloom /app/iras /app/iras
COPY --from=builder --chown=bloom:bloom /app/bloom /app/bloom

# Switch to non-root user
USER bloom

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "bloom.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
