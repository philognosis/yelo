"""
Test Suite for HTN Planning

Tests cover:
- Task creation and management
- Plan creation and decomposition
- Task dependencies and execution order
- Plan progress tracking
- Task status transitions
- Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from iras.core.planning import (
    HTNPlanner,
    Plan,
    Task,
    TaskStatus,
    TaskPriority,
    TaskRequirements,
    DecompositionStrategy,
    DecompositionRule,
)


class TestTaskCreation:
    """Test task creation and properties"""

    def test_basic_task_creation(self):
        """Test creating a simple task"""
        task = Task(
            name="test_task",
            description="A test task",
        )

        assert task.name == "test_task"
        assert task.is_primitive is True
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM

    def test_task_with_requirements(self):
        """Test task with specific requirements"""
        requirements = TaskRequirements(
            required_capabilities={"search", "analyze"},
            estimated_duration=120.0,
            estimated_tokens=2000,
        )

        task = Task(
            name="complex_task",
            description="Task with requirements",
            requirements=requirements,
        )

        assert "search" in task.requirements.required_capabilities
        assert task.requirements.estimated_duration == 120.0

    def test_task_with_dependencies(self):
        """Test task with dependencies"""
        dep_id = uuid4()
        requirements = TaskRequirements(
            dependencies={dep_id},
        )

        task = Task(
            name="dependent_task",
            description="Has dependencies",
            requirements=requirements,
        )

        assert dep_id in task.requirements.dependencies

    def test_task_priority_levels(self):
        """Test different priority levels"""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH,
            TaskPriority.CRITICAL,
        ]

        for priority in priorities:
            task = Task(
                name=f"task_{priority}",
                description="Test",
                priority=priority,
            )
            assert task.priority == priority

    def test_task_is_ready(self):
        """Test task readiness based on dependencies"""
        dep1_id = uuid4()
        dep2_id = uuid4()

        requirements = TaskRequirements(
            dependencies={dep1_id, dep2_id},
        )

        task = Task(
            name="test",
            description="Test",
            requirements=requirements,
        )

        # Not ready when dependencies not completed
        assert task.is_ready(set()) is False
        assert task.is_ready({dep1_id}) is False

        # Ready when all dependencies completed
        assert task.is_ready({dep1_id, dep2_id}) is True


class TestPlanCreation:
    """Test plan creation and initialization"""

    @pytest.mark.asyncio
    async def test_create_simple_plan(self):
        """Test creating a basic plan"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Complete test task",
            auto_decompose=False,
        )

        assert plan is not None
        assert plan.goal == "Complete test task"
        assert len(plan.tasks) == 1
        assert plan.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_plan_with_custom_task(self):
        """Test creating plan with custom initial task"""
        planner = HTNPlanner()

        initial_task = Task(
            name="custom_task",
            description="Custom initial task",
            is_primitive=True,
        )

        plan = await planner.create_plan(
            goal="Custom goal",
            initial_task=initial_task,
            auto_decompose=False,
        )

        assert plan.root_task == initial_task.id
        assert initial_task.id in plan.tasks

    @pytest.mark.asyncio
    async def test_plan_auto_decomposition(self):
        """Test automatic task decomposition"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Research AI technology",
            auto_decompose=True,
        )

        # Should have decomposed into subtasks
        root_task = plan.tasks[plan.root_task]
        assert len(root_task.subtasks) > 0

    @pytest.mark.asyncio
    async def test_plan_stored_in_planner(self):
        """Test that plans are stored"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test")

        assert plan.id in planner.plans
        assert planner.get_plan(plan.id) is not None


