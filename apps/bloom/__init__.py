"""
Bloom - Employee Evaluation & Growth Engine

A zero-UI, autonomous multi-agent system for performance evaluations.

Built on the IRAS (Intelligent Research & Analysis Swarm) framework.

Core Features:
- Autonomous evaluation workflow orchestration
- AI-assisted manager evaluations with RAG
- Context mining from multiple data sources
- Intelligent peer selection
- Real-time dashboard monitoring
- Slack/Email integration for notifications

Architecture:
- Multi-agent swarm with specialized agents
- Event-driven state machine
- Database-backed persistence
- RESTful API for dashboard
- Integration with enterprise systems (Slack, Jira, Git, Calendar)
"""

__version__ = "0.1.0"
__author__ = "Bloom Team"

from bloom.models.employee import Employee, Person
from bloom.models.evaluation import Evaluation, EvaluationState
from bloom.orchestrator import BloomOrchestrator

__all__ = [
    "Employee",
    "Person",
    "Evaluation",
    "EvaluationState",
    "BloomOrchestrator",
]
