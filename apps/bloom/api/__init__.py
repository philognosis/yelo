"""
Bloom Dashboard API

FastAPI-based REST API for the Bloom evaluation system.
Provides endpoints for managing evaluations, submitting feedback,
and monitoring the agent swarm.
"""

from bloom.api.main import app

__all__ = ["app"]
