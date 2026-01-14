"""
Fact Checker Agent

Specializes in:
- Fact verification
- Source credibility assessment
- Contradiction detection
- Evidence evaluation
- Cross-referencing
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType, ReasoningStrategy
from iras.core.state import AgentStatus


class FactCheckerAgent(Agent):
    """
    Specialized agent for fact-checking and verification

    Capabilities:
    - Fact verification
    - Source credibility assessment
    - Claim validation
    - Contradiction detection
    - Evidence cross-referencing
    """

    def __init__(self, name: str = "FactChecker"):
        config = AgentConfig(
            name=name,
            role="fact_checker",
            capabilities={
                "fact_verification",
                "source_assessment",
                "claim_validation",
                "contradiction_detection",
                "cross_referencing",
            },
            temperature=0.1,  # Very deterministic for fact-checking
            max_tokens=3000,
        )
        super().__init__(config)

        # Register specialized tools
        self._register_fact_checking_tools()

        # Fact-checking specific state
        self.facts_checked: List[Dict[str, Any]] = []
        self.contradictions_found: List[Dict[str, Any]] = []
        self.verifications_performed = 0

    def _register_fact_checking_tools(self) -> None:
        """Register fact-checking specific tools"""

        # Fact verification tool
        verify_tool = AgentTool(
            name="verify_fact",
            description="Verify a factual claim",
            parameters={
                "claim": {"type": "string", "description": "Claim to verify"},
                "sources": {"type": "array", "description": "Sources to check against"},
            },
            function=self._verify_fact,
        )
        self.register_tool(verify_tool)

        # Contradiction detection tool
        contradiction_tool = AgentTool(
            name="detect_contradictions",
            description="Detect contradictions in statements",
            parameters={
                "statements": {"type": "array", "description": "Statements to check"},
            },
            function=self._detect_contradictions,
        )
        self.register_tool(contradiction_tool)

    async def _verify_fact(
        self,
        claim: str,
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify a factual claim against sources

        Args:
            claim: Claim to verify
            sources: Sources to check against

        Returns:
            Verification result
        """
        self.verifications_performed += 1

        # Simulated fact verification
        # In production, this would use semantic similarity and NLP
        verification = {
            "claim": claim,
            "verdict": "unverified",  # Can be: verified, refuted, unverified
            "confidence": 0.0,
            "supporting_sources": [],
            "contradicting_sources": [],
            "timestamp": datetime.now().isoformat(),
        }

        # Check sources
        supporting_count = 0
        contradicting_count = 0

        for source in sources:
            # Simulated source checking
            # In production: use semantic similarity between claim and source content
            source_supports = hash(claim + str(source.get("url", ""))) % 3

            if source_supports == 0:  # Supports
                verification["supporting_sources"].append(source)
                supporting_count += 1
            elif source_supports == 1:  # Contradicts
                verification["contradicting_sources"].append(source)
                contradicting_count += 1

        # Determine verdict
        total_relevant = supporting_count + contradicting_count

        if total_relevant == 0:
            verification["verdict"] = "unverified"
            verification["confidence"] = 0.0
        elif supporting_count > contradicting_count * 2:
            verification["verdict"] = "verified"
            verification["confidence"] = min(0.95, supporting_count / (total_relevant + 1))
        elif contradicting_count > supporting_count * 2:
            verification["verdict"] = "refuted"
            verification["confidence"] = min(0.95, contradicting_count / (total_relevant + 1))
        else:
            verification["verdict"] = "disputed"
            verification["confidence"] = 0.5

        logger.info(
            f"Fact verification: '{claim[:50]}...' -> {verification['verdict']} "
            f"(confidence: {verification['confidence']:.2f})"
        )

        self.facts_checked.append(verification)

        return verification

    async def _detect_contradictions(
        self,
        statements: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions among statements

        Args:
            statements: Statements to check

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Simulated contradiction detection
        # In production: use semantic similarity and logical analysis
        for i, stmt1 in enumerate(statements):
            for j, stmt2 in enumerate(statements[i + 1 :], start=i + 1):
                # Simple heuristic: if statements are very different, might contradict
                if len(set(stmt1.lower().split()) & set(stmt2.lower().split())) < 2:
                    contradiction = {
                        "statement_1": stmt1,
                        "statement_2": stmt2,
                        "severity": "low",  # low, medium, high
                        "confidence": 0.4,
                    }
                    contradictions.append(contradiction)

        if contradictions:
            self.contradictions_found.extend(contradictions)
            logger.warning(f"Found {len(contradictions)} potential contradictions")
        else:
            logger.info("No contradictions detected")

        return contradictions

    async def verify_claims(
        self,
        claims: List[str],
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify multiple claims against sources

        Args:
            claims: List of claims to verify
            sources: Sources to check against

        Returns:
            Verification results for all claims
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Verifying {len(claims)} claims",
        )

        try:
            results = {
                "total_claims": len(claims),
                "verifications": [],
                "summary": {
                    "verified": 0,
                    "refuted": 0,
                    "disputed": 0,
                    "unverified": 0,
                },
                "overall_reliability": 0.0,
                "timestamp": datetime.now().isoformat(),
            }

            # Verify each claim
            for claim in claims:
                verification = await self._verify_fact(claim, sources)
                results["verifications"].append(verification)

                # Update summary
                verdict = verification["verdict"]
                results["summary"][verdict] = results["summary"].get(verdict, 0) + 1

                # Add evidence to reasoning engine
                await self.reasoning.add_evidence(
                    content=f"Claim '{claim[:50]}...' was {verdict}",
                    evidence_type=EvidenceType.FACTUAL,
                    confidence=verification["confidence"],
                    source=f"fact_checker_{self.id}",
                )

            # Calculate overall reliability
            if results["total_claims"] > 0:
                verified_count = results["summary"]["verified"]
                results["overall_reliability"] = verified_count / results["total_claims"]

            # Remember in memory
            await self.memory.remember(
                content={
                    "verification_session": True,
                    "claims_checked": len(claims),
                    "reliability": results["overall_reliability"],
                },
                importance=0.9,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Verification complete: {len(claims)} claims, "
                f"{results['summary']['verified']} verified, "
                f"{results['summary']['refuted']} refuted"
            )

            return results

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def assess_source_credibility(
        self,
        source: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assess the credibility of a source

        Args:
            source: Source to assess

        Returns:
            Credibility assessment
        """
        assessment = {
            "source_url": source.get("url"),
            "credibility_score": 0.0,
            "factors": {
                "domain_reputation": 0.0,
                "citation_quality": 0.0,
                "author_credibility": 0.0,
                "recency": 0.0,
                "consistency": 0.0,
            },
            "overall_rating": "unknown",  # high, medium, low, unknown
            "concerns": [],
            "recommendations": [],
        }

        # Simulated credibility assessment
        # In production: check domain reputation databases, author credentials, etc.

        # Domain reputation (simulated)
        domain = source.get("url", "").split("/")[2] if "/" in source.get("url", "") else ""
        trusted_domains = ["edu", "gov", "org"]
        if any(td in domain for td in trusted_domains):
            assessment["factors"]["domain_reputation"] = 0.9
        else:
            assessment["factors"]["domain_reputation"] = 0.6

        # Citation quality (check if source has citations)
        if source.get("citations"):
            assessment["factors"]["citation_quality"] = 0.8
        else:
            assessment["factors"]["citation_quality"] = 0.5

        # Author credibility (simulated)
        if source.get("author"):
            assessment["factors"]["author_credibility"] = 0.7
        else:
            assessment["factors"]["author_credibility"] = 0.4
            assessment["concerns"].append("Author not clearly identified")

        # Recency
        timestamp = source.get("timestamp")
        if timestamp:
            assessment["factors"]["recency"] = 0.8
        else:
            assessment["factors"]["recency"] = 0.5

        # Consistency with other sources
        assessment["factors"]["consistency"] = 0.7

        # Calculate overall score
        assessment["credibility_score"] = sum(assessment["factors"].values()) / len(
            assessment["factors"]
        )

        # Determine rating
        if assessment["credibility_score"] >= 0.8:
            assessment["overall_rating"] = "high"
        elif assessment["credibility_score"] >= 0.6:
            assessment["overall_rating"] = "medium"
        else:
            assessment["overall_rating"] = "low"
            assessment["recommendations"].append("Verify information with additional sources")

        logger.info(
            f"Credibility assessment: {source.get('url')} -> "
            f"{assessment['overall_rating']} ({assessment['credibility_score']:.2f})"
        )

        return assessment

    async def cross_reference(
        self,
        claim: str,
        sources: List[Dict[str, Any]],
        min_sources: int = 2,
    ) -> Dict[str, Any]:
        """
        Cross-reference a claim across multiple sources

        Args:
            claim: Claim to cross-reference
            sources: Sources to check
            min_sources: Minimum sources needed for verification

        Returns:
            Cross-reference results
        """
        result = {
            "claim": claim,
            "sources_checked": len(sources),
            "supporting_sources": [],
            "neutral_sources": [],
            "contradicting_sources": [],
            "verification_status": "insufficient_data",
            "confidence": 0.0,
        }

        # Verify against each source
        verification = await self._verify_fact(claim, sources)

        result["supporting_sources"] = verification["supporting_sources"]
        result["contradicting_sources"] = verification["contradicting_sources"]

        # Determine verification status
        support_count = len(result["supporting_sources"])

        if support_count >= min_sources:
            result["verification_status"] = "verified"
            result["confidence"] = min(0.95, support_count / len(sources))
        elif len(result["contradicting_sources"]) >= min_sources:
            result["verification_status"] = "refuted"
            result["confidence"] = verification["confidence"]
        else:
            result["verification_status"] = "unverified"
            result["confidence"] = 0.0

        logger.info(
            f"Cross-reference: {support_count}/{len(sources)} sources support claim"
        )

        return result

    def get_fact_checking_summary(self) -> Dict[str, Any]:
        """Get summary of fact-checking activities"""
        return {
            "agent_id": str(self.id),
            "agent_name": self.config.name,
            "total_verifications": self.verifications_performed,
            "facts_checked": len(self.facts_checked),
            "contradictions_found": len(self.contradictions_found),
            "recent_verifications": self.facts_checked[-5:] if self.facts_checked else [],
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }
