"""Test Suite for Task Allocation Algorithms"""

import pytest
import asyncio
import numpy as np
from uuid import uuid4

from iras.math.task_allocation import (
    TaskAllocator,
    AllocationStrategy,
    TaskAllocation,
    AgentCapability,
)


class TestTaskAllocation:
    """Test task allocation algorithms"""

    @pytest.mark.asyncio
    async def test_greedy_allocation(self):
        allocator = TaskAllocator(strategy=AllocationStrategy.GREEDY)

        agents = [
            {"id": uuid4(), "capacity": 1.0, "capabilities": {"A", "B"}},
            {"id": uuid4(), "capacity": 0.5, "capabilities": {"A"}},
        ]

        tasks = [
            {"id": uuid4(), "requirements": {"A"}, "workload": 0.3},
            {"id": uuid4(), "requirements": {"B"}, "workload": 0.4},
        ]

        allocation = await allocator.allocate(agents, tasks)
        assert len(allocation.assignments) > 0

    @pytest.mark.asyncio
    async def test_load_balanced_allocation(self):
        allocator = TaskAllocator(strategy=AllocationStrategy.LOAD_BALANCED)

        agents = [
            {"id": uuid4(), "capacity": 1.0, "capabilities": {"A"}},
            {"id": uuid4(), "capacity": 1.0, "capabilities": {"A"}},
        ]

        tasks = [
            {"id": uuid4(), "requirements": {"A"}, "workload": 0.5},
            {"id": uuid4(), "requirements": {"A"}, "workload": 0.5},
        ]

        allocation = await allocator.allocate(agents, tasks)
        # Should distribute evenly
        assert len(allocation.assignments) == 2

    @pytest.mark.asyncio
    async def test_capability_matching(self):
        allocator = TaskAllocator(strategy=AllocationStrategy.GREEDY)

        agents = [
            {"id": uuid4(), "capacity": 1.0, "capabilities": {"X"}},
            {"id": uuid4(), "capacity": 1.0, "capabilities": {"Y"}},
        ]

        task = {"id": uuid4(), "requirements": {"Y"}, "workload": 0.3}

        allocation = await allocator.allocate(agents, [task])

        # Should assign to agent with capability Y
        assert len(allocation.assignments) == 1

    @pytest.mark.asyncio
    async def test_unallocated_tasks(self):
        allocator = TaskAllocator(strategy=AllocationStrategy.GREEDY)

        agents = [
            {"id": uuid4(), "capacity": 0.1, "capabilities": {"A"}},
        ]

        tasks = [
            {"id": uuid4(), "requirements": {"A"}, "workload": 0.9},
        ]

        allocation = await allocator.allocate(agents, tasks)

        # May have unallocated tasks due to capacity
        assert allocation is not None


class TestLoadBalancing:
    """Test load balancing calculations"""

    def test_calculate_agent_load(self):
        from iras.math.load_balancing import calculate_load

        assignments = [0.3, 0.4, 0.2]
        total_load = calculate_load(assignments)

        assert total_load == pytest.approx(0.9)

    def test_load_variance(self):
        from iras.math.load_balancing import load_variance

        loads = [0.5, 0.5, 0.5]  # Perfectly balanced
        variance = load_variance(loads)

        assert variance == pytest.approx(0.0)


class TestEdgeCases:
    """Test edge cases in task allocation"""

    @pytest.mark.asyncio
    async def test_no_agents(self):
        allocator = TaskAllocator()

        tasks = [{"id": uuid4(), "requirements": set(), "workload": 0.5}]

        allocation = await allocator.allocate([], tasks)
        assert len(allocation.assignments) == 0

    @pytest.mark.asyncio
    async def test_no_tasks(self):
        allocator = TaskAllocator()

        agents = [{"id": uuid4(), "capacity": 1.0, "capabilities": set()}]

        allocation = await allocator.allocate(agents, [])
        assert len(allocation.assignments) == 0
