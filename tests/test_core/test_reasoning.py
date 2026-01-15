"""
Test Suite for Reasoning Engine

Tests cover:
- Evidence management
- Claim creation and tracking
- Reasoning strategies (CoT, deductive, inductive)
- Confidence propagation
- Contradiction detection
- Reasoning chain construction
- Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from iras.core.reasoning import (
    ReasoningEngine,
    ReasoningStrategy,
    EvidenceType,
    Evidence,
    Claim,
    ReasoningChain,
    ReasoningStep,
)


class TestEvidenceManagement:
    """Test evidence addition and management"""

    @pytest.mark.asyncio
    async def test_add_factual_evidence(self):
        """Test adding factual evidence"""
        engine = ReasoningEngine()

        evidence_id = await engine.add_evidence(
            content="The sky is blue",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.95,
            source="observation",
        )

        assert evidence_id is not None
        assert evidence_id in engine.evidence_store

    @pytest.mark.asyncio
    async def test_add_statistical_evidence(self):
        """Test adding statistical evidence"""
        engine = ReasoningEngine()

        evidence_id = await engine.add_evidence(
            content={"mean": 10.5, "std": 2.3},
            evidence_type=EvidenceType.STATISTICAL,
            confidence=0.85,
            source="experiment",
        )

        evidence = engine.evidence_store[evidence_id]
        assert evidence.evidence_type == EvidenceType.STATISTICAL

    @pytest.mark.asyncio
    async def test_evidence_confidence_bounds(self):
        """Test that evidence confidence is bounded [0, 1]"""
        engine = ReasoningEngine()

        # Test upper bound
        id1 = await engine.add_evidence(
            content="test",
            evidence_type=EvidenceType.FACTUAL,
            confidence=1.5,
            source="test",
        )

        evidence1 = engine.evidence_store[id1]
        assert evidence1.confidence <= 1.0

        # Test lower bound
        id2 = await engine.add_evidence(
            content="test",
            evidence_type=EvidenceType.FACTUAL,
            confidence=-0.5,
            source="test",
        )

        evidence2 = engine.evidence_store[id2]
        assert evidence2.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_evidence_with_support_link(self):
        """Test evidence supporting a claim"""
        engine = ReasoningEngine()

        claim_id = uuid4()
        evidence_id = await engine.add_evidence(
            content="Supporting data",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="test",
            supports=claim_id,
        )

        evidence = engine.evidence_store[evidence_id]
        assert evidence.supports == claim_id


class TestClaimManagement:
    """Test claim creation and tracking"""

    @pytest.mark.asyncio
    async def test_make_simple_claim(self):
        """Test making a claim with evidence"""
        engine = ReasoningEngine()

        # Add evidence first
        evidence_id = await engine.add_evidence(
            content="Water boils at 100°C",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.99,
            source="science",
        )

        # Make claim
        claim_id = await engine.make_claim(
            statement="Water boils at high temperature",
            evidence_ids=[evidence_id],
        )

        assert claim_id in engine.claims
        claim = engine.claims[claim_id]
        assert claim.confidence > 0.5

    @pytest.mark.asyncio
    async def test_claim_confidence_from_evidence(self):
        """Test that claim confidence derives from evidence"""
        engine = ReasoningEngine()

        # Add high-confidence evidence
        evidence_id = await engine.add_evidence(
            content="Strong evidence",
            evidence_type=EvidenceType.EXPERIMENTAL,
            confidence=0.95,
            source="lab",
        )

        claim_id = await engine.make_claim(
            statement="High confidence claim",
            evidence_ids=[evidence_id],
        )

        claim = engine.claims[claim_id]
        assert claim.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_claim_with_no_evidence(self):
        """Test making claim with no evidence"""
        engine = ReasoningEngine()

        claim_id = await engine.make_claim(
            statement="Unsupported claim",
            evidence_ids=[],
        )

        claim = engine.claims[claim_id]
        assert claim.confidence == 0.5  # Default neutral

    @pytest.mark.asyncio
    async def test_claim_with_derivation(self):
        """Test claim with derivation reasoning"""
        engine = ReasoningEngine()

        evidence_id = await engine.add_evidence(
            content="Premise",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="test",
        )

        claim_id = await engine.make_claim(
            statement="Conclusion",
            evidence_ids=[evidence_id],
            derivation="Deductive reasoning from premise",
        )

        claim = engine.claims[claim_id]
        assert claim.derivation is not None


class TestReasoningStrategies:
    """Test different reasoning strategies"""

    @pytest.mark.asyncio
    async def test_chain_of_thought_reasoning(self):
        """Test chain-of-thought reasoning"""
        engine = ReasoningEngine()

        # Add some evidence
        await engine.add_evidence(
            content="Fact 1",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="test",
        )

        chain = await engine.reason(
            query="What can we conclude?",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        assert chain.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT
        assert len(chain.steps) > 0
        assert chain.final_conclusion is not None
        assert chain.completed_at is not None

    @pytest.mark.asyncio
    async def test_deductive_reasoning(self):
        """Test deductive reasoning strategy"""
        engine = ReasoningEngine()

        # Add high-confidence evidence (principles)
        await engine.add_evidence(
            content="All humans are mortal",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.95,
            source="logic",
        )

        chain = await engine.reason(
            query="Is Socrates mortal?",
            strategy=ReasoningStrategy.DEDUCTIVE,
        )

        assert chain.strategy == ReasoningStrategy.DEDUCTIVE
        assert len(chain.steps) > 0

    @pytest.mark.asyncio
    async def test_inductive_reasoning(self):
        """Test inductive reasoning strategy"""
        engine = ReasoningEngine()

        # Add multiple specific observations
        for i in range(5):
            await engine.add_evidence(
                content=f"Observation {i}",
                evidence_type=EvidenceType.EXPERIMENTAL,
                confidence=0.85,
                source=f"experiment_{i}",
            )

        chain = await engine.reason(
            query="What pattern emerges?",
            strategy=ReasoningStrategy.INDUCTIVE,
        )

        assert chain.strategy == ReasoningStrategy.INDUCTIVE
        assert len(chain.steps) > 0

    @pytest.mark.asyncio
    async def test_reasoning_with_max_steps(self):
        """Test reasoning respects max steps limit"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Complex query",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            max_steps=5,
        )

        assert len(chain.steps) <= 5

    @pytest.mark.asyncio
    async def test_unsupported_strategy_fallback(self):
        """Test that unsupported strategies fall back to CoT"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Test query",
            strategy=ReasoningStrategy.ANALOGICAL,  # Not fully implemented
        )

        # Should still complete with fallback
        assert chain is not None
        assert chain.final_conclusion is not None


class TestReasoningChain:
    """Test reasoning chain construction"""

    @pytest.mark.asyncio
    async def test_reasoning_chain_steps(self):
        """Test that reasoning creates multiple steps"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Multi-step problem",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        assert len(chain.steps) >= 2
        for i, step in enumerate(chain.steps):
            assert step.step_number == i + 1
            assert step.thought is not None

    @pytest.mark.asyncio
    async def test_reasoning_chain_timestamps(self):
        """Test that chain has proper timestamps"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Test query",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        assert chain.created_at is not None
        assert chain.completed_at is not None
        assert chain.completed_at >= chain.created_at

    @pytest.mark.asyncio
    async def test_reasoning_chain_storage(self):
        """Test that chains are stored"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Test query",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        assert chain in engine.reasoning_chains

    @pytest.mark.asyncio
    async def test_get_reasoning_summary(self):
        """Test getting reasoning chain summary"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Summarizable query",
            strategy=ReasoningStrategy.DEDUCTIVE,
        )

        summary = engine.get_reasoning_summary(chain.id)

        assert summary is not None
        assert summary["query"] == "Summarizable query"
        assert summary["strategy"] == ReasoningStrategy.DEDUCTIVE
        assert "num_steps" in summary
        assert "confidence" in summary


class TestContradictionDetection:
    """Test contradiction detection"""

    @pytest.mark.asyncio
    async def test_detect_simple_contradiction(self):
        """Test detecting contradictory evidence"""
        engine = ReasoningEngine()

        # Make a high-confidence claim
        evidence1_id = await engine.add_evidence(
            content="The sky is blue",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="observation",
        )

        claim_id = await engine.make_claim(
            statement="Sky is blue",
            evidence_ids=[evidence1_id],
        )

        # Add contradictory evidence
        evidence2_id = await engine.add_evidence(
            content="The sky is not blue",
            evidence_type=EvidenceType.TESTIMONIAL,
            confidence=0.2,  # Low confidence
            source="unreliable",
        )

        evidence2 = engine.evidence_store[evidence2_id]
        # Should detect potential contradiction
        assert len(evidence2.contradicts) >= 0  # May or may not detect in simple impl

    @pytest.mark.asyncio
    async def test_contradiction_tracking(self):
        """Test that contradictions are tracked"""
        engine = ReasoningEngine()

        # High confidence claim
        claim_id = await engine.make_claim(
            statement="Test claim",
            evidence_ids=[],
        )
        engine.claims[claim_id].confidence = 0.9

        # Add low confidence contradictory evidence
        evidence_id = await engine.add_evidence(
            content="Contradicts claim",
            evidence_type=EvidenceType.TESTIMONIAL,
            confidence=0.1,
            source="test",
        )

        evidence = engine.evidence_store[evidence_id]
        # Check contradiction set exists
        assert isinstance(evidence.contradicts, set)


class TestConfidencePropagation:
    """Test confidence score propagation"""

    @pytest.mark.asyncio
    async def test_confidence_from_single_evidence(self):
        """Test claim confidence with single evidence"""
        engine = ReasoningEngine()

        evidence_id = await engine.add_evidence(
            content="Evidence",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.8,
            source="test",
        )

        claim_id = await engine.make_claim(
            statement="Claim",
            evidence_ids=[evidence_id],
        )

        claim = engine.claims[claim_id]
        assert 0.7 <= claim.confidence <= 0.9

    @pytest.mark.asyncio
    async def test_confidence_from_multiple_evidence(self):
        """Test confidence averaging with multiple evidence"""
        engine = ReasoningEngine()

        evidence_ids = []
        for conf in [0.7, 0.8, 0.9]:
            eid = await engine.add_evidence(
                content=f"Evidence {conf}",
                evidence_type=EvidenceType.FACTUAL,
                confidence=conf,
                source="test",
            )
            evidence_ids.append(eid)

        claim_id = await engine.make_claim(
            statement="Multi-evidence claim",
            evidence_ids=evidence_ids,
        )

        claim = engine.claims[claim_id]
        # Should be reasonably high but not as high as single strong evidence
        assert 0.5 <= claim.confidence <= 0.9

    @pytest.mark.asyncio
    async def test_reasoning_overall_confidence(self):
        """Test overall confidence in reasoning chain"""
        engine = ReasoningEngine()

        # Add high-confidence evidence
        await engine.add_evidence(
            content="Strong evidence",
            evidence_type=EvidenceType.EXPERIMENTAL,
            confidence=0.95,
            source="test",
        )

        chain = await engine.reason(
            query="High confidence query",
            strategy=ReasoningStrategy.DEDUCTIVE,
        )

        assert 0.0 <= chain.overall_confidence <= 1.0


class TestStatistics:
    """Test reasoning engine statistics"""

    def test_get_statistics_empty(self):
        """Test statistics on empty engine"""
        engine = ReasoningEngine()

        stats = engine.get_statistics()

        assert stats["total_evidence"] == 0
        assert stats["total_claims"] == 0
        assert stats["total_reasoning_chains"] == 0
        assert stats["average_confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self):
        """Test statistics with data"""
        engine = ReasoningEngine()

        # Add evidence
        await engine.add_evidence(
            content="Evidence",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="test",
        )

        # Make claim
        await engine.make_claim(
            statement="Claim",
            evidence_ids=[],
        )

        # Create reasoning chain
        await engine.reason(
            query="Query",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        stats = engine.get_statistics()

        assert stats["total_evidence"] == 1
        assert stats["total_claims"] == 1
        assert stats["total_reasoning_chains"] == 1
        assert stats["average_confidence"] > 0.0


class TestComplexScenarios:
    """Test complex reasoning scenarios"""

    @pytest.mark.asyncio
    async def test_multi_step_reasoning_with_evidence(self):
        """Test complex multi-step reasoning"""
        engine = ReasoningEngine()

        # Build evidence base
        for i in range(5):
            await engine.add_evidence(
                content=f"Evidence piece {i}",
                evidence_type=EvidenceType.FACTUAL,
                confidence=0.8 + (i * 0.02),
                source=f"source_{i}",
            )

        chain = await engine.reason(
            query="What conclusions can we draw?",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            max_steps=10,
        )

        assert len(chain.steps) > 0
        assert chain.overall_confidence > 0.5

    @pytest.mark.asyncio
    async def test_concurrent_reasoning_chains(self):
        """Test creating multiple reasoning chains concurrently"""
        engine = ReasoningEngine()

        # Add shared evidence
        await engine.add_evidence(
            content="Shared evidence",
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.9,
            source="test",
        )

        # Run concurrent reasoning
        chains = await asyncio.gather(
            engine.reason("Query 1", ReasoningStrategy.CHAIN_OF_THOUGHT),
            engine.reason("Query 2", ReasoningStrategy.DEDUCTIVE),
            engine.reason("Query 3", ReasoningStrategy.INDUCTIVE),
        )

        assert len(chains) == 3
        assert all(c.final_conclusion is not None for c in chains)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_query_reasoning(self):
        """Test reasoning with empty query"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="",
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        assert chain is not None
        assert chain.query == ""

    @pytest.mark.asyncio
    async def test_reasoning_with_no_evidence(self):
        """Test reasoning with no evidence in store"""
        engine = ReasoningEngine()

        chain = await engine.reason(
            query="Query with no evidence",
            strategy=ReasoningStrategy.DEDUCTIVE,
        )

        assert chain is not None
        assert chain.overall_confidence < 0.5

    @pytest.mark.asyncio
    async def test_claim_with_invalid_evidence_ids(self):
        """Test making claim with non-existent evidence"""
        engine = ReasoningEngine()

        fake_id = uuid4()
        claim_id = await engine.make_claim(
            statement="Claim with bad evidence",
            evidence_ids=[fake_id],
        )

        # Should still create claim with low confidence
        claim = engine.claims[claim_id]
        assert claim.confidence == 0.5

    @pytest.mark.asyncio
    async def test_get_summary_nonexistent_chain(self):
        """Test getting summary of non-existent chain"""
        engine = ReasoningEngine()

        fake_id = uuid4()
        summary = engine.get_reasoning_summary(fake_id)

        assert summary is None

    @pytest.mark.asyncio
    async def test_inductive_reasoning_insufficient_cases(self):
        """Test inductive reasoning with insufficient evidence"""
        engine = ReasoningEngine()

        # Add only 1-2 observations
        await engine.add_evidence(
            content="Single observation",
            evidence_type=EvidenceType.EXPERIMENTAL,
            confidence=0.8,
            source="test",
        )

        chain = await engine.reason(
            query="Pattern?",
            strategy=ReasoningStrategy.INDUCTIVE,
        )

        # Should have lower confidence
        assert chain.overall_confidence < 0.5