class TestTaskDecomposition:
    """Test task decomposition functionality"""

    @pytest.mark.asyncio
    async def test_research_task_decomposition(self):
        """Test decomposing research tasks"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Research quantum computing",
            auto_decompose=True,
        )

        root_task = plan.tasks[plan.root_task]
        # Should decompose into research subtasks
        assert len(root_task.subtasks) >= 4

    @pytest.mark.asyncio
    async def test_analysis_task_decomposition(self):
        """Test decomposing analysis tasks"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Analyze market trends",
            auto_decompose=True,
        )

        root_task = plan.tasks[plan.root_task]
        assert len(root_task.subtasks) >= 4

    @pytest.mark.asyncio
    async def test_sequential_decomposition_dependencies(self):
        """Test that sequential decomposition creates dependencies"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Research topic",
            auto_decompose=True,
        )

        root_task = plan.tasks[plan.root_task]
        if len(root_task.subtasks) > 1:
            # Later tasks should depend on earlier ones
            second_task = plan.tasks[root_task.subtasks[1]]
            first_task_id = root_task.subtasks[0]

            assert first_task_id in second_task.requirements.dependencies

    @pytest.mark.asyncio
    async def test_primitive_task_not_decomposed(self):
        """Test that primitive tasks are not decomposed"""
        planner = HTNPlanner()

        primitive_task = Task(
            name="primitive",
            description="Cannot decompose",
            is_primitive=True,
        )

        plan = await planner.create_plan(
            goal="Test",
            initial_task=primitive_task,
            auto_decompose=True,
        )

        # Should not have subtasks
        task = plan.tasks[plan.root_task]
        assert len(task.subtasks) == 0


class TestTaskExecution:
    """Test task execution and status management"""

    @pytest.mark.asyncio
    async def test_mark_task_started(self):
        """Test marking task as started"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)
        task_id = plan.root_task
        agent_id = uuid4()

        success = await planner.mark_task_started(plan.id, task_id, agent_id)

        assert success is True
        task = plan.tasks[task_id]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.assigned_to == agent_id
        assert task.started_at is not None

    @pytest.mark.asyncio
    async def test_mark_task_completed(self):
        """Test marking task as completed"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)
        task_id = plan.root_task

        # Start first
        await planner.mark_task_started(plan.id, task_id)

        # Then complete
        result = {"output": "success"}
        success = await planner.mark_task_completed(plan.id, task_id, result)

        assert success is True
        task = plan.tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task_id in plan.completed_tasks

    @pytest.mark.asyncio
    async def test_mark_task_failed(self):
        """Test marking task as failed"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)
        task_id = plan.root_task

        # Start and fail
        await planner.mark_task_started(plan.id, task_id)
        success = await planner.mark_task_failed(plan.id, task_id, "Error occurred")

        assert success is True
        task = plan.tasks[task_id]
        assert task.status == TaskStatus.FAILED
        assert task.error == "Error occurred"
        assert task_id in plan.failed_tasks

    @pytest.mark.asyncio
    async def test_plan_completion_detection(self):
        """Test that plan completion is detected"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)
        task_id = plan.root_task

        await planner.mark_task_started(plan.id, task_id)
        await planner.mark_task_completed(plan.id, task_id)

        # Plan should be marked complete
        assert plan.status == TaskStatus.COMPLETED
        assert plan.completed_at is not None


class TestTaskPrioritization:
    """Test task priority and ordering"""

    @pytest.mark.asyncio
    async def test_get_next_tasks_priority_order(self):
        """Test that next tasks are returned by priority"""
        planner = HTNPlanner()

        # Create plan with multiple tasks
        low_task = Task(name="low", description="Low priority", priority=TaskPriority.LOW)
        high_task = Task(name="high", description="High priority", priority=TaskPriority.HIGH)
        critical_task = Task(name="critical", description="Critical", priority=TaskPriority.CRITICAL)

        root_task = Task(
            name="root",
            description="Root",
            is_primitive=False,
            subtasks=[low_task.id, high_task.id, critical_task.id],
        )

        plan = Plan(
            goal="Priority test",
            root_task=root_task.id,
            tasks={
                root_task.id: root_task,
                low_task.id: low_task,
                high_task.id: high_task,
                critical_task.id: critical_task,
            },
        )

        next_tasks = plan.get_next_tasks()

        # Critical should be first
        assert next_tasks[0].priority == TaskPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_get_next_tasks_respects_dependencies(self):
        """Test that dependencies are respected"""
        task1 = Task(name="task1", description="First")
        task2 = Task(
            name="task2",
            description="Second",
            requirements=TaskRequirements(dependencies={task1.id}),
        )

        root = Task(
            name="root",
            description="Root",
            is_primitive=False,
            subtasks=[task1.id, task2.id],
        )

        plan = Plan(
            goal="Dependency test",
            root_task=root.id,
            tasks={
                root.id: root,
                task1.id: task1,
                task2.id: task2,
            },
        )

        next_tasks = plan.get_next_tasks()

        # Only task1 should be ready
        assert len(next_tasks) == 1
        assert next_tasks[0].id == task1.id


class TestPlanProgress:
    """Test plan progress tracking"""

    @pytest.mark.asyncio
    async def test_get_plan_progress_empty(self):
        """Test progress on new plan"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)

        progress = plan.get_progress()

        assert progress == 0.0

    @pytest.mark.asyncio
    async def test_get_plan_progress_partial(self):
        """Test progress with partially completed tasks"""
        task1 = Task(name="task1", description="First")
        task2 = Task(name="task2", description="Second")

        root = Task(
            name="root",
            description="Root",
            is_primitive=False,
            subtasks=[task1.id, task2.id],
        )

        plan = Plan(
            goal="Progress test",
            root_task=root.id,
            tasks={
                root.id: root,
                task1.id: task1,
                task2.id: task2,
            },
        )

        # Complete one task
        plan.completed_tasks.add(task1.id)

        progress = plan.get_progress()

        # 1 of 3 tasks completed (root + 2 subtasks)
        assert abs(progress - 1/3) < 0.01

    @pytest.mark.asyncio
    async def test_get_plan_summary(self):
        """Test getting plan summary"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test goal", auto_decompose=True)

        summary = planner.get_plan_summary(plan.id)

        assert summary is not None
        assert summary["goal"] == "Test goal"
        assert "progress" in summary
        assert "total_tasks" in summary
        assert "hierarchy" in summary


class TestTaskHierarchy:
    """Test task hierarchy representation"""

    @pytest.mark.asyncio
    async def test_get_task_hierarchy(self):
        """Test getting hierarchical task structure"""
        task1 = Task(name="subtask1", description="Sub 1")
        task2 = Task(name="subtask2", description="Sub 2")

        root = Task(
            name="root",
            description="Root task",
            is_primitive=False,
            subtasks=[task1.id, task2.id],
        )

        plan = Plan(
            goal="Hierarchy test",
            root_task=root.id,
            tasks={
                root.id: root,
                task1.id: task1,
                task2.id: task2,
            },
        )

        hierarchy = plan.get_task_hierarchy()

        assert hierarchy["name"] == "root"
        assert len(hierarchy["subtasks"]) == 2
        assert hierarchy["subtasks"][0]["name"] == "subtask1"

    @pytest.mark.asyncio
    async def test_nested_task_hierarchy(self):
        """Test deeply nested task hierarchy"""
        leaf = Task(name="leaf", description="Leaf task")
        middle = Task(
            name="middle",
            description="Middle",
            is_primitive=False,
            subtasks=[leaf.id],
        )
        root = Task(
            name="root",
            description="Root",
            is_primitive=False,
            subtasks=[middle.id],
        )

        plan = Plan(
            goal="Nested test",
            root_task=root.id,
            tasks={
                root.id: root,
                middle.id: middle,
                leaf.id: leaf,
            },
        )

        hierarchy = plan.get_task_hierarchy()

        assert hierarchy["name"] == "root"
        assert hierarchy["subtasks"][0]["name"] == "middle"
        assert hierarchy["subtasks"][0]["subtasks"][0]["name"] == "leaf"


class TestParentTaskCompletion:
    """Test parent task completion logic"""

    @pytest.mark.asyncio
    async def test_parent_completes_when_all_subtasks_done(self):
        """Test parent marked complete when all subtasks done"""
        planner = HTNPlanner()

        task1 = Task(name="sub1", description="Subtask 1")
        task2 = Task(name="sub2", description="Subtask 2")

        parent = Task(
            name="parent",
            description="Parent task",
            is_primitive=False,
            subtasks=[task1.id, task2.id],
        )

        plan = Plan(
            goal="Parent test",
            root_task=parent.id,
            tasks={
                parent.id: parent,
                task1.id: task1,
                task2.id: task2,
            },
        )

        planner.plans[plan.id] = plan

        # Complete subtasks
        await planner.mark_task_started(plan.id, task1.id)
        await planner.mark_task_completed(plan.id, task1.id)

        await planner.mark_task_started(plan.id, task2.id)
        await planner.mark_task_completed(plan.id, task2.id)

        # Parent should be completed
        assert parent.status == TaskStatus.COMPLETED
        assert parent.id in plan.completed_tasks


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_mark_task_started_invalid_plan(self):
        """Test starting task with invalid plan ID"""
        planner = HTNPlanner()

        fake_plan_id = uuid4()
        fake_task_id = uuid4()

        success = await planner.mark_task_started(fake_plan_id, fake_task_id)

        assert success is False

    @pytest.mark.asyncio
    async def test_mark_task_completed_without_starting(self):
        """Test completing task that wasn't started"""
        planner = HTNPlanner()

        plan = await planner.create_plan(goal="Test", auto_decompose=False)
        task_id = plan.root_task

        success = await planner.mark_task_completed(plan.id, task_id)

        assert success is False

    @pytest.mark.asyncio
    async def test_get_next_tasks_empty_plan(self):
        """Test getting next tasks from plan with no ready tasks"""
        plan = Plan(
            goal="Empty",
            root_task=uuid4(),
            tasks={},
        )

        next_tasks = plan.get_next_tasks()

        assert len(next_tasks) == 0

    @pytest.mark.asyncio
    async def test_plan_progress_no_tasks(self):
        """Test progress calculation with no tasks"""
        plan = Plan(
            goal="No tasks",
            root_task=uuid4(),
            tasks={},
        )

        progress = plan.get_progress()

        assert progress == 0.0

    @pytest.mark.asyncio
    async def test_get_plan_summary_nonexistent(self):
        """Test getting summary of non-existent plan"""
        planner = HTNPlanner()

        fake_id = uuid4()
        summary = planner.get_plan_summary(fake_id)

        assert summary is None

    @pytest.mark.asyncio
    async def test_task_is_ready_no_dependencies(self):
        """Test task with no dependencies is always ready"""
        task = Task(name="test", description="Test")

        assert task.is_ready(set()) is True
        assert task.is_ready({uuid4()}) is True

    @pytest.mark.asyncio
    async def test_decomposition_no_matching_rule(self):
        """Test decomposition with no matching rule"""
        planner = HTNPlanner()

        plan = await planner.create_plan(
            goal="Unrecognized task type",
            auto_decompose=True,
        )

        root = plan.tasks[plan.root_task]
        # Should be marked primitive when no rule matches
        assert root.is_primitive is True
