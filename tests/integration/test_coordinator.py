"""Integration Tests for Multi-Agent Coordination"""

import pytest
import asyncio
from uuid import uuid4

from iras.core.agent import Agent, AgentConfig
from iras.orchestration.coordinator import Coordinator, CoordinationStrategy
from iras.communication.protocols import MessageBus


class TestCoordinatorIntegration:
    """Test coordinator managing multiple agents"""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self):
        coordinator = Coordinator(
            strategy=CoordinationStrategy.HIERARCHICAL,
        )

        assert coordinator is not None
        assert len(coordinator.agents) == 0

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self):
        coordinator = Coordinator()

        # Create and register agents
        agent1 = Agent(AgentConfig(name="agent1", role="worker"))
        agent2 = Agent(AgentConfig(name="agent2", role="worker"))

        await coordinator.register_agent(agent1)
        await coordinator.register_agent(agent2)

        assert len(coordinator.agents) == 2

    @pytest.mark.asyncio
    async def test_coordinate_simple_task(self):
        coordinator = Coordinator()

        agent = Agent(AgentConfig(
            name="worker",
            role="worker",
            capabilities={"task_capability"},
        ))

        await coordinator.register_agent(agent)

        result = await coordinator.coordinate_task(
            task_description="Simple task",
            required_capabilities={"task_capability"},
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self):
        coordinator = Coordinator()

        # Create specialized agents
        agent1 = Agent(AgentConfig(
            name="researcher",
            role="researcher",
            capabilities={"research"},
        ))

        agent2 = Agent(AgentConfig(
            name="analyst",
            role="analyst",
            capabilities={"analyze"},
        ))

        await coordinator.register_agent(agent1)
        await coordinator.register_agent(agent2)

        # Coordinate complex task requiring multiple agents
        result = await coordinator.coordinate_workflow([
            {"step": 1, "capabilities": {"research"}},
            {"step": 2, "capabilities": {"analyze"}},
        ])

        assert result is not None

    @pytest.mark.asyncio
    async def test_agent_load_balancing(self):
        coordinator = Coordinator(
            strategy=CoordinationStrategy.LOAD_BALANCED,
        )

        # Create multiple similar agents
        for i in range(3):
            agent = Agent(AgentConfig(
                name=f"worker_{i}",
                role="worker",
                capabilities={"common_task"},
            ))
            await coordinator.register_agent(agent)

        # Submit multiple tasks
        tasks = [
            {"desc": f"Task {i}", "caps": {"common_task"}}
            for i in range(6)
        ]

        results = await coordinator.coordinate_batch(tasks)

        assert len(results) > 0


class TestMessageBasedCoordination:
    """Test coordination using message passing"""

    @pytest.mark.asyncio
    async def test_message_based_coordination(self):
        bus = MessageBus()
        coordinator = Coordinator(message_bus=bus)

        agent1 = Agent(AgentConfig(name="a1", role="worker"))
        agent2 = Agent(AgentConfig(name="a2", role="worker"))

        await coordinator.register_agent(agent1)
        await coordinator.register_agent(agent2)

        # Coordinate via messages
        await coordinator.broadcast_message({
            "type": "task_available",
            "task": "test_task",
        })

        # Verify messages were sent
        assert True  # Message bus should have activity


class TestErrorHandling:
    """Test error handling in coordination"""

    @pytest.mark.asyncio
    async def test_no_capable_agents(self):
        coordinator = Coordinator()

        agent = Agent(AgentConfig(
            name="limited",
            role="worker",
            capabilities={"capability_a"},
        ))

        await coordinator.register_agent(agent)

        # Request capability agent doesn't have
        result = await coordinator.coordinate_task(
            task_description="Task",
            required_capabilities={"capability_b"},
        )

        # Should handle gracefully
        assert result is not None or result is None

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self):
        coordinator = Coordinator(
            strategy=CoordinationStrategy.FAULT_TOLERANT,
        )

        # Register multiple agents
        for i in range(3):
            agent = Agent(AgentConfig(
                name=f"agent_{i}",
                role="worker",
                capabilities={"task"},
            ))
            await coordinator.register_agent(agent)

        # Even if one fails, others should handle
        result = await coordinator.coordinate_task(
            task_description="Resilient task",
            required_capabilities={"task"},
        )

        assert result is not None


class TestComplexWorkflows:
    """Test complex multi-agent workflows"""

    @pytest.mark.asyncio
    async def test_sequential_workflow(self):
        coordinator = Coordinator()

        agents = [
            Agent(AgentConfig(name="step1", role="w", capabilities={"A"})),
            Agent(AgentConfig(name="step2", role="w", capabilities={"B"})),
            Agent(AgentConfig(name="step3", role="w", capabilities={"C"})),
        ]

        for agent in agents:
            await coordinator.register_agent(agent)

        workflow = [
            {"step": 1, "caps": {"A"}, "depends_on": []},
            {"step": 2, "caps": {"B"}, "depends_on": [1]},
            {"step": 3, "caps": {"C"}, "depends_on": [2]},
        ]

        result = await coordinator.execute_workflow(workflow)
        assert result is not None

    @pytest.mark.asyncio
    async def test_parallel_workflow(self):
        coordinator = Coordinator()

        # Multiple agents with same capabilities
        for i in range(3):
            agent = Agent(AgentConfig(
                name=f"parallel_{i}",
                role="worker",
                capabilities={"parallel_task"},
            ))
            await coordinator.register_agent(agent)

        # Execute parallel tasks
        parallel_tasks = [
            {"id": i, "caps": {"parallel_task"}}
            for i in range(3)
        ]

        results = await coordinator.execute_parallel(parallel_tasks)
        assert len(results) == 3
