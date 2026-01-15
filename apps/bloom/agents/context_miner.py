"""
Context Miner Agent - Collaboration Data Engineer

The Context Miner analyzes collaboration patterns to suggest peer reviewers.

Responsibilities:
- Connect to Calendar, Jira, Git, and other data sources
- Analyze collaboration patterns and relationship strength
- Auto-populate suggested peer lists based on interaction metrics
- Calculate relationship scores using graph analysis
- Track collaboration trends over time

Design Pattern: ETL Pipeline + Graph Analytics
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import numpy as np
from loguru import logger

from apps.bloom.models.employee import Employee
from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore
from iras.databases.graph_store import GraphStore
from iras.math.graph_analysis import (
    AgentNetwork,
    calculate_centrality,
    calculate_clustering_coefficient,
)


class CollaborationMetrics:
    """Collaboration metrics for a pair of employees"""

    def __init__(self):
        self.calendar_meetings: int = 0
        self.jira_interactions: int = 0
        self.git_collaborations: int = 0
        self.slack_messages: int = 0
        self.total_score: float = 0.0

    def calculate_score(self) -> float:
        """
        Calculate overall collaboration strength score

        Weighted combination of different interaction types
        """
        # Weights for different interaction types
        weights = {
            "calendar": 0.3,
            "jira": 0.25,
            "git": 0.25,
            "slack": 0.2,
        }

        # Normalize counts (cap at 50 to avoid outliers)
        normalized = {
            "calendar": min(self.calendar_meetings / 50.0, 1.0),
            "jira": min(self.jira_interactions / 100.0, 1.0),
            "git": min(self.git_collaborations / 50.0, 1.0),
            "slack": min(self.slack_messages / 200.0, 1.0),
        }

        self.total_score = sum(normalized[k] * weights[k] for k in weights.keys())
        return self.total_score


class ContextMiner(Agent):
    """
    Data engineering agent for collaboration analysis

    The Context Miner connects to various data sources and builds
    a relationship graph to identify strong collaboration patterns.

    Capabilities:
    - Multi-source data integration (Calendar, Jira, Git, Slack)
    - Relationship strength calculation
    - Peer suggestion generation
    - Collaboration trend analysis
    - Graph-based network analysis
    """

    def __init__(
        self,
        name: str = "ContextMiner",
        document_store: Optional[DocumentStore] = None,
        graph_store: Optional[GraphStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="data_engineer",
            capabilities={
                "data_integration",
                "graph_analysis",
                "peer_suggestion",
                "relationship_scoring",
                "trend_analysis",
            },
            temperature=0.2,  # Deterministic for data analysis
            max_tokens=3000,
        )
        super().__init__(config)

        # Database connections
        self.document_store = document_store or DocumentStore()
        self.graph_store = graph_store or GraphStore(directed=False)

        # Data source configurations
        self.data_sources = {
            "calendar": {"enabled": True, "weight": 0.3},
            "jira": {"enabled": True, "weight": 0.25},
            "git": {"enabled": True, "weight": 0.25},
            "slack": {"enabled": True, "weight": 0.2},
        }

        # Cache for collaboration data
        self.collaboration_cache: Dict[Tuple[UUID, UUID], CollaborationMetrics] = {}
        self.cache_expiry = timedelta(hours=24)
        self.last_cache_refresh = datetime.now()

        # Register tools
        self._register_mining_tools()

        logger.info(f"ContextMiner '{name}' initialized with {len(self.data_sources)} data sources")

    def _register_mining_tools(self) -> None:
        """Register Context Miner specific tools"""
        self.register_tool(
            AgentTool(
                name="suggest_peers",
                description="Generate peer reviewer suggestions for employee",
                parameters={
                    "employee_id": {"type": "string"},
                    "count": {"type": "integer"},
                },
                function=self.suggest_peers,
            )
        )

        self.register_tool(
            AgentTool(
                name="calculate_relationship_strength",
                description="Calculate relationship strength between two employees",
                parameters={
                    "employee_a_id": {"type": "string"},
                    "employee_b_id": {"type": "string"},
                },
                function=self.calculate_relationship_strength,
            )
        )

        self.register_tool(
            AgentTool(
                name="analyze_collaboration_network",
                description="Analyze overall collaboration network",
                parameters={},
                function=self.analyze_collaboration_network,
            )
        )

    async def suggest_peers(
        self,
        employee_id: UUID,
        count: int = 5,
        time_window_days: int = 180,
    ) -> Dict[str, Any]:
        """
        Generate peer reviewer suggestions based on collaboration patterns

        Args:
            employee_id: Employee to generate suggestions for
            count: Number of peers to suggest
            time_window_days: Look back window in days

        Returns:
            Suggested peers with scores and justifications
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Generating peer suggestions for employee {employee_id}",
        )

        try:
            # Load employee data
            employee_doc = await self.document_store.find_by_id(
                collection="employees",
                doc_id=str(employee_id),
            )

            if not employee_doc:
                raise ValueError(f"Employee not found: {employee_id}")

            # Get all potential peers (same or adjacent level)
            employee_level = employee_doc.get("level", "L3")
            potential_peers = await self._get_potential_peers(employee_id, employee_level)

            logger.info(f"Found {len(potential_peers)} potential peers for {employee_id}")

            # Calculate collaboration scores for each potential peer
            peer_scores: List[Tuple[UUID, float, Dict[str, Any]]] = []

            for peer_id in potential_peers:
                # Calculate relationship strength
                strength = await self.calculate_relationship_strength(
                    employee_id,
                    peer_id,
                    time_window_days,
                )

                if strength["total_score"] > 0.1:  # Minimum threshold
                    peer_scores.append(
                        (
                            peer_id,
                            strength["total_score"],
                            strength["breakdown"],
                        )
                    )

            # Sort by score and take top N
            peer_scores.sort(key=lambda x: x[1], reverse=True)
            top_peers = peer_scores[:count]

            # Build suggestions with justifications
            suggestions = []
            for peer_id, score, breakdown in top_peers:
                peer_doc = await self.document_store.find_by_id(
                    collection="employees",
                    doc_id=str(peer_id),
                )

                justification = self._generate_justification(breakdown)

                suggestions.append(
                    {
                        "peer_id": str(peer_id),
                        "peer_name": peer_doc.get("name", "Unknown") if peer_doc else "Unknown",
                        "score": score,
                        "justification": justification,
                        "breakdown": breakdown,
                    }
                )

            # Store in graph
            for peer_id, score, _ in top_peers:
                await self.graph_store.add_edge(
                    source=str(employee_id),
                    target=str(peer_id),
                    edge_type="collaboration",
                    weight=score,
                    properties={
                        "suggested_at": datetime.now().isoformat(),
                        "score": score,
                    },
                )

            # Add evidence to reasoning
            await self.reasoning.add_evidence(
                content=f"Generated {len(suggestions)} peer suggestions based on collaboration analysis",
                evidence_type=EvidenceType.STATISTICAL,
                confidence=0.85,
                source=f"context_miner_{self.id}",
            )

            # Remember in memory
            await self.memory.remember(
                content={
                    "action": "peer_suggestions",
                    "employee_id": str(employee_id),
                    "suggestions_count": len(suggestions),
                    "avg_score": np.mean([s["score"] for s in suggestions]) if suggestions else 0,
                },
                importance=0.8,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Generated {len(suggestions)} peer suggestions for employee {employee_id}"
            )

            return {
                "employee_id": str(employee_id),
                "suggestions": suggestions,
                "total_candidates_analyzed": len(potential_peers),
                "time_window_days": time_window_days,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate peer suggestions: {e}")
            raise

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def calculate_relationship_strength(
        self,
        employee_a_id: UUID,
        employee_b_id: UUID,
        time_window_days: int = 180,
    ) -> Dict[str, Any]:
        """
        Calculate relationship strength between two employees

        Args:
            employee_a_id: First employee
            employee_b_id: Second employee
            time_window_days: Look back window

        Returns:
            Relationship strength score and breakdown
        """
        # Check cache
        cache_key = tuple(sorted([employee_a_id, employee_b_id]))
        if cache_key in self.collaboration_cache:
            cached = self.collaboration_cache[cache_key]
            return {
                "total_score": cached.total_score,
                "breakdown": {
                    "calendar_meetings": cached.calendar_meetings,
                    "jira_interactions": cached.jira_interactions,
                    "git_collaborations": cached.git_collaborations,
                    "slack_messages": cached.slack_messages,
                },
            }

        metrics = CollaborationMetrics()

        # Fetch collaboration data from each source
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_window_days)

        # Calendar data (simulated)
        if self.data_sources["calendar"]["enabled"]:
            metrics.calendar_meetings = await self._fetch_calendar_interactions(
                employee_a_id, employee_b_id, start_date, end_date
            )

        # Jira data (simulated)
        if self.data_sources["jira"]["enabled"]:
            metrics.jira_interactions = await self._fetch_jira_interactions(
                employee_a_id, employee_b_id, start_date, end_date
            )

        # Git data (simulated)
        if self.data_sources["git"]["enabled"]:
            metrics.git_collaborations = await self._fetch_git_collaborations(
                employee_a_id, employee_b_id, start_date, end_date
            )

        # Slack data (simulated)
        if self.data_sources["slack"]["enabled"]:
            metrics.slack_messages = await self._fetch_slack_interactions(
                employee_a_id, employee_b_id, start_date, end_date
            )

        # Calculate total score
        total_score = metrics.calculate_score()

        # Cache result
        self.collaboration_cache[cache_key] = metrics

        return {
            "total_score": total_score,
            "breakdown": {
                "calendar_meetings": metrics.calendar_meetings,
                "jira_interactions": metrics.jira_interactions,
                "git_collaborations": metrics.git_collaborations,
                "slack_messages": metrics.slack_messages,
            },
        }

    async def analyze_collaboration_network(
        self,
        min_edge_weight: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Analyze the overall collaboration network

        Args:
            min_edge_weight: Minimum edge weight to include

        Returns:
            Network analysis results
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason="Analyzing collaboration network",
        )

        try:
            # Get network statistics from graph store
            graph_stats = self.graph_store.get_statistics()

            # Calculate centrality for key players
            centrality = await self.graph_store.get_centrality(
                algorithm="pagerank",
                node_type="employee",
            )

            # Get top influencers
            top_influencers = sorted(
                centrality.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            # Detect communities
            communities = await self.graph_store.detect_communities(
                algorithm="louvain"
            )

            community_sizes = defaultdict(int)
            for node, community_id in communities.items():
                community_sizes[community_id] += 1

            logger.info(
                f"Network analysis complete: {graph_stats['num_nodes']} nodes, "
                f"{graph_stats['num_edges']} edges, {len(community_sizes)} communities"
            )

            return {
                "network_stats": graph_stats,
                "top_influencers": [
                    {"employee_id": emp_id, "centrality": score}
                    for emp_id, score in top_influencers
                ],
                "num_communities": len(community_sizes),
                "largest_community_size": max(community_sizes.values()) if community_sizes else 0,
                "analyzed_at": datetime.now().isoformat(),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _get_potential_peers(
        self,
        employee_id: UUID,
        employee_level: str,
    ) -> List[UUID]:
        """Get list of potential peer reviewers"""
        # Query employees at same or adjacent levels
        # Exclude the employee themselves and their direct manager
        employees = await self.document_store.find(
            collection="employees",
            query={
                "_id": {"$ne": str(employee_id)},
                # In production, add level filtering
            },
        )

        return [UUID(emp["_id"]) for emp in employees]

    async def _fetch_calendar_interactions(
        self,
        emp_a: UUID,
        emp_b: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """
        Fetch calendar meeting interactions (simulated)

        In production, integrate with Google Calendar / Outlook API
        """
        # Simulated: Generate random but consistent count based on employee IDs
        seed = hash((str(emp_a), str(emp_b))) % 100
        np.random.seed(seed)
        return int(np.random.poisson(lam=15))

    async def _fetch_jira_interactions(
        self,
        emp_a: UUID,
        emp_b: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """
        Fetch Jira ticket interactions (simulated)

        In production, integrate with Jira API
        """
        seed = hash((str(emp_a), str(emp_b), "jira")) % 100
        np.random.seed(seed)
        return int(np.random.poisson(lam=25))

    async def _fetch_git_collaborations(
        self,
        emp_a: UUID,
        emp_b: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """
        Fetch Git PR collaborations (simulated)

        In production, integrate with GitHub/GitLab API
        """
        seed = hash((str(emp_a), str(emp_b), "git")) % 100
        np.random.seed(seed)
        return int(np.random.poisson(lam=10))

    async def _fetch_slack_interactions(
        self,
        emp_a: UUID,
        emp_b: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """
        Fetch Slack message interactions (simulated)

        In production, integrate with Slack API
        """
        seed = hash((str(emp_a), str(emp_b), "slack")) % 100
        np.random.seed(seed)
        return int(np.random.poisson(lam=40))

    def _generate_justification(self, breakdown: Dict[str, int]) -> str:
        """Generate human-readable justification for peer suggestion"""
        parts = []

        if breakdown["calendar_meetings"] > 20:
            parts.append(f"{breakdown['calendar_meetings']} shared meetings")
        elif breakdown["calendar_meetings"] > 10:
            parts.append(f"frequent meeting collaboration ({breakdown['calendar_meetings']} meetings)")

        if breakdown["jira_interactions"] > 30:
            parts.append(f"{breakdown['jira_interactions']} Jira collaborations")
        elif breakdown["jira_interactions"] > 15:
            parts.append(f"regular Jira interactions ({breakdown['jira_interactions']})")

        if breakdown["git_collaborations"] > 15:
            parts.append(f"{breakdown['git_collaborations']} code collaborations")
        elif breakdown["git_collaborations"] > 5:
            parts.append(f"code review partnership ({breakdown['git_collaborations']} PRs)")

        if breakdown["slack_messages"] > 50:
            parts.append("high communication frequency")

        if not parts:
            parts.append("consistent collaboration across multiple channels")

        return "Strong collaboration: " + ", ".join(parts)

    async def refresh_collaboration_cache(self) -> None:
        """Refresh the collaboration data cache"""
        logger.info("Refreshing collaboration cache")
        self.collaboration_cache.clear()
        self.last_cache_refresh = datetime.now()
