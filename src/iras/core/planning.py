"""
Hierarchical Task Network (HTN) Planning

Implements:
- Task decomposition
- Multi-level planning
- Plan validation
- Dynamic replanning
- Resource estimation
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """Task priority levels"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskRequirements:
    """Requirements for task execution"""

    required_capabilities: Set[str] = field(default_factory=set)
    estimated_duration: float = 60.0  # seconds
    estimated_tokens: int = 1000
    dependencies: Set[UUID] = field(default_factory=set)
    resources: Dict[str, Any] = field(default_factory=dict)


class Task(BaseModel):
    """
    Represents a task in the HTN

    Can be:
    - Primitive (directly executable)
    - Compound (requires decomposition)
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    is_primitive: bool = True
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    # Hierarchical structure
    parent_task: Optional[UUID] = None
    subtasks: List[UUID] = Field(default_factory=list)

    # Requirements and constraints
    requirements: TaskRequirements = Field(default_factory=TaskRequirements)

    # Execution tracking
    assigned_to: Optional[UUID] = None  # Agent ID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def is_ready(self, completed_tasks: Set[UUID]) -> bool:
        """Check if task dependencies are satisfied"""
        return all(dep in completed_tasks for dep in self.requirements.dependencies)

    def estimate_completion_time(self) -> float:
        """Estimate total completion time including subtasks"""
        return self.requirements.estimated_duration


class DecompositionStrategy(str, Enum):
    """Task decomposition strategies"""

    SEQUENTIAL = "sequential"  # Execute subtasks in order
    PARALLEL = "parallel"  # Execute subtasks concurrently
    CONDITIONAL = "conditional"  # Execute based on conditions
    ITERATIVE = "iterative"  # Repeat until condition


@dataclass
class DecompositionRule:
    """Rule for decomposing compound tasks"""

    task_pattern: str  # Pattern to match task type
    strategy: DecompositionStrategy
    subtask_templates: List[Dict[str, Any]]
    preconditions: List[str] = field(default_factory=list)


class Plan(BaseModel):
    """
    Hierarchical task network plan

    Contains:
    - Task hierarchy
    - Execution order
    - Resource allocation
    """

    id: UUID = Field(default_factory=uuid4)
    goal: str
    root_task: UUID
    tasks: Dict[UUID, Task] = Field(default_factory=dict)

    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    current_tasks: Set[UUID] = Field(default_factory=set)  # Currently executing
    completed_tasks: Set[UUID] = Field(default_factory=set)
    failed_tasks: Set[UUID] = Field(default_factory=set)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

    def get_next_tasks(self) -> List[Task]:
        """
        Get tasks ready for execution

        Returns primitive tasks whose dependencies are satisfied
        """
        ready_tasks = []

        for task_id, task in self.tasks.items():
            if (
                task.status == TaskStatus.PENDING
                and task.is_primitive
                and task.is_ready(self.completed_tasks)
                and task_id not in self.current_tasks
            ):
                ready_tasks.append(task)

        # Sort by priority
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
        return ready_tasks

    def get_progress(self) -> float:
        """Calculate plan completion progress (0.0 to 1.0)"""
        if not self.tasks:
            return 0.0

        total_tasks = len(self.tasks)
        completed = len(self.completed_tasks)
        return completed / total_tasks

    def get_task_hierarchy(self, task_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get task hierarchy as nested dict"""
        if task_id is None:
            task_id = self.root_task

        task = self.tasks.get(task_id)
        if not task:
            return {}

        return {
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "is_primitive": task.is_primitive,
            "subtasks": [
                self.get_task_hierarchy(subtask_id)
                for subtask_id in task.subtasks
            ],
        }


