"""
Consensus Algorithms for Multi-Agent Systems.

This module provides various consensus mechanisms:
- Majority voting (simple and quorum-based)
- Weighted voting based on agent reputation/expertise
- Simplified PBFT (Practical Byzantine Fault Tolerance)
- Simplified Raft consensus protocol
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np


def majority_voting(
    votes: List[Any],
    quorum: Optional[float] = None,
) -> Tuple[Any, float, bool]:
    """
    Determine consensus using simple majority or quorum-based voting.

    Args:
        votes: List of votes from agents (can be any hashable type)
        quorum: Optional minimum fraction of votes (0.0 to 1.0) required
               for consensus. If None, uses simple majority (>50%)

    Returns:
        tuple: (winner, vote_fraction, consensus_reached)
            - winner: The option with most votes (or None if no consensus)
            - vote_fraction: Fraction of votes for the winner
            - consensus_reached: Boolean indicating if quorum was met

    Example:
        >>> votes = ['A', 'A', 'B', 'A', 'C']
        >>> winner, fraction, consensus = majority_voting(votes, quorum=0.5)
        >>> print(f"Winner: {winner}, Support: {fraction:.1%}")
    """
    if not votes:
        return None, 0.0, False

    # Count votes
    vote_counts = Counter(votes)
    winner, winner_count = vote_counts.most_common(1)[0]

    # Calculate vote fraction
    vote_fraction = winner_count / len(votes)

    # Determine if consensus is reached
    if quorum is None:
        quorum = 0.5  # Simple majority

    consensus_reached = vote_fraction > quorum

    return winner, vote_fraction, consensus_reached


def weighted_voting(
    votes: List[Any],
    weights: List[float],
    quorum: Optional[float] = None,
) -> Tuple[Any, float, bool]:
    """
    Determine consensus using weighted voting.

    Votes are weighted by agent expertise, reputation, or other factors.

    Args:
        votes: List of votes from agents
        weights: List of weights corresponding to each vote (must be same length as votes)
        quorum: Optional minimum weighted fraction (0.0 to 1.0) required
               for consensus. If None, uses weighted majority (>50% of total weight)

    Returns:
        tuple: (winner, weighted_fraction, consensus_reached)
            - winner: The option with highest weighted votes
            - weighted_fraction: Fraction of total weight for the winner
            - consensus_reached: Boolean indicating if weighted quorum was met

    Example:
        >>> votes = ['A', 'A', 'B', 'A', 'C']
        >>> weights = [0.3, 0.2, 0.3, 0.1, 0.1]  # Based on agent expertise
        >>> winner, fraction, consensus = weighted_voting(votes, weights)

    Raises:
        ValueError: If votes and weights have different lengths or weights are invalid
    """
    if len(votes) != len(weights):
        raise ValueError("Votes and weights must have the same length")

    if not votes:
        return None, 0.0, False

    if any(w < 0 for w in weights):
        raise ValueError("Weights must be non-negative")

    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Total weight must be positive")

    # Calculate weighted vote counts
    weighted_counts = {}
    for vote, weight in zip(votes, weights):
        weighted_counts[vote] = weighted_counts.get(vote, 0.0) + weight

    # Find winner
    winner = max(weighted_counts.items(), key=lambda x: x[1])[0]
    winner_weight = weighted_counts[winner]

    # Calculate weighted fraction
    weighted_fraction = winner_weight / total_weight

    # Determine if consensus is reached
    if quorum is None:
        quorum = 0.5  # Weighted majority

    consensus_reached = weighted_fraction > quorum

    return winner, weighted_fraction, consensus_reached


def pbft_consensus(
    proposals: List[Dict[str, Any]],
    agent_states: List[Dict[str, Any]],
    byzantine_tolerance: int = 1,
) -> Tuple[Optional[Dict[str, Any]], bool, Dict[str, Any]]:
    """
    Simplified PBFT (Practical Byzantine Fault Tolerance) consensus.

    PBFT allows consensus even when up to f agents are faulty or Byzantine,
    requiring 3f + 1 total agents.

    This is a simplified implementation that simulates the three-phase protocol:
    1. Pre-prepare: Primary proposes a value
    2. Prepare: Agents verify and vote
    3. Commit: Final agreement phase

    Args:
        proposals: List of proposal dictionaries from agents with 'agent_id', 'value', 'signature'
        agent_states: List of agent state dictionaries with 'id', 'is_faulty' (optional)
        byzantine_tolerance: Number of Byzantine (faulty) agents to tolerate (f)

    Returns:
        tuple: (agreed_value, consensus_reached, metrics)
            - agreed_value: The consensus value (or None if no consensus)
            - consensus_reached: Boolean indicating if PBFT consensus was reached
            - metrics: Dictionary with consensus metrics

    Example:
        >>> proposals = [
        ...     {'agent_id': 0, 'value': 'A', 'signature': 'sig0'},
        ...     {'agent_id': 1, 'value': 'A', 'signature': 'sig1'},
        ...     {'agent_id': 2, 'value': 'A', 'signature': 'sig2'},
        ...     {'agent_id': 3, 'value': 'B', 'signature': 'sig3'},
        ... ]
        >>> agents = [{'id': i} for i in range(4)]
        >>> value, consensus, metrics = pbft_consensus(proposals, agents, byzantine_tolerance=1)
    """
    n_agents = len(agent_states)
    f = byzantine_tolerance

    # PBFT requires at least 3f + 1 agents
    min_agents = 3 * f + 1
    if n_agents < min_agents:
        return None, False, {
            'error': f'Need at least {min_agents} agents for f={f} Byzantine tolerance',
            'n_agents': n_agents,
        }

    # Count votes for each proposal value
    proposal_counts = Counter([p['value'] for p in proposals])

    # PBFT requires 2f + 1 matching responses for consensus
    required_votes = 2 * f + 1

    metrics = {
        'n_agents': n_agents,
        'n_proposals': len(proposals),
        'byzantine_tolerance': f,
        'required_votes': required_votes,
    }

    # Find if any value has enough votes
    for value, count in proposal_counts.most_common():
        if count >= required_votes:
            metrics['consensus_votes'] = count
            metrics['consensus_fraction'] = count / n_agents
            return value, True, metrics

    # No consensus reached
    metrics['max_votes'] = proposal_counts.most_common(1)[0][1] if proposal_counts else 0
    return None, False, metrics


def raft_consensus(
    agents: List[Dict[str, Any]],
    proposed_value: Any,
    current_term: int = 0,
) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Simplified Raft consensus algorithm.

    Raft is a consensus algorithm designed to be more understandable than Paxos.
    It uses leader election and log replication.

    This is a simplified single-round implementation focusing on:
    1. Leader election (based on votes)
    2. Log replication (majority agreement)

    Args:
        agents: List of agent dictionaries with 'id', 'vote', 'is_leader' (optional)
        proposed_value: Value proposed by the leader
        current_term: Current term number (for leader election)

    Returns:
        tuple: (committed_value, state_info)
            - committed_value: The committed value if consensus reached, else None
            - state_info: Dictionary with leader_id, term, votes, etc.

    Example:
        >>> agents = [
        ...     {'id': 0, 'vote': 'approve', 'is_leader': True},
        ...     {'id': 1, 'vote': 'approve'},
        ...     {'id': 2, 'vote': 'approve'},
        ...     {'id': 3, 'vote': 'reject'},
        ... ]
        >>> value, info = raft_consensus(agents, proposed_value='update_config')
    """
    if not agents:
        return None, {'error': 'No agents provided'}

    n_agents = len(agents)
    majority = (n_agents // 2) + 1

    # Determine leader (first agent marked as leader, or agent 0)
    leader_id = None
    for agent in agents:
        if agent.get('is_leader', False):
            leader_id = agent['id']
            break

    if leader_id is None:
        # Simple election: agent with lowest ID becomes leader
        leader_id = min(agent['id'] for agent in agents)

    # Count votes for the proposed value
    votes = [agent.get('vote') for agent in agents]
    approve_votes = sum(1 for v in votes if v == 'approve')

    # Raft requires majority approval
    consensus_reached = approve_votes >= majority

    state_info = {
        'leader_id': leader_id,
        'term': current_term,
        'n_agents': n_agents,
        'majority_required': majority,
        'approve_votes': approve_votes,
        'consensus_reached': consensus_reached,
        'vote_fraction': approve_votes / n_agents,
    }

    if consensus_reached:
        return proposed_value, state_info
    else:
        return None, state_info


def calculate_consensus_quality(
    votes: List[Any],
    weights: Optional[List[float]] = None,
) -> Dict[str, float]:
    """
    Calculate quality metrics for a consensus decision.

    Args:
        votes: List of votes from agents
        weights: Optional weights for each vote

    Returns:
        dict: Quality metrics including agreement, entropy, etc.
    """
    if not votes:
        return {
            'agreement': 0.0,
            'entropy': 0.0,
            'diversity': 0.0,
            'n_votes': 0,
        }

    vote_counts = Counter(votes)
    n_votes = len(votes)
    n_options = len(vote_counts)

    # Calculate agreement (fraction voting for winner)
    winner_count = vote_counts.most_common(1)[0][1]
    agreement = winner_count / n_votes

    # Calculate entropy (measure of disagreement)
    probabilities = np.array([count / n_votes for count in vote_counts.values()])
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

    # Normalize entropy by maximum possible (log2 of number of options)
    max_entropy = np.log2(n_options) if n_options > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Diversity (how many different options were voted for)
    diversity = n_options / n_votes

    metrics = {
        'agreement': agreement,
        'entropy': entropy,
        'normalized_entropy': normalized_entropy,
        'diversity': diversity,
        'n_votes': n_votes,
        'n_options': n_options,
    }

    # If weights are provided, calculate weighted agreement
    if weights is not None and len(weights) == len(votes):
        total_weight = sum(weights)
        if total_weight > 0:
            winner = vote_counts.most_common(1)[0][0]
            winner_weight = sum(w for v, w in zip(votes, weights) if v == winner)
            metrics['weighted_agreement'] = winner_weight / total_weight

    return metrics
