"""
Bloom Specialized Agents

A suite of specialized agents for the Bloom performance evaluation system.
Each agent extends the IRAS Agent class with domain-specific capabilities.

Agents:
- Watchkeeper: Orchestrates evaluation cycles and manages state transitions
- ContextMiner: Analyzes collaboration patterns and suggests peer reviewers
- Scribe: Synthesizes feedback and generates evaluation drafts
- Chaser: Enforces deadlines and sends notifications
- Gatekeeper: Manages RBAC and audit logging
- Analyst: Calculates metrics and generates insights
"""

from apps.bloom.agents.analyst import BloomAnalyst
from apps.bloom.agents.chaser import Chaser
from apps.bloom.agents.context_miner import ContextMiner
from apps.bloom.agents.gatekeeper import Gatekeeper
from apps.bloom.agents.scribe import Scribe
from apps.bloom.agents.watchkeeper import Watchkeeper

__all__ = [
    "Watchkeeper",
    "ContextMiner",
    "Scribe",
    "Chaser",
    "Gatekeeper",
    "BloomAnalyst",
]
