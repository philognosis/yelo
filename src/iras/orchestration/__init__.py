"""
Orchestration Layer for IRAS Multi-Agent System

This module provides high-level orchestration capabilities for coordinating
swarms of specialized agents to perform complex research and analysis tasks.

Key Components:
- Coordinator: Main orchestration class that manages agent swarms
- Workflow management for multi-step research pipelines
- Task distribution using mathematical foundations
- Multi-database integration for comprehensive data storage
- Autonomous operation with monitoring and recovery

Example Usage:
    >>> from iras.orchestration import Coordinator
    >>>
    >>> coordinator = Coordinator()
    >>> await coordinator.initialize()
    >>>
    >>> # Simple research task
    >>> results = await coordinator.research("quantum computing")
    >>>
    >>> # Complex multi-agent workflow
    >>> results = await coordinator.comprehensive_research(
    ...     topics=["AI", "blockchain"],
    ...     depth=3,
    ...     enable_fact_checking=True
    ... )
"""

from iras.orchestration.coordinator import Coordinator, WorkflowConfig

__all__ = [
    "Coordinator",
    "WorkflowConfig",
]
