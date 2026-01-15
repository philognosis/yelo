"""
Agent State Management

Implements state space models for multi-agent systems with:
- State transitions and validation
- State history tracking
- Concurrent state access
- State persistence
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Set
from uuid import UUID, uuid4

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent operational states"""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMMUNICATING = "communicating"
    ERROR = "error"
    COMPLETED = "completed"
    SHUTDOWN = "shutdown"


class StateTransition(BaseModel):
    """Represents a state transition event"""

    from_state: AgentStatus
    to_state: AgentStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """
    Comprehensive agent state representation

    Implements state space model: S = (Status, Task, Memory, Context, Metrics)
    """

    agent_id: UUID
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    capabilities: Set[str] = Field(default_factory=set)
    workload: float = 0.0  # 0.0 to 1.0
    health: float = 1.0  # 0.0 to 1.0
    active_connections: Set[UUID] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Performance metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_task_duration: float = 0.0
    last_active: datetime = Field(default_factory=datetime.now)

    # State vector representation for mathematical operations
    def to_vector(self) -> np.ndarray:
        """
        Convert state to numerical vector for mathematical analysis

        Vector: [status_code, workload, health, task_completion_rate, recency]
        """
        status_code = list(AgentStatus).index(self.status)
        total_tasks = self.tasks_completed + self.tasks_failed
        completion_rate = self.tasks_completed / total_tasks if total_tasks > 0 else 1.0

        # Recency score (0-1, exponential decay)
        time_since_active = (datetime.now() - self.last_active).total_seconds()
        recency = np.exp(-time_since_active / 3600)  # 1-hour half-life

        return np.array(
            [status_code, self.workload, self.health, completion_rate, recency], dtype=np.float32
        )

    def distance_to(self, other: AgentState) -> float:
        """Calculate Euclidean distance between agent states"""
        return float(np.linalg.norm(self.to_vector() - other.to_vector()))

    class Config:
        arbitrary_types_allowed = True


class StateManager:
    """
    Manages agent state with history, transitions, and validation

    Features:
    - Thread-safe state updates
    - State transition validation
    - History tracking with configurable depth
    - State listeners/observers
    - Persistence support
    """

    def __init__(self, agent_id: UUID, max_history: int = 1000):
        self.agent_id = agent_id
        self.current_state = AgentState(agent_id=agent_id)
        self.max_history = max_history

        # State transition history
        self.transition_history: Deque[StateTransition] = deque(maxlen=max_history)

        # State change listeners
        self.listeners: List[Callable[[AgentState, StateTransition], None]] = []

        # Concurrency control
        self._lock = asyncio.Lock()

        # Valid state transitions (state machine)
        self._valid_transitions: Dict[AgentStatus, Set[AgentStatus]] = {
            AgentStatus.IDLE: {
                AgentStatus.PLANNING,
                AgentStatus.COMMUNICATING,
                AgentStatus.SHUTDOWN,
            },
            AgentStatus.PLANNING: {
                AgentStatus.EXECUTING,
                AgentStatus.WAITING,
                AgentStatus.ERROR,
                AgentStatus.IDLE,
            },
            AgentStatus.EXECUTING: {
                AgentStatus.COMPLETED,
                AgentStatus.ERROR,
                AgentStatus.WAITING,
                AgentStatus.COMMUNICATING,
            },
            AgentStatus.WAITING: {
                AgentStatus.EXECUTING,
                AgentStatus.ERROR,
                AgentStatus.IDLE,
            },
            AgentStatus.COMMUNICATING: {
                AgentStatus.IDLE,
                AgentStatus.EXECUTING,
                AgentStatus.ERROR,
            },
            AgentStatus.ERROR: {
                AgentStatus.IDLE,
                AgentStatus.SHUTDOWN,
            },
            AgentStatus.COMPLETED: {
                AgentStatus.IDLE,
                AgentStatus.SHUTDOWN,
            },
            AgentStatus.SHUTDOWN: set(),  # Terminal state
        }

    async def update_status(
        self,
        new_status: AgentStatus,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update agent status with validation and history tracking

        Returns:
            bool: True if transition was valid and completed
        """
        async with self._lock:
            current = self.current_state.status

            # Validate transition
            if new_status not in self._valid_transitions[current]:
                logger.warning(
                    f"Invalid state transition: {current} -> {new_status} for agent {self.agent_id}"
                )
                return False

            # Create transition record
            transition = StateTransition(
                from_state=current,
                to_state=new_status,
                reason=reason,
                metadata=metadata or {},
            )

            # Update state
            old_state = self.current_state.model_copy(deep=True)
            self.current_state.status = new_status
            self.current_state.last_active = datetime.now()

            # Record transition
            self.transition_history.append(transition)

            # Notify listeners
            for listener in self.listeners:
                try:
                    listener(self.current_state, transition)
                except Exception as e:
                    logger.error(f"State listener error: {e}")

            logger.info(
                f"Agent {self.agent_id}: {current} -> {new_status}"
                + (f" ({reason})" if reason else "")
            )

            return True

    async def update_workload(self, workload: float) -> None:
        """Update agent workload (0.0 to 1.0)"""
        async with self._lock:
            self.current_state.workload = max(0.0, min(1.0, workload))
            self.current_state.last_active = datetime.now()

    async def update_health(self, health: float) -> None:
        """Update agent health (0.0 to 1.0)"""
        async with self._lock:
            self.current_state.health = max(0.0, min(1.0, health))
            self.current_state.last_active = datetime.now()

    async def record_task_completion(self, success: bool, duration: float) -> None:
        """Record task completion metrics"""
        async with self._lock:
            if success:
                self.current_state.tasks_completed += 1
            else:
                self.current_state.tasks_failed += 1

            # Update average duration (running average)
            n = self.current_state.tasks_completed + self.current_state.tasks_failed
            current_avg = self.current_state.average_task_duration
            self.current_state.average_task_duration = (
                current_avg * (n - 1) + duration
            ) / n

            self.current_state.last_active = datetime.now()

    def add_listener(self, listener: Callable[[AgentState, StateTransition], None]) -> None:
        """Add state change listener"""
        self.listeners.append(listener)

    def get_state(self) -> AgentState:
        """Get current state (thread-safe copy)"""
        return self.current_state.model_copy(deep=True)

    def get_transition_history(self, limit: Optional[int] = None) -> List[StateTransition]:
        """Get state transition history"""
        history = list(self.transition_history)
        return history[-limit:] if limit else history

    def get_state_duration(self, status: AgentStatus) -> float:
        """Calculate total time spent in a specific state (seconds)"""
        total_duration = 0.0
        current_start = None

        for transition in self.transition_history:
            if transition.to_state == status:
                current_start = transition.timestamp
            elif current_start and transition.from_state == status:
                duration = (transition.timestamp - current_start).total_seconds()
                total_duration += duration
                current_start = None

        # If currently in the status, add ongoing duration
        if self.current_state.status == status and current_start:
            total_duration += (datetime.now() - current_start).total_seconds()

        return total_duration

    def get_success_rate(self) -> float:
        """Calculate task success rate"""
        total = self.current_state.tasks_completed + self.current_state.tasks_failed
        return self.current_state.tasks_completed / total if total > 0 else 1.0
