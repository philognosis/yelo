"""
Tests for ContextMiner Agent

Tests peer suggestion, relationship strength calculation,
collaboration network analysis, and graph integration.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from bloom.agents.context_miner import CollaborationMetrics, ContextMiner


class TestContextMiner:
    """Test ContextMiner basic functionality"""

    @pytest.mark.asyncio
    async def test_context_miner_initialization(self, mock_context_miner):
        """Test ContextMiner initializes correctly"""
        assert mock_context_miner.config.name == "ContextMiner"
        assert "peer_suggestion" in mock_context_miner.config.capabilities
        assert "graph_analysis" in mock_context_miner.config.capabilities

    @pytest.mark.asyncio
    async def test_data_sources_configured(self, mock_context_miner):
        """Test data sources are configured"""
        assert "calendar" in mock_context_miner.data_sources
        assert "jira" in mock_context_miner.data_sources
        assert "git" in mock_context_miner.data_sources
        assert "slack" in mock_context_miner.data_sources

        # Check weights
        total_weight = sum(
            source["weight"] for source in mock_context_miner.data_sources.values()
        )
        assert 0.9 < total_weight <= 1.0


class TestCollaborationMetrics:
    """Test collaboration metrics calculation"""

    def test_collaboration_metrics_creation(self):
        """Test creating collaboration metrics"""
        metrics = CollaborationMetrics()
        assert metrics.calendar_meetings == 0
        assert metrics.jira_interactions == 0
        assert metrics.git_collaborations == 0
        assert metrics.slack_messages == 0
        assert metrics.total_score == 0.0

    def test_collaboration_score_calculation(self):
        """Test calculating collaboration score"""
        metrics = CollaborationMetrics()
        metrics.calendar_meetings = 25
        metrics.jira_interactions = 50
        metrics.git_collaborations = 25
        metrics.slack_messages = 100

        score = metrics.calculate_score()

        assert 0 <= score <= 1.0
        assert score > 0  # Should have positive score

    def test_collaboration_score_normalization(self):
        """Test that very high numbers are normalized"""
        metrics = CollaborationMetrics()
        metrics.calendar_meetings = 1000  # Way above cap
        metrics.jira_interactions = 1000
        metrics.git_collaborations = 1000
        metrics.slack_messages = 1000

        score = metrics.calculate_score()

        # Should be capped at 1.0
        assert score <= 1.0

    def test_collaboration_score_weighted(self):
        """Test that different sources have different weights"""
        # Calendar only
        calendar_metrics = CollaborationMetrics()
        calendar_metrics.calendar_meetings = 50

        # Jira only
        jira_metrics = CollaborationMetrics()
        jira_metrics.jira_interactions = 100

        calendar_score = calendar_metrics.calculate_score()
        jira_score = jira_metrics.calculate_score()

        # Both should contribute to score
        assert calendar_score > 0
        assert jira_score > 0


class TestPeerSuggestion:
    """Test peer reviewer suggestion"""

    @pytest.mark.asyncio
    async def test_suggest_peers_simple(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test basic peer suggestion"""
        # Mock employee data
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()

        # Mock potential peers
        mock_document_store.find.return_value = [
            {"_id": str(uuid4()), "level": "L3"} for _ in range(10)
        ]

        result = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=5,
        )

        assert "suggestions" in result
        assert result["employee_id"] == str(mock_employee.person.id)
        assert "total_candidates_analyzed" in result

    @pytest.mark.asyncio
    async def test_suggest_peers_with_scores(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test peer suggestions include scores"""
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()
        mock_document_store.find.return_value = [
            {"_id": str(uuid4()), "name": f"Peer {i}", "level": "L3"}
            for i in range(5)
        ]

        result = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=3,
        )

        # Each suggestion should have score
        if result["suggestions"]:
            suggestion = result["suggestions"][0]
            assert "score" in suggestion
            assert "justification" in suggestion
            assert "breakdown" in suggestion

    @pytest.mark.asyncio
    async def test_suggest_peers_sorted_by_score(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test peers are sorted by collaboration score"""
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()
        mock_document_store.find.return_value = [
            {"_id": str(uuid4()), "level": "L3"} for _ in range(10)
        ]

        result = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=5,
        )

        if len(result["suggestions"]) > 1:
            # Verify descending order
            scores = [s["score"] for s in result["suggestions"]]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_suggest_peers_minimum_threshold(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test that peers below threshold are filtered out"""
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()
        mock_document_store.find.return_value = [
            {"_id": str(uuid4()), "level": "L3"}
        ]

        result = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=5,
        )

        # All suggestions should have score > 0.1 (minimum threshold)
        for suggestion in result["suggestions"]:
            assert suggestion["score"] > 0.1

    @pytest.mark.asyncio
    async def test_suggest_peers_employee_not_found(
        self, mock_context_miner, mock_document_store
    ):
        """Test error when employee not found"""
        mock_document_store.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Employee not found"):
            await mock_context_miner.suggest_peers(
                employee_id=uuid4(),
                count=5,
            )


class TestRelationshipStrength:
    """Test relationship strength calculation"""

    @pytest.mark.asyncio
    async def test_calculate_relationship_strength(self, mock_context_miner):
        """Test calculating relationship strength between two employees"""
        emp_a = uuid4()
        emp_b = uuid4()

        result = await mock_context_miner.calculate_relationship_strength(
            employee_a_id=emp_a,
            employee_b_id=emp_b,
            time_window_days=180,
        )

        assert "total_score" in result
        assert "breakdown" in result
        assert 0 <= result["total_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_relationship_strength_breakdown(self, mock_context_miner):
        """Test breakdown includes all data sources"""
        result = await mock_context_miner.calculate_relationship_strength(
            employee_a_id=uuid4(),
            employee_b_id=uuid4(),
        )

        breakdown = result["breakdown"]
        assert "calendar_meetings" in breakdown
        assert "jira_interactions" in breakdown
        assert "git_collaborations" in breakdown
        assert "slack_messages" in breakdown

    @pytest.mark.asyncio
    async def test_relationship_strength_caching(self, mock_context_miner):
        """Test that relationship strength is cached"""
        emp_a = uuid4()
        emp_b = uuid4()

        # First call
        result1 = await mock_context_miner.calculate_relationship_strength(
            emp_a, emp_b
        )

        # Second call (should use cache)
        result2 = await mock_context_miner.calculate_relationship_strength(
            emp_a, emp_b
        )

        assert result1["total_score"] == result2["total_score"]

    @pytest.mark.asyncio
    async def test_relationship_strength_symmetric(self, mock_context_miner):
        """Test relationship strength is symmetric (A->B == B->A)"""
        emp_a = uuid4()
        emp_b = uuid4()

        result_ab = await mock_context_miner.calculate_relationship_strength(
            emp_a, emp_b
        )
        result_ba = await mock_context_miner.calculate_relationship_strength(
            emp_b, emp_a
        )

        # Should be same (cached)
        assert result_ab["total_score"] == result_ba["total_score"]


class TestCollaborationNetwork:
    """Test collaboration network analysis"""

    @pytest.mark.asyncio
    async def test_analyze_collaboration_network(
        self, mock_context_miner, mock_graph_store
    ):
        """Test analyzing overall collaboration network"""
        # Mock network stats
        mock_graph_store.get_statistics.return_value = {
            "num_nodes": 100,
            "num_edges": 450,
        }
        mock_graph_store.get_centrality.return_value = {
            str(uuid4()): 0.95,
            str(uuid4()): 0.87,
            str(uuid4()): 0.76,
        }
        mock_graph_store.detect_communities.return_value = {
            str(uuid4()): 1,
            str(uuid4()): 1,
            str(uuid4()): 2,
        }

        result = await mock_context_miner.analyze_collaboration_network()

        assert "network_stats" in result
        assert "top_influencers" in result
        assert "num_communities" in result

    @pytest.mark.asyncio
    async def test_network_top_influencers(
        self, mock_context_miner, mock_graph_store
    ):
        """Test top influencers are identified"""
        # Mock centrality scores
        influencers = {str(uuid4()): score for score in [0.95, 0.87, 0.76, 0.65, 0.54]}
        mock_graph_store.get_centrality.return_value = influencers
        mock_graph_store.get_statistics.return_value = {"num_nodes": 50, "num_edges": 200}
        mock_graph_store.detect_communities.return_value = {}

        result = await mock_context_miner.analyze_collaboration_network()

        # Should return top influencers sorted by centrality
        assert len(result["top_influencers"]) <= 10
        if len(result["top_influencers"]) > 1:
            centralities = [inf["centrality"] for inf in result["top_influencers"]]
            assert centralities == sorted(centralities, reverse=True)

    @pytest.mark.asyncio
    async def test_network_community_detection(
        self, mock_context_miner, mock_graph_store
    ):
        """Test community detection in network"""
        # Mock communities
        communities = {
            str(uuid4()): 1 for _ in range(20)
        }
        communities.update({str(uuid4()): 2 for _ in range(15)})
        communities.update({str(uuid4()): 3 for _ in range(10)})

        mock_graph_store.detect_communities.return_value = communities
        mock_graph_store.get_statistics.return_value = {"num_nodes": 45, "num_edges": 180}
        mock_graph_store.get_centrality.return_value = {}

        result = await mock_context_miner.analyze_collaboration_network()

        assert result["num_communities"] == 3
        assert result["largest_community_size"] == 20


class TestComplexScenarios:
    """Complex test scenarios"""

    @pytest.mark.asyncio
    async def test_suggest_peers_with_time_window(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test peer suggestion with different time windows"""
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()
        mock_document_store.find.return_value = [
            {"_id": str(uuid4()), "level": "L3"} for _ in range(5)
        ]

        # 30 days
        result_30 = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=5,
            time_window_days=30,
        )

        # 180 days
        result_180 = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=5,
            time_window_days=180,
        )

        # Both should return results
        assert "suggestions" in result_30
        assert "suggestions" in result_180

    @pytest.mark.asyncio
    async def test_cross_team_collaboration_detection(
        self, mock_context_miner, mock_document_store, mock_employee
    ):
        """Test detecting cross-team collaboration patterns"""
        mock_document_store.find_by_id.return_value = mock_employee.model_dump()

        # Mock peers from different teams
        peers = [
            {"_id": str(uuid4()), "level": "L3", "team": f"Team {i % 3}"}
            for i in range(15)
        ]
        mock_document_store.find.return_value = peers

        result = await mock_context_miner.suggest_peers(
            employee_id=mock_employee.person.id,
            count=10,
        )

        # Should suggest peers from multiple teams
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_justification_generation(self, mock_context_miner):
        """Test generating human-readable justifications"""
        breakdown = {
            "calendar_meetings": 25,
            "jira_interactions": 60,
            "git_collaborations": 20,
            "slack_messages": 80,
        }

        justification = mock_context_miner._generate_justification(breakdown)

        assert isinstance(justification, str)
        assert len(justification) > 0
        assert "collaboration" in justification.lower()
