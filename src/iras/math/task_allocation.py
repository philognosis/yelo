"""
Task Allocation Algorithms for Multi-Agent Systems.

This module provides various task allocation strategies:
- Hungarian algorithm for optimal task-agent assignment
- Contract Net Protocol for distributed task allocation
- Load-aware allocation considering agent capacity
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from scipy.optimize import linear_sum_assignment


def hungarian_assignment(
    cost_matrix: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Solve the assignment problem using the Hungarian algorithm.

    The Hungarian algorithm finds the optimal assignment of tasks to agents
    that minimizes the total cost. This is a polynomial-time solution to the
    assignment problem.

    Args:
        cost_matrix: 2D numpy array where cost_matrix[i, j] represents the cost
                    of assigning task i to agent j. Shape: (n_tasks, n_agents)

    Returns:
        tuple: (task_indices, agent_indices, total_cost)
            - task_indices: Array of task indices in the optimal assignment
            - agent_indices: Array of agent indices corresponding to tasks
            - total_cost: Total cost of the optimal assignment

    Example:
        >>> cost_matrix = np.array([[4, 2, 8], [4, 3, 7], [3, 1, 6]])
        >>> tasks, agents, cost = hungarian_assignment(cost_matrix)
        >>> print(f"Task {tasks[0]} -> Agent {agents[0]}")

    Raises:
        ValueError: If cost_matrix is not 2D or contains invalid values
    """
    if cost_matrix.ndim != 2:
        raise ValueError("Cost matrix must be 2-dimensional")

    if np.any(np.isnan(cost_matrix)) or np.any(np.isinf(cost_matrix)):
        raise ValueError("Cost matrix contains NaN or Inf values")

    # Use scipy's implementation of the Hungarian algorithm
    task_indices, agent_indices = linear_sum_assignment(cost_matrix)

    # Calculate total cost
    total_cost = cost_matrix[task_indices, agent_indices].sum()

    return task_indices, agent_indices, total_cost


def contract_net_allocation(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    bid_function: Optional[callable] = None,
) -> Dict[int, int]:
    """
    Allocate tasks using the Contract Net Protocol.

    The Contract Net Protocol is a distributed task allocation mechanism where:
    1. Tasks are announced to all agents
    2. Agents submit bids based on their capabilities and current load
    3. The best bid for each task wins the contract

    Args:
        tasks: List of task dictionaries with keys like 'id', 'requirements', 'priority'
        agents: List of agent dictionaries with keys like 'id', 'capabilities', 'load'
        bid_function: Optional custom function(task, agent) -> float that returns
                     bid value (lower is better). If None, uses default bidding.

    Returns:
        dict: Mapping of task_id -> agent_id for allocated tasks

    Example:
        >>> tasks = [{'id': 0, 'requirements': {'cpu': 2}},
        ...          {'id': 1, 'requirements': {'cpu': 1}}]
        >>> agents = [{'id': 0, 'capabilities': {'cpu': 4}, 'load': 0.2},
        ...           {'id': 1, 'capabilities': {'cpu': 2}, 'load': 0.5}]
        >>> allocation = contract_net_allocation(tasks, agents)
    """

    def default_bid(task: Dict[str, Any], agent: Dict[str, Any]) -> float:
        """
        Default bidding function based on agent load and capability match.

        Lower bid is better. Returns infinity if agent cannot handle the task.
        """
        # Check if agent has required capabilities
        task_reqs = task.get('requirements', {})
        agent_caps = agent.get('capabilities', {})

        for req_key, req_val in task_reqs.items():
            if req_key not in agent_caps or agent_caps[req_key] < req_val:
                return float('inf')  # Agent cannot handle this task

        # Bid based on current load and task priority
        current_load = agent.get('load', 0.0)
        task_priority = task.get('priority', 1.0)

        # Lower bid = higher preference (less loaded, higher priority)
        bid = current_load / task_priority

        return bid

    # Use custom bid function if provided, otherwise use default
    bid_func = bid_function if bid_function is not None else default_bid

    allocation = {}

    # For each task, collect bids from all agents
    for task in tasks:
        task_id = task['id']
        best_bid = float('inf')
        best_agent = None

        # Collect bids from all agents
        for agent in agents:
            bid = bid_func(task, agent)

            if bid < best_bid:
                best_bid = bid
                best_agent = agent['id']

        # Allocate task to best bidder if found
        if best_agent is not None:
            allocation[task_id] = best_agent

            # Update agent load (simplified)
            for agent in agents:
                if agent['id'] == best_agent:
                    agent['load'] = agent.get('load', 0.0) + 0.1
                    break

    return allocation


