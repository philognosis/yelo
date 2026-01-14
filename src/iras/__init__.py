"""
IRAS - Intelligent Research & Analysis Swarm

A production-ready multi-agent AI system demonstrating:
- Multi-layer architecture (Infrastructure → Application)
- Advanced agent anatomy (reasoning, planning, memory)
- Communication protocols (Contract Net, Blackboard, Pub/Sub)
- Multi-database integration (Vector, Graph, Time-Series, Document)
- Mathematical foundations (task allocation, consensus, load balancing)
- Context optimization (pruning, compression, validation)
- Autonomous operation (self-monitoring, error recovery, adaptive learning)
"""

__version__ = "0.1.0"
__author__ = "IRAS Team"

from iras.core.agent import Agent, AgentConfig
from iras.core.state import AgentState, StateManager
from iras.orchestration.coordinator import Coordinator

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentState",
    "StateManager",
    "Coordinator",
]