class HTNPlanner:
    """
    Hierarchical Task Network Planner

    Features:
    - Automatic task decomposition
    - Multi-level planning
    - Dynamic replanning
    - Resource-aware scheduling
    """

    def __init__(self):
        self.plans: Dict[UUID, Plan] = {}
        self.decomposition_rules: List[DecompositionRule] = []
        self._lock = asyncio.Lock()

        # Register default decomposition rules
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register default task decomposition rules"""

        # Research task decomposition
        research_rule = DecompositionRule(
            task_pattern="research",
            strategy=DecompositionStrategy.SEQUENTIAL,
            subtask_templates=[
                {"name": "define_scope", "description": "Define research scope and objectives"},
                {"name": "gather_sources", "description": "Gather relevant sources"},
                {"name": "analyze_sources", "description": "Analyze gathered sources"},
                {"name": "synthesize", "description": "Synthesize findings"},
            ],
        )
        self.decomposition_rules.append(research_rule)

        # Analysis task decomposition
        analysis_rule = DecompositionRule(
            task_pattern="analyze",
            strategy=DecompositionStrategy.SEQUENTIAL,
            subtask_templates=[
                {"name": "collect_data", "description": "Collect data for analysis"},
                {"name": "process_data", "description": "Process and clean data"},
                {"name": "apply_methods", "description": "Apply analytical methods"},
                {"name": "interpret_results", "description": "Interpret results"},
            ],
        )
        self.decomposition_rules.append(analysis_rule)

    async def create_plan(
        self,
        goal: str,
        initial_task: Optional[Task] = None,
        auto_decompose: bool = True,
    ) -> Plan:
        """
        Create a new plan for achieving a goal

        Args:
            goal: The goal to achieve
            initial_task: Optional initial task (created if not provided)
            auto_decompose: Automatically decompose compound tasks

        Returns:
            Created plan
        """
        async with self._lock:
            # Create initial task if not provided
            if initial_task is None:
                initial_task = Task(
                    name=goal,
                    description=f"Achieve goal: {goal}",
                    is_primitive=False,  # Will be decomposed
                    priority=TaskPriority.HIGH,
                )

            # Create plan
            plan = Plan(
                goal=goal,
                root_task=initial_task.id,
                tasks={initial_task.id: initial_task},
            )

            # Auto-decompose if requested
            if auto_decompose and not initial_task.is_primitive:
                await self._decompose_task(plan, initial_task.id)

            self.plans[plan.id] = plan
            logger.info(f"Created plan {plan.id} for goal: {goal}")

            return plan

    async def _decompose_task(self, plan: Plan, task_id: UUID) -> List[UUID]:
        """
        Decompose a compound task into subtasks

        Args:
            plan: The plan containing the task
            task_id: ID of task to decompose

        Returns:
            List of created subtask IDs
        """
        task = plan.tasks.get(task_id)
        if not task or task.is_primitive:
            return []

        # Find matching decomposition rule
        rule = self._find_decomposition_rule(task)
        if not rule:
            logger.warning(f"No decomposition rule found for task: {task.name}")
            # Mark as primitive (can't decompose further)
            task.is_primitive = True
            return []

        # Create subtasks from templates
        subtask_ids = []
        for i, template in enumerate(rule.subtask_templates):
            subtask = Task(
                name=template["name"],
                description=template.get("description", ""),
                is_primitive=template.get("is_primitive", True),
                parent_task=task_id,
                priority=task.priority,
            )

            # Set dependencies (sequential by default)
            if rule.strategy == DecompositionStrategy.SEQUENTIAL and i > 0:
                subtask.requirements.dependencies.add(subtask_ids[-1])

            plan.tasks[subtask.id] = subtask
            subtask_ids.append(subtask.id)

        # Update parent task
        task.subtasks = subtask_ids

        logger.info(f"Decomposed task '{task.name}' into {len(subtask_ids)} subtasks")

        # Recursively decompose compound subtasks
        for subtask_id in subtask_ids:
            subtask = plan.tasks[subtask_id]
            if not subtask.is_primitive:
                await self._decompose_task(plan, subtask_id)

        return subtask_ids

    def _find_decomposition_rule(self, task: Task) -> Optional[DecompositionRule]:
        """Find applicable decomposition rule for task"""
        task_name_lower = task.name.lower()

        for rule in self.decomposition_rules:
            if rule.task_pattern in task_name_lower:
                return rule

        return None

    async def mark_task_started(
        self,
        plan_id: UUID,
        task_id: UUID,
        agent_id: Optional[UUID] = None,
    ) -> bool:
        """Mark task as started"""
        async with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return False

            task = plan.tasks.get(task_id)
            if not task or task.status != TaskStatus.PENDING:
                return False

            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            task.assigned_to = agent_id
            plan.current_tasks.add(task_id)

            if plan.status == TaskStatus.PENDING:
                plan.status = TaskStatus.IN_PROGRESS
                plan.started_at = datetime.now()

            logger.info(f"Task '{task.name}' started")
            return True

    async def mark_task_completed(
        self,
        plan_id: UUID,
        task_id: UUID,
        result: Optional[Any] = None,
    ) -> bool:
        """Mark task as completed"""
        async with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return False

            task = plan.tasks.get(task_id)
            if not task or task.status != TaskStatus.IN_PROGRESS:
                return False

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            plan.current_tasks.discard(task_id)
            plan.completed_tasks.add(task_id)

            # Check if parent task is completed
            if task.parent_task:
                await self._check_parent_completion(plan, task.parent_task)

            # Check if plan is completed
            if plan.root_task in plan.completed_tasks:
                plan.status = TaskStatus.COMPLETED
                plan.completed_at = datetime.now()
                logger.info(f"Plan {plan_id} completed!")

            logger.info(f"Task '{task.name}' completed")
            return True

    async def mark_task_failed(
        self,
        plan_id: UUID,
        task_id: UUID,
        error: str,
    ) -> bool:
        """Mark task as failed"""
        async with self._lock:
            plan = self.plans.get(plan_id)
            if not plan:
                return False

            task = plan.tasks.get(task_id)
            if not task:
                return False

            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error
            plan.current_tasks.discard(task_id)
            plan.failed_tasks.add(task_id)

            logger.error(f"Task '{task.name}' failed: {error}")
            return True

    async def _check_parent_completion(self, plan: Plan, parent_id: UUID) -> None:
        """Check if parent task can be marked as completed"""
        parent = plan.tasks.get(parent_id)
        if not parent:
            return

        # Check if all subtasks are completed
        all_completed = all(
            subtask_id in plan.completed_tasks
            for subtask_id in parent.subtasks
        )

        if all_completed and parent.status != TaskStatus.COMPLETED:
            parent.status = TaskStatus.COMPLETED
            parent.completed_at = datetime.now()
            plan.completed_tasks.add(parent_id)

            # Recursively check grandparent
            if parent.parent_task:
                await self._check_parent_completion(plan, parent.parent_task)

    def get_plan(self, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID"""
        return self.plans.get(plan_id)

    def get_plan_summary(self, plan_id: UUID) -> Optional[Dict[str, Any]]:
        """Get plan summary"""
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        return {
            "id": str(plan.id),
            "goal": plan.goal,
            "status": plan.status,
            "progress": plan.get_progress(),
            "total_tasks": len(plan.tasks),
            "completed_tasks": len(plan.completed_tasks),
            "failed_tasks": len(plan.failed_tasks),
            "current_tasks": len(plan.current_tasks),
            "hierarchy": plan.get_task_hierarchy(),
        }
