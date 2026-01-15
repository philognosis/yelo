"""
IRAS Test Suite

Comprehensive test suite for the Intelligent Research & Analysis Swarm (IRAS) system.

Test Structure:
- test_core/: Core agent functionality tests
- test_databases/: Database system tests
- test_communication/: Communication protocol tests
- test_math/: Mathematical algorithms tests
- test_agents/: Specialized agent tests
- integration/: Integration and end-to-end tests

Usage:
    # Run all tests
    pytest

    # Run specific module
    pytest tests/test_core/

    # Run with coverage
    pytest --cov=iras --cov-report=html

    # Run only fast tests
    pytest -m "not slow"

    # Run integration tests
    pytest -m integration

    # Run async tests
    pytest -m asyncio
"""

__version__ = "1.0.0"
__author__ = "IRAS Development Team"
