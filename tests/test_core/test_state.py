"""
Test Suite for State Management

Tests cover:
- State initialization
- State transitions and validation
- State history tracking
- Concurrent state access
- State listeners/observers
- State metrics and calculations
- Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
import numpy as np

from iras.core.state import (
    AgentState,
    AgentStatus,
    StateManager,
    StateTransition,
)


class TestAgentState:
    """Test AgentState model and operations"""

    def test_agent_state_initialization(self):
        """Test basic state initialization"""
        agent_id = uuid4()
        state = AgentState(agent_id=agent_id)

        assert state.agent_id == agent_id
        assert state.status == AgentStatus.IDLE
        assert state.workload == 0.0
        assert state.health == 1.0
        assert len(state.capabilities) == 0
        assert state.tasks_completed == 0
        assert state.tasks_failed == 0

    def test_agent_state_with_capabilities(self):
        """Test state with custom capabilities"""
        agent_id = uuid4()
        capabilities = {"search", "analyze", "report"}
        state = AgentState(
            agent_id=agent_id,
            capabilities=capabilities,
        )

        assert len(state.capabilities) == 3
        assert "search" in state.capabilities

    def test_state_to_vector_conversion(self):
        """Test converting state to numerical vector"""
        agent_id = uuid4()
        state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.EXECUTING,
            workload=0.5,
            health=0.9,
            tasks_completed=10,
            tasks_failed=2,
        )

        vector = state.to_vector()

        assert isinstance(vector, np.ndarray)
        assert len(vector) == 5
        assert vector[1] == 0.5  # workload
        assert vector[2] == 0.9  # health

    def test_state_distance_calculation(self):
        """Test calculating distance between states"""
        agent_id = uuid4()

        state1 = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            workload=0.0,
            health=1.0,
        )

        state2 = AgentState(
            agent_id=agent_id,
            status=AgentStatus.EXECUTING,
            workload=0.8,
            health=0.9,
        )

        distance = state1.distance_to(state2)

        assert isinstance(distance, float)
        assert distance > 0.0

    def test_state_vector_dimensions(self):
        """Test vector has correct dimensions"""
        state = AgentState(agent_id=uuid4())
        vector = state.to_vector()

        # Vector should be: [status_code, workload, health, completion_rate, recency]
        assert vector.shape == (5,)
        assert all(0 <= v <= 10 for v in vector)  # Reasonable bounds


class TestStateTransitions:
    """Test state transition validation and logic"""

    @pytest.mark.asyncio
    async def test_valid_state_transition_idle_to_planning(self):
        """Test valid transition from IDLE to PLANNING"""
        manager = StateManager(agent_id=uuid4())

        success = await manager.update_status(
            AgentStatus.PLANNING,
            reason="Starting planning",
        )

        assert success is True
        assert manager.current_state.status == AgentStatus.PLANNING

    @pytest.mark.asyncio
    async def test_valid_state_transition_planning_to_executing(self):
        """Test valid transition from PLANNING to EXECUTING"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.PLANNING)
        success = await manager.update_status(AgentStatus.EXECUTING)

        assert success is True
        assert manager.current_state.status == AgentStatus.EXECUTING

    @pytest.mark.asyncio
    async def test_invalid_state_transition(self):
        """Test that invalid transitions are rejected"""
        manager = StateManager(agent_id=uuid4())

        # IDLE -> EXECUTING is not valid (must go through PLANNING)
        success = await manager.update_status(AgentStatus.EXECUTING)

        assert success is False
        assert manager.current_state.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_terminal_state_shutdown(self):
        """Test that SHUTDOWN is a terminal state"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.IDLE)
        await manager.update_status(AgentStatus.SHUTDOWN)

        # No transitions allowed from SHUTDOWN
        success = await manager.update_status(AgentStatus.IDLE)

        assert success is False
        assert manager.current_state.status == AgentStatus.SHUTDOWN

    @pytest.mark.asyncio
    async def test_error_state_recovery(self):
        """Test recovery from ERROR state"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.PLANNING)
        await manager.update_status(AgentStatus.ERROR)

        # Can recover from ERROR to IDLE
        success = await manager.update_status(AgentStatus.IDLE)

        assert success is True
        assert manager.current_state.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_transition_with_metadata(self):
        """Test transitions with metadata"""
        manager = StateManager(agent_id=uuid4())

        metadata = {"task_id": "123", "reason": "test"}
        await manager.update_status(
            AgentStatus.PLANNING,
            reason="Test transition",
            metadata=metadata,
        )

        history = manager.get_transition_history(limit=1)
        assert len(history) == 1
        assert history[0].metadata == metadata