def load_aware_allocation(
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    load_threshold: float = 0.8,
) -> Tuple[Dict[int, int], List[int]]:
    """
    Allocate tasks considering agent load and capacity constraints.

    This algorithm distributes tasks to agents while respecting their current
    load and capacity limits. Tasks are allocated to minimize load imbalance.

    Args:
        tasks: List of task dictionaries with 'id', 'load' (computational cost)
        agents: List of agent dictionaries with 'id', 'capacity', 'current_load'
        load_threshold: Maximum allowed load ratio (0.0 to 1.0) before rejecting tasks

    Returns:
        tuple: (allocation, unallocated_tasks)
            - allocation: dict mapping task_id -> agent_id
            - unallocated_tasks: list of task IDs that couldn't be allocated

    Example:
        >>> tasks = [{'id': 0, 'load': 10}, {'id': 1, 'load': 20}]
        >>> agents = [{'id': 0, 'capacity': 100, 'current_load': 50},
        ...           {'id': 1, 'capacity': 100, 'current_load': 30}]
        >>> allocation, unallocated = load_aware_allocation(tasks, agents)
    """
    allocation = {}
    unallocated_tasks = []

    # Create a copy of agent states to track load changes
    agent_states = []
    for agent in agents:
        agent_states.append({
            'id': agent['id'],
            'capacity': agent.get('capacity', 100.0),
            'current_load': agent.get('current_load', 0.0),
        })

    # Sort tasks by load (descending) - allocate heavy tasks first
    sorted_tasks = sorted(tasks, key=lambda t: t.get('load', 0.0), reverse=True)

    for task in sorted_tasks:
        task_id = task['id']
        task_load = task.get('load', 0.0)

        # Find the agent with the lowest current load that can handle this task
        best_agent = None
        best_load_ratio = float('inf')

        for agent_state in agent_states:
            capacity = agent_state['capacity']
            current = agent_state['current_load']

            # Check if agent can handle the additional load
            new_load = current + task_load
            new_load_ratio = new_load / capacity if capacity > 0 else float('inf')

            if new_load_ratio <= load_threshold and new_load_ratio < best_load_ratio:
                best_agent = agent_state
                best_load_ratio = new_load_ratio

        if best_agent is not None:
            # Allocate task to the best agent
            allocation[task_id] = best_agent['id']
            best_agent['current_load'] += task_load
        else:
            # Cannot allocate this task
            unallocated_tasks.append(task_id)

    return allocation, unallocated_tasks


def calculate_allocation_metrics(
    allocation: Dict[int, int],
    tasks: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Calculate metrics for a given task allocation.

    Args:
        allocation: Dictionary mapping task_id -> agent_id
        tasks: List of task dictionaries
        agents: List of agent dictionaries

    Returns:
        dict: Metrics including load_balance, utilization, etc.
    """
    # Count tasks per agent
    agent_task_counts = {}
    agent_loads = {}

    for agent in agents:
        agent_id = agent['id']
        agent_task_counts[agent_id] = 0
        agent_loads[agent_id] = 0.0

    # Calculate loads
    for task_id, agent_id in allocation.items():
        if agent_id in agent_task_counts:
            agent_task_counts[agent_id] += 1

            # Find task load
            task_load = next(
                (t.get('load', 1.0) for t in tasks if t['id'] == task_id),
                1.0
            )
            agent_loads[agent_id] += task_load

    # Calculate metrics
    loads = list(agent_loads.values())

    metrics = {
        'avg_load': np.mean(loads) if loads else 0.0,
        'max_load': np.max(loads) if loads else 0.0,
        'min_load': np.min(loads) if loads else 0.0,
        'load_std': np.std(loads) if loads else 0.0,
        'allocated_tasks': len(allocation),
        'total_tasks': len(tasks),
        'allocation_rate': len(allocation) / len(tasks) if tasks else 0.0,
    }

    # Load balance score (0 to 1, where 1 is perfectly balanced)
    if len(loads) > 0 and np.mean(loads) > 0:
        metrics['load_balance'] = 1.0 - (np.std(loads) / np.mean(loads))
    else:
        metrics['load_balance'] = 1.0

    return metrics
