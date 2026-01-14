"""
Mathematical Foundations Module for IRAS Multi-Agent System.

This module provides mathematical algorithms and utilities for:
- Task allocation (Hungarian algorithm, Contract Net, Load-aware allocation)
- Consensus mechanisms (Voting, PBFT, Raft)
- Load balancing (Round-robin, Least-loaded, Response time-based)
- Graph analysis (Network analysis, Centrality, Clustering)
"""

from .task_allocation import (
    hungarian_assignment,
    contract_net_allocation,
    load_aware_allocation,
)
from .consensus import (
    majority_voting,
    weighted_voting,
    pbft_consensus,
    raft_consensus,
)
from .load_balancing import (
    round_robin_balance,
    least_loaded_balance,
    response_time_balance,
)
from .graph_analysis import (
    analyze_agent_network,
    calculate_centrality,
    calculate_clustering_coefficient,
)

__all__ = [
    # Task allocation
    "hungarian_assignment",
    "contract_net_allocation",
    "load_aware_allocation",
    # Consensus
    "majority_voting",
    "weighted_voting",
    "pbft_consensus",
    "raft_consensus",
    # Load balancing
    "round_robin_balance",
    "least_loaded_balance",
    "response_time_balance",
    # Graph analysis
    "analyze_agent_network",
    "calculate_centrality",
    "calculate_clustering_coefficient",
]