class TestStateHistory:
    """Test state history tracking"""

    @pytest.mark.asyncio
    async def test_transition_history_tracking(self):
        """Test that state transitions are tracked"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.PLANNING)
        await manager.update_status(AgentStatus.EXECUTING)
        await manager.update_status(AgentStatus.COMPLETED)
        await manager.update_status(AgentStatus.IDLE)

        history = manager.get_transition_history()

        assert len(history) == 4
        assert history[0].from_state == AgentStatus.IDLE
        assert history[0].to_state == AgentStatus.PLANNING

    @pytest.mark.asyncio
    async def test_history_limit(self):
        """Test history size limit"""
        manager = StateManager(agent_id=uuid4(), max_history=5)

        # Create more transitions than the limit
        for _ in range(10):
            await manager.update_status(AgentStatus.PLANNING)
            await manager.update_status(AgentStatus.IDLE)

        history = manager.get_transition_history()

        assert len(history) <= 5

    @pytest.mark.asyncio
    async def test_get_limited_history(self):
        """Test retrieving limited history"""
        manager = StateManager(agent_id=uuid4())

        # Create some transitions
        await manager.update_status(AgentStatus.PLANNING)
        await manager.update_status(AgentStatus.EXECUTING)
        await manager.update_status(AgentStatus.COMPLETED)

        recent_history = manager.get_transition_history(limit=2)

        assert len(recent_history) == 2
        # Should be the most recent 2
        assert recent_history[-1].to_state == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_transition_timestamps(self):
        """Test that transitions have timestamps"""
        manager = StateManager(agent_id=uuid4())

        before = datetime.now()
        await manager.update_status(AgentStatus.PLANNING)
        after = datetime.now()

        history = manager.get_transition_history(limit=1)

        assert len(history) == 1
        assert before <= history[0].timestamp <= after


class TestConcurrentStateAccess:
    """Test concurrent state access and thread safety"""

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self):
        """Test multiple concurrent state updates"""
        manager = StateManager(agent_id=uuid4())

        async def update_workload(value):
            await manager.update_workload(value)
            await asyncio.sleep(0.01)

        # Concurrent updates
        await asyncio.gather(
            update_workload(0.1),
            update_workload(0.5),
            update_workload(0.9),
        )

        # Final state should be one of the values
        assert 0.0 <= manager.current_state.workload <= 1.0

    @pytest.mark.asyncio
    async def test_concurrent_task_completions(self):
        """Test concurrent task completion recording"""
        manager = StateManager(agent_id=uuid4())

        async def record_completion(success):
            await manager.record_task_completion(success, duration=1.0)

        # Record multiple completions concurrently
        await asyncio.gather(
            record_completion(True),
            record_completion(True),
            record_completion(False),
        )

        assert manager.current_state.tasks_completed == 2
        assert manager.current_state.tasks_failed == 1

    @pytest.mark.asyncio
    async def test_get_state_returns_copy(self):
        """Test that get_state returns a copy, not reference"""
        manager = StateManager(agent_id=uuid4())

        state1 = manager.get_state()
        state1.workload = 0.99  # Modify the copy

        state2 = manager.get_state()

        # Original should be unchanged
        assert state2.workload == 0.0


class TestStateListeners:
    """Test state change listeners/observers"""

    @pytest.mark.asyncio
    async def test_listener_called_on_state_change(self):
        """Test that listeners are notified of state changes"""
        manager = StateManager(agent_id=uuid4())

        called = []

        def listener(state, transition):
            called.append((state.status, transition.to_state))

        manager.add_listener(listener)

        await manager.update_status(AgentStatus.PLANNING)

        assert len(called) == 1
        assert called[0][1] == AgentStatus.PLANNING

    @pytest.mark.asyncio
    async def test_multiple_listeners(self):
        """Test multiple listeners"""
        manager = StateManager(agent_id=uuid4())

        calls1 = []
        calls2 = []

        def listener1(state, transition):
            calls1.append(transition.to_state)

        def listener2(state, transition):
            calls2.append(transition.to_state)

        manager.add_listener(listener1)
        manager.add_listener(listener2)

        await manager.update_status(AgentStatus.PLANNING)

        assert len(calls1) == 1
        assert len(calls2) == 1

    @pytest.mark.asyncio
    async def test_listener_error_handling(self):
        """Test that listener errors don't break state updates"""
        manager = StateManager(agent_id=uuid4())

        def bad_listener(state, transition):
            raise ValueError("Listener error")

        manager.add_listener(bad_listener)

        # Should still succeed despite listener error
        success = await manager.update_status(AgentStatus.PLANNING)

        assert success is True
        assert manager.current_state.status == AgentStatus.PLANNING


