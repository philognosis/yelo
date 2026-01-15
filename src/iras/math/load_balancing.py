"""
Load Balancing Algorithms for Multi-Agent Systems.

This module provides various load balancing strategies:
- Round-robin balancing for even distribution
- Least-loaded balancing based on current agent load
- Response time-based balancing for performance optimization
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import deque


class RoundRobinBalancer:
    """
    Round-robin load balancer that distributes tasks evenly across agents.

    This balancer cycles through agents in order, ensuring fair distribution
    without considering current load or performance.
    """

    def __init__(self, agent_ids: List[int]):
        """
        Initialize the round-robin balancer.

        Args:
            agent_ids: List of agent identifiers
        """
        self.agents = deque(agent_ids)
        self.assignment_count = {agent_id: 0 for agent_id in agent_ids}

    def next_agent(self) -> int:
        """
        Get the next agent in round-robin order.

        Returns:
            int: Agent ID to assign the next task to
        """
        if not self.agents:
            raise ValueError("No agents available")

        # Get next agent and rotate
        agent_id = self.agents[0]
        self.agents.rotate(-1)

        # Track assignment
        self.assignment_count[agent_id] += 1

        return agent_id

    def get_stats(self) -> Dict[str, Any]:
        """Get balancer statistics."""
        counts = list(self.assignment_count.values())
        return {
            'assignments': dict(self.assignment_count),
            'total_assignments': sum(counts),
            'avg_assignments': np.mean(counts) if counts else 0.0,
            'std_assignments': np.std(counts) if counts else 0.0,
        }


def round_robin_balance(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
) -> Dict[int, int]:
    """
    Distribute tasks using round-robin algorithm.

    Tasks are assigned to agents in circular order, ensuring even distribution.

    Args:
        tasks: List of task dictionaries with at least an 'id' field
        agents: List of agent dictionaries with at least an 'id' field

    Returns:
        dict: Mapping of task_id -> agent_id

    Example:
        >>> tasks = [{'id': i} for i in range(5)]
        >>> agents = [{'id': 0}, {'id': 1}, {'id': 2}]
        >>> allocation = round_robin_balance(tasks, agents)
        >>> # Tasks 0,3 -> Agent 0; Tasks 1,4 -> Agent 1; Task 2 -> Agent 2
    """
    if not agents:
        return {}

    agent_ids = [agent['id'] for agent in agents]
    balancer = RoundRobinBalancer(agent_ids)

    allocation = {}
    for task in tasks:
        task_id = task['id']
        agent_id = balancer.next_agent()
        allocation[task_id] = agent_id

    return allocation


class LeastLoadedBalancer:
    """
    Least-loaded balancer that assigns tasks to the least busy agent.

    This balancer tracks current load for each agent and assigns new tasks
    to the agent with the lowest load.
    """

    def __init__(self, agents: List[Dict[str, Any]]):
        """
        Initialize the least-loaded balancer.

        Args:
            agents: List of agent dictionaries with 'id' and optional 'current_load'
        """
        self.agent_loads = {}
        for agent in agents:
            agent_id = agent['id']
            self.agent_loads[agent_id] = agent.get('current_load', 0.0)

    def assign_task(self, task_load: float = 1.0) -> int:
        """
        Assign a task to the least loaded agent.

        Args:
            task_load: Load value of the task (default: 1.0)

        Returns:
            int: Agent ID of the least loaded agent
        """
        if not self.agent_loads:
            raise ValueError("No agents available")

        # Find agent with minimum load
        min_agent = min(self.agent_loads.items(), key=lambda x: x[1])
        agent_id = min_agent[0]

        # Update load
        self.agent_loads[agent_id] += task_load

        return agent_id

    def get_stats(self) -> Dict[str, Any]:
        """Get balancer statistics."""
        loads = list(self.agent_loads.values())
        return {
            'agent_loads': dict(self.agent_loads),
            'total_load': sum(loads),
            'avg_load': np.mean(loads) if loads else 0.0,
            'max_load': max(loads) if loads else 0.0,
            'min_load': min(loads) if loads else 0.0,
            'load_std': np.std(loads) if loads else 0.0,
            'load_balance': 1.0 - (np.std(loads) / np.mean(loads)) if loads and np.mean(loads) > 0 else 1.0,
        }


def least_loaded_balance(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
) -> Dict[int, int]:
    """
    Distribute tasks to least loaded agents.

    Each task is assigned to the agent with the current lowest load.

    Args:
        tasks: List of task dictionaries with 'id' and optional 'load'
        agents: List of agent dictionaries with 'id' and optional 'current_load'

    Returns:
        dict: Mapping of task_id -> agent_id

    Example:
        >>> tasks = [{'id': 0, 'load': 10}, {'id': 1, 'load': 5}]
        >>> agents = [{'id': 0, 'current_load': 20}, {'id': 1, 'current_load': 5}]
        >>> allocation = least_loaded_balance(tasks, agents)
        >>> # Task 0 -> Agent 1 (lower load), Task 1 -> depends on load after task 0
    """
    if not agents:
        return {}

    balancer = LeastLoadedBalancer(agents)

    allocation = {}
    for task in tasks:
        task_id = task['id']
        task_load = task.get('load', 1.0)
        agent_id = balancer.assign_task(task_load)
        allocation[task_id] = agent_id

    return allocation


class ResponseTimeBalancer:
    """
    Response time-based balancer using exponential moving average.

    This balancer tracks historical response times for each agent and
    assigns tasks to agents with the best (lowest) average response time.
    """

    def __init__(
        self,
        agents: List[Dict[str, Any]],
        alpha: float = 0.3,
    ):
        """
        Initialize the response time balancer.

        Args:
            agents: List of agent dictionaries with 'id' and optional 'avg_response_time'
            alpha: Smoothing factor for exponential moving average (0 < alpha <= 1)
                  Higher alpha = more weight on recent observations
        """
        self.alpha = alpha
        self.agent_response_times = {}
        self.agent_pending_tasks = {}

        for agent in agents:
            agent_id = agent['id']
            self.agent_response_times[agent_id] = agent.get('avg_response_time', 1.0)
            self.agent_pending_tasks[agent_id] = 0

    def assign_task(self) -> int:
        """
        Assign a task to the agent with best expected response time.

        Takes into account both average response time and current pending tasks.

        Returns:
            int: Agent ID with the best expected response time
        """
        if not self.agent_response_times:
            raise ValueError("No agents available")

        # Calculate expected response time considering pending tasks
        expected_times = {}
        for agent_id, avg_time in self.agent_response_times.items():
            pending = self.agent_pending_tasks[agent_id]
            # Expected time increases with pending tasks
            expected_times[agent_id] = avg_time * (1 + pending * 0.5)

        # Choose agent with minimum expected response time
        best_agent = min(expected_times.items(), key=lambda x: x[1])
        agent_id = best_agent[0]

        # Increment pending tasks
        self.agent_pending_tasks[agent_id] += 1

        return agent_id

    def record_completion(
        self,
        agent_id: int,
        response_time: float,
    ) -> None:
        """
        Record task completion and update response time statistics.

        Args:
            agent_id: ID of the agent that completed the task
            response_time: Actual response time for the completed task
        """
        if agent_id not in self.agent_response_times:
            raise ValueError(f"Unknown agent ID: {agent_id}")

        # Update exponential moving average
        current_avg = self.agent_response_times[agent_id]
        new_avg = self.alpha * response_time + (1 - self.alpha) * current_avg
        self.agent_response_times[agent_id] = new_avg

        # Decrement pending tasks
        if self.agent_pending_tasks[agent_id] > 0:
            self.agent_pending_tasks[agent_id] -= 1

    def get_stats(self) -> Dict[str, Any]:
        """Get balancer statistics."""
        response_times = list(self.agent_response_times.values())
        pending_tasks = list(self.agent_pending_tasks.values())

        return {
            'agent_response_times': dict(self.agent_response_times),
            'agent_pending_tasks': dict(self.agent_pending_tasks),
            'avg_response_time': np.mean(response_times) if response_times else 0.0,
            'max_response_time': max(response_times) if response_times else 0.0,
            'min_response_time': min(response_times) if response_times else 0.0,
            'total_pending': sum(pending_tasks),
        }


def response_time_balance(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    alpha: float = 0.3,
) -> Tuple[Dict[int, int], ResponseTimeBalancer]:
    """
    Distribute tasks based on agent response time performance.

    Tasks are assigned to agents with the best historical response times,
    taking into account current load.

    Args:
        tasks: List of task dictionaries with 'id'
        agents: List of agent dictionaries with 'id' and optional 'avg_response_time'
        alpha: Smoothing factor for response time tracking (0 < alpha <= 1)

    Returns:
        tuple: (allocation, balancer)
            - allocation: dict mapping task_id -> agent_id
            - balancer: ResponseTimeBalancer instance for tracking completions

    Example:
        >>> tasks = [{'id': i} for i in range(5)]
        >>> agents = [
        ...     {'id': 0, 'avg_response_time': 1.5},
        ...     {'id': 1, 'avg_response_time': 1.0},
        ... ]
        >>> allocation, balancer = response_time_balance(tasks, agents)
        >>> # Later, record completions:
        >>> balancer.record_completion(agent_id=1, response_time=0.8)
    """
    if not agents:
        return {}, None

    balancer = ResponseTimeBalancer(agents, alpha=alpha)

    allocation = {}
    for task in tasks:
        task_id = task['id']
        agent_id = balancer.assign_task()
        allocation[task_id] = agent_id

    return allocation, balancer


def calculate_load_balance_score(
    agent_loads: Dict[int, float],
) -> float:
    """
    Calculate a load balance score (0 to 1, where 1 is perfectly balanced).

    Args:
        agent_loads: Dictionary mapping agent_id -> current load

    Returns:
        float: Balance score from 0 (completely imbalanced) to 1 (perfectly balanced)
    """
    if not agent_loads:
        return 1.0

    loads = np.array(list(agent_loads.values()))

    if len(loads) == 1:
        return 1.0

    avg_load = np.mean(loads)
    if avg_load == 0:
        return 1.0

    # Use coefficient of variation (CV) to measure balance
    # CV = std / mean
    # Score = 1 / (1 + CV)
    std_load = np.std(loads)
    cv = std_load / avg_load
    score = 1.0 / (1.0 + cv)

    return score


def adaptive_load_balance(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    strategy: str = 'auto',
) -> Dict[int, int]:
    """
    Adaptively select and apply the best load balancing strategy.

    Args:
        tasks: List of task dictionaries
        agents: List of agent dictionaries
        strategy: Balancing strategy - 'auto', 'round_robin', 'least_loaded', 'response_time'

    Returns:
        dict: Mapping of task_id -> agent_id

    Example:
        >>> tasks = [{'id': i, 'load': np.random.random()} for i in range(10)]
        >>> agents = [{'id': i, 'current_load': 0} for i in range(3)]
        >>> allocation = adaptive_load_balance(tasks, agents, strategy='auto')
    """
    if not agents or not tasks:
        return {}

    # Auto-select strategy based on available information
    if strategy == 'auto':
        has_load_info = any('load' in task for task in tasks)
        has_response_info = any('avg_response_time' in agent for agent in agents)

        if has_response_info:
            strategy = 'response_time'
        elif has_load_info:
            strategy = 'least_loaded'
        else:
            strategy = 'round_robin'

    # Apply selected strategy
    if strategy == 'round_robin':
        return round_robin_balance(tasks, agents)
    elif strategy == 'least_loaded':
        return least_loaded_balance(tasks, agents)
    elif strategy == 'response_time':
        allocation, _ = response_time_balance(tasks, agents)
        return allocation
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
