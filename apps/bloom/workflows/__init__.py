"""
Workflow Orchestration

Provides workflow orchestration components for Bloom:
- State machine for evaluation workflow
- Phase handlers for each evaluation phase
- Transition validation and execution
- Agent triggering on state changes

All workflow components integrate with:
- IRAS communication protocols
- Bloom integrations (Slack, Email, etc.)
- Deadline and notification management
"""

from bloom.workflows.phase_handlers import (
    CalibrationHandler,
    ContextPeerSelectionHandler,
    DataGatheringHandler,
    ManagerEvaluationHandler,
    PhaseHandler,
    ReleaseDiscussionHandler,
)
from bloom.workflows.state_machine import EvaluationStateMachine, TransitionResult

__all__ = [
    "EvaluationStateMachine",
    "TransitionResult",
    "PhaseHandler",
    "ContextPeerSelectionHandler",
    "DataGatheringHandler",
    "ManagerEvaluationHandler",
    "CalibrationHandler",
    "ReleaseDiscussionHandler",
]