class TestStateMetrics:
    """Test state metrics and calculations"""

    @pytest.mark.asyncio
    async def test_workload_update(self):
        """Test workload updates"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_workload(0.7)

        assert manager.current_state.workload == 0.7

    @pytest.mark.asyncio
    async def test_workload_bounds(self):
        """Test that workload is bounded [0, 1]"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_workload(1.5)
        assert manager.current_state.workload == 1.0

        await manager.update_workload(-0.5)
        assert manager.current_state.workload == 0.0

    @pytest.mark.asyncio
    async def test_health_update(self):
        """Test health updates"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_health(0.8)

        assert manager.current_state.health == 0.8

    @pytest.mark.asyncio
    async def test_health_bounds(self):
        """Test that health is bounded [0, 1]"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_health(2.0)
        assert manager.current_state.health == 1.0

        await manager.update_health(-1.0)
        assert manager.current_state.health == 0.0

    @pytest.mark.asyncio
    async def test_task_completion_tracking(self):
        """Test task completion metrics"""
        manager = StateManager(agent_id=uuid4())

        await manager.record_task_completion(success=True, duration=10.0)
        await manager.record_task_completion(success=True, duration=20.0)
        await manager.record_task_completion(success=False, duration=5.0)

        assert manager.current_state.tasks_completed == 2
        assert manager.current_state.tasks_failed == 1
        assert manager.current_state.average_task_duration > 0

    @pytest.mark.asyncio
    async def test_average_duration_calculation(self):
        """Test running average duration calculation"""
        manager = StateManager(agent_id=uuid4())

        await manager.record_task_completion(success=True, duration=10.0)
        await manager.record_task_completion(success=True, duration=20.0)
        await manager.record_task_completion(success=True, duration=30.0)

        # Average should be 20.0
        assert abs(manager.current_state.average_task_duration - 20.0) < 0.01

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        manager = StateManager(agent_id=uuid4())
        manager.current_state.tasks_completed = 7
        manager.current_state.tasks_failed = 3

        success_rate = manager.get_success_rate()

        assert success_rate == 0.7

    def test_success_rate_no_tasks(self):
        """Test success rate with no completed tasks"""
        manager = StateManager(agent_id=uuid4())

        success_rate = manager.get_success_rate()

        assert success_rate == 1.0  # Default to perfect when no data


class TestStateDuration:
    """Test state duration calculations"""

    @pytest.mark.asyncio
    async def test_state_duration_calculation(self):
        """Test calculating time spent in a state"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.PLANNING)
        await asyncio.sleep(0.1)
        await manager.update_status(AgentStatus.EXECUTING)
        await asyncio.sleep(0.1)
        await manager.update_status(AgentStatus.IDLE)

        # Get duration in PLANNING state
        duration = manager.get_state_duration(AgentStatus.PLANNING)

        assert duration >= 0.1
        assert duration < 0.2  # Should not include EXECUTING time

    @pytest.mark.asyncio
    async def test_current_state_duration(self):
        """Test duration includes current state if still in it"""
        manager = StateManager(agent_id=uuid4())

        await manager.update_status(AgentStatus.PLANNING)
        await asyncio.sleep(0.1)

        duration = manager.get_state_duration(AgentStatus.PLANNING)

        assert duration >= 0.1

    @pytest.mark.asyncio
    async def test_multiple_visits_to_state(self):
        """Test duration calculation with multiple visits"""
        manager = StateManager(agent_id=uuid4())

        # First visit
        await manager.update_status(AgentStatus.PLANNING)
        await asyncio.sleep(0.05)
        await manager.update_status(AgentStatus.IDLE)

        # Second visit
        await manager.update_status(AgentStatus.PLANNING)
        await asyncio.sleep(0.05)
        await manager.update_status(AgentStatus.IDLE)

        duration = manager.get_state_duration(AgentStatus.PLANNING)

        assert duration >= 0.1  # Sum of both visits


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_state_with_empty_capabilities(self):
        """Test state with no capabilities"""
        state = AgentState(
            agent_id=uuid4(),
            capabilities=set(),
        )

        assert len(state.capabilities) == 0

    def test_state_vector_with_zero_tasks(self):
        """Test vector calculation with zero completed tasks"""
        state = AgentState(
            agent_id=uuid4(),
            tasks_completed=0,
            tasks_failed=0,
        )

        vector = state.to_vector()

        assert isinstance(vector, np.ndarray)
        # Completion rate should default to 1.0
        assert vector[3] == 1.0

    @pytest.mark.asyncio
    async def test_update_status_with_none_reason(self):
        """Test status update with None reason"""
        manager = StateManager(agent_id=uuid4())

        success = await manager.update_status(
            AgentStatus.PLANNING,
            reason=None,
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_update_status_with_none_metadata(self):
        """Test status update with None metadata"""
        manager = StateManager(agent_id=uuid4())

        success = await manager.update_status(
            AgentStatus.PLANNING,
            metadata=None,
        )

        assert success is True
        history = manager.get_transition_history(limit=1)
        assert history[0].metadata == {}

    def test_state_distance_same_state(self):
        """Test distance between identical states"""
        agent_id = uuid4()
        state1 = AgentState(agent_id=agent_id)
        state2 = AgentState(agent_id=agent_id)

        distance = state1.distance_to(state2)

        assert distance == 0.0

    @pytest.mark.asyncio
    async def test_last_active_updates(self):
        """Test that last_active timestamp updates"""
        manager = StateManager(agent_id=uuid4())

        before = datetime.now()
        await manager.update_status(AgentStatus.PLANNING)
        after = datetime.now()

        assert before <= manager.current_state.last_active <= after

    @pytest.mark.asyncio
    async def test_transition_history_empty_initially(self):
        """Test that history is empty initially"""
        manager = StateManager(agent_id=uuid4())

        history = manager.get_transition_history()

        assert len(history) == 0
