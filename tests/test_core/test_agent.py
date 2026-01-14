"""
Test Suite for Core Agent Functionality

Tests cover:
- Agent initialization and configuration
- Task execution (simple, semi-complex, complex)
- Tool registration and usage
- State management integration
- Memory integration
- Reasoning integration
- Plan execution
- Error handling and recovery
- Lifecycle management
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.planning import Task, TaskPriority, TaskRequirements, Plan
from iras.core.state import AgentStatus
from iras.core.reasoning import ReasoningStrategy


class TestAgentInitialization:
    """Test agent initialization and configuration"""

    def test_agent_basic_initialization(self):
        """Test basic agent creation with minimal config"""
        config = AgentConfig(
            name="test_agent",
            role="researcher",
        )
        agent = Agent(config)

        assert agent.config.name == "test_agent"
        assert agent.config.role == "researcher"
        assert agent.id is not None
        assert agent.total_tasks_completed == 0
        assert agent.total_tasks_failed == 0

    def test_agent_with_custom_capabilities(self):
        """Test agent initialization with custom capabilities"""
        config = AgentConfig(
            name="specialized_agent",
            role="analyst",
            capabilities={"search", "analyze", "report"},
        )
        agent = Agent(config)

        assert "search" in agent.config.capabilities
        assert "analyze" in agent.config.capabilities
        assert len(agent.config.capabilities) == 3

    def test_agent_default_configuration(self):
        """Test default configuration values"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)

        assert agent.config.model == "claude-sonnet-4"
        assert agent.config.temperature == 0.7
        assert agent.config.max_tokens == 4000
        assert agent.config.autonomous_mode is True

    @pytest.mark.asyncio
    async def test_agent_initialization_async(self):
        """Test async initialization method"""
        config = AgentConfig(name="async_agent", role="worker")
        agent = Agent(config)

        await agent.initialize()

        state = agent.get_state()
        assert state.status == AgentStatus.IDLE
        assert state.agent_id == agent.id


class TestToolManagement:
    """Test tool registration and management"""

    def test_register_basic_tool(self):
        """Test registering a simple tool"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)

        def search_tool(query: str) -> str:
            return f"Results for: {query}"

        tool = AgentTool(
            name="search",
            description="Search for information",
            function=search_tool,
        )

        agent.register_tool(tool)

        assert "search" in agent.tools
        assert "search" in agent.config.capabilities

    def test_register_multiple_tools(self):
        """Test registering multiple tools"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)

        tools = [
            AgentTool(name="tool1", description="Tool 1"),
            AgentTool(name="tool2", description="Tool 2"),
            AgentTool(name="tool3", description="Tool 3"),
        ]

        for tool in tools:
            agent.register_tool(tool)

        assert len(agent.tools) == 3
        assert "tool1" in agent.config.capabilities
        assert "tool2" in agent.config.capabilities


class TestTaskExecution:
    """Test task execution scenarios"""

    @pytest.mark.asyncio
    async def test_simple_task_execution(self):
        """Test executing a simple task"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        task = Task(
            name="simple_task",
            description="A simple test task",
            is_primitive=True,
        )

        result = await agent.execute_task(task)

        assert result is not None
        assert result["task_name"] == "simple_task"
        assert result["status"] == "completed"
        assert agent.total_tasks_completed == 1
        assert agent.total_tasks_failed == 0

    @pytest.mark.asyncio
    async def test_semi_complex_task_with_dependencies(self):
        """Test task with requirements and dependencies"""
        config = AgentConfig(
            name="agent",
            role="worker",
            capabilities={"capability_a", "capability_b"},
        )
        agent = Agent(config)
        await agent.initialize()

        requirements = TaskRequirements(
            required_capabilities={"capability_a", "capability_b"},
            estimated_duration=30.0,
            estimated_tokens=500,
        )

        task = Task(
            name="semi_complex_task",
            description="Task with specific requirements",
            requirements=requirements,
            priority=TaskPriority.HIGH,
        )

        result = await agent.execute_task(task)

        assert result is not None
        assert agent.total_tasks_completed == 1

    @pytest.mark.asyncio
    async def test_complex_concurrent_tasks(self):
        """Test executing multiple tasks concurrently"""
        config = AgentConfig(
            name="agent",
            role="worker",
            max_concurrent_tasks=3,
        )
        agent = Agent(config)
        await agent.initialize()

        tasks = [
            Task(name=f"task_{i}", description=f"Test task {i}")
            for i in range(3)
        ]

        results = await asyncio.gather(
            *[agent.execute_task(task) for task in tasks]
        )

        assert len(results) == 3
        assert agent.total_tasks_completed == 3
        assert all(r["status"] == "completed" for r in results)

    @pytest.mark.asyncio
    async def test_task_execution_updates_state(self):
        """Test that task execution properly updates agent state"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        task = Task(name="state_test", description="Test state updates")

        # State should be IDLE before task
        assert agent.get_state().status == AgentStatus.IDLE

        result = await agent.execute_task(task)

        # State should be IDLE after task completion
        assert agent.get_state().status == AgentStatus.IDLE
        assert agent.get_state().tasks_completed == 1

    @pytest.mark.asyncio
    async def test_task_execution_stores_memory(self):
        """Test that task execution stores memories"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        task = Task(name="memory_test", description="Test memory storage")
        await agent.execute_task(task)

        # Check that memory was stored
        stats = agent.memory.get_memory_stats()
        assert stats["total_memories"] > 0


class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_task_failure_missing_capabilities(self):
        """Test task fails when required capabilities are missing"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        requirements = TaskRequirements(
            required_capabilities={"missing_capability"}
        )
        task = Task(
            name="failing_task",
            description="Task with missing capabilities",
            requirements=requirements,
        )

        with pytest.raises(ValueError, match="Missing required capabilities"):
            await agent.execute_task(task)

        assert agent.total_tasks_failed == 1
        assert agent.get_state().status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_task_failure_updates_state(self):
        """Test that task failures are tracked in state"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        requirements = TaskRequirements(
            required_capabilities={"nonexistent"}
        )
        task = Task(
            name="fail_task",
            description="Failing task",
            requirements=requirements,
        )

        try:
            await agent.execute_task(task)
        except ValueError:
            pass

        assert agent.total_tasks_failed == 1
        state = agent.get_state()
        assert state.tasks_failed == 1


class TestPlanExecution:
    """Test plan execution capabilities"""

    @pytest.mark.asyncio
    async def test_execute_simple_plan(self):
        """Test executing a simple plan"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Create a simple plan
        root_task = Task(
            name="root",
            description="Root task",
            is_primitive=True,
        )
        plan = Plan(
            goal="Test goal",
            root_task=root_task.id,
            tasks={root_task.id: root_task},
        )

        result = await agent.execute_plan(plan)

        assert result["status"] == "completed"
        assert result["completed_tasks"] == 1
        assert result["failed_tasks"] == 0
        assert result["progress"] == 1.0

    @pytest.mark.asyncio
    async def test_execute_plan_with_multiple_tasks(self):
        """Test executing a plan with multiple sequential tasks"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Create tasks with dependencies
        task1 = Task(name="task1", description="First task")
        task2 = Task(
            name="task2",
            description="Second task",
            requirements=TaskRequirements(dependencies={task1.id}),
        )

        root_task = Task(
            name="root",
            description="Root task",
            is_primitive=False,
            subtasks=[task1.id, task2.id],
        )

        plan = Plan(
            goal="Sequential test",
            root_task=root_task.id,
            tasks={
                root_task.id: root_task,
                task1.id: task1,
                task2.id: task2,
            },
        )

        result = await agent.execute_plan(plan)

        assert result["completed_tasks"] == 2


class TestReasoningIntegration:
    """Test reasoning engine integration"""

    @pytest.mark.asyncio
    async def test_agent_can_reason_chain_of_thought(self):
        """Test agent reasoning with chain-of-thought"""
        config = AgentConfig(name="agent", role="researcher")
        agent = Agent(config)
        await agent.initialize()

        query = "What is the best approach to solve this problem?"
        chain = await agent.reason(query, ReasoningStrategy.CHAIN_OF_THOUGHT)

        assert chain is not None
        assert chain.query == query
        assert chain.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT
        assert len(chain.steps) > 0
        assert chain.final_conclusion is not None

    @pytest.mark.asyncio
    async def test_agent_can_reason_deductive(self):
        """Test deductive reasoning"""
        config = AgentConfig(name="agent", role="researcher")
        agent = Agent(config)
        await agent.initialize()

        chain = await agent.reason(
            "Test deductive reasoning",
            ReasoningStrategy.DEDUCTIVE,
        )

        assert chain.strategy == ReasoningStrategy.DEDUCTIVE
        assert chain.overall_confidence >= 0.0

    @pytest.mark.asyncio
    async def test_reasoning_stores_memory(self):
        """Test that reasoning results are stored in memory"""
        config = AgentConfig(name="agent", role="researcher")
        agent = Agent(config)
        await agent.initialize()

        await agent.reason("Test query", ReasoningStrategy.CHAIN_OF_THOUGHT)

        stats = agent.memory.get_memory_stats()
        assert stats["total_memories"] > 0


class TestAutonomyDecisions:
    """Test autonomous decision making"""

    @pytest.mark.asyncio
    async def test_should_ask_human_low_confidence(self):
        """Test that agent asks human when confidence is low"""
        config = AgentConfig(
            name="agent",
            role="worker",
            autonomous_mode=True,
            ask_threshold=0.7,
        )
        agent = Agent(config)

        should_ask = await agent.should_ask_human(
            confidence=0.5,
            context="Low confidence decision",
        )

        assert should_ask is True

    @pytest.mark.asyncio
    async def test_should_not_ask_human_high_confidence(self):
        """Test that agent proceeds when confidence is high"""
        config = AgentConfig(
            name="agent",
            role="worker",
            autonomous_mode=True,
            ask_threshold=0.7,
        )
        agent = Agent(config)

        should_ask = await agent.should_ask_human(
            confidence=0.9,
            context="High confidence decision",
        )

        assert should_ask is False

    @pytest.mark.asyncio
    async def test_non_autonomous_mode_always_asks(self):
        """Test that non-autonomous mode always asks"""
        config = AgentConfig(
            name="agent",
            role="worker",
            autonomous_mode=False,
        )
        agent = Agent(config)

        should_ask = await agent.should_ask_human(
            confidence=0.99,
            context="Any decision",
        )

        assert should_ask is True


class TestAgentStatus:
    """Test agent status and monitoring"""

    @pytest.mark.asyncio
    async def test_get_comprehensive_status(self):
        """Test getting comprehensive agent status"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Execute a task to populate stats
        task = Task(name="test", description="Test task")
        await agent.execute_task(task)

        status = agent.get_status()

        assert status["name"] == "agent"
        assert status["role"] == "worker"
        assert status["status"] == AgentStatus.IDLE
        assert status["tasks_completed"] == 1
        assert status["tasks_failed"] == 0
        assert "memory" in status
        assert "reasoning" in status
        assert "uptime" in status

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self):
        """Test success rate calculation"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Execute successful task
        task1 = Task(name="success", description="Success")
        await agent.execute_task(task1)

        # Execute failing task
        requirements = TaskRequirements(
            required_capabilities={"missing"}
        )
        task2 = Task(
            name="fail",
            description="Fail",
            requirements=requirements,
        )
        try:
            await agent.execute_task(task2)
        except ValueError:
            pass

        status = agent.get_status()
        assert status["success_rate"] == 0.5


class TestAgentLifecycle:
    """Test agent lifecycle management"""

    @pytest.mark.asyncio
    async def test_agent_shutdown(self):
        """Test graceful agent shutdown"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Add some data
        task = Task(name="test", description="Test")
        await agent.execute_task(task)

        # Shutdown
        await agent.shutdown()

        state = agent.get_state()
        assert state.status == AgentStatus.SHUTDOWN

    @pytest.mark.asyncio
    async def test_agent_memory_consolidation_on_shutdown(self):
        """Test that memory is consolidated on shutdown"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        # Add important memory
        await agent.memory.remember(
            content={"important": "data"},
            importance=0.9,
        )

        # Shutdown should consolidate
        await agent.shutdown()

        # Memory stats should reflect consolidation
        stats = agent.memory.get_memory_stats()
        assert stats is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_execute_task_with_none_context(self):
        """Test task execution with None context"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        task = Task(name="test", description="Test")
        result = await agent.execute_task(task, context=None)

        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_task_with_empty_context(self):
        """Test task execution with empty context"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        task = Task(name="test", description="Test")
        result = await agent.execute_task(task, context={})

        assert result is not None

    def test_agent_with_zero_capabilities(self):
        """Test agent with no capabilities"""
        config = AgentConfig(
            name="agent",
            role="worker",
            capabilities=set(),
        )
        agent = Agent(config)

        assert len(agent.config.capabilities) == 0

    @pytest.mark.asyncio
    async def test_empty_plan_execution(self):
        """Test executing plan with only root task"""
        config = AgentConfig(name="agent", role="worker")
        agent = Agent(config)
        await agent.initialize()

        root = Task(name="root", description="Root only")
        plan = Plan(
            goal="Empty plan",
            root_task=root.id,
            tasks={root.id: root},
        )

        result = await agent.execute_plan(plan)
        assert result["completed_tasks"] == 1
