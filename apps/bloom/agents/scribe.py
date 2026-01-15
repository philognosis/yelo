"""
Scribe Agent - GenAI Feedback Synthesizer and Co-Pilot

The Scribe is the AI synthesis engine for evaluation content.

Responsibilities:
- **CRITICAL**: Ingest feedback, documents, and historical data
- Perform RAG (Retrieval Augmented Generation) for evidence-based drafts
- Synthesize peer feedback into professional narratives
- Generate manager evaluation drafts with evidence citations
- Ask clarifying questions to fill gaps
- Clean up voice dictation into polished text
- Maintain citation trails for transparency

Design Pattern: RAG Pipeline + Interactive Q&A System
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import numpy as np
from loguru import logger

from apps.bloom.models.evaluation import (
    Evaluation,
    ManagerEvaluation,
    PeerFeedback,
    Rating,
    SelfEvaluation,
)
from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType, ReasoningStrategy
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore
from iras.databases.vector_store import VectorStore


class EvidenceMapping:
    """Maps evaluation claims to supporting evidence"""

    def __init__(self):
        self.claim_to_evidence: Dict[str, List[str]] = {}

    def add_evidence(self, claim: str, evidence: str) -> None:
        """Link evidence to a claim"""
        if claim not in self.claim_to_evidence:
            self.claim_to_evidence[claim] = []
        self.claim_to_evidence[claim].append(evidence)

    def get_citations(self, claim: str) -> List[str]:
        """Get all evidence for a claim"""
        return self.claim_to_evidence.get(claim, [])


class Scribe(Agent):
    """
    AI synthesis and co-pilot agent for evaluation content

    The Scribe transforms raw inputs into polished, evidence-based
    evaluation content. It uses RAG to ground all claims in evidence
    and asks clarifying questions to fill knowledge gaps.

    Capabilities:
    - RAG-based content generation
    - Voice dictation cleanup
    - Peer feedback synthesis
    - Manager evaluation drafting
    - Evidence citation mapping
    - Clarifying question generation
    - Professional tone transformation
    """

    def __init__(
        self,
        name: str = "Scribe",
        document_store: Optional[DocumentStore] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="synthesizer",
            capabilities={
                "rag_generation",
                "text_synthesis",
                "voice_cleanup",
                "evidence_citation",
                "question_generation",
                "tone_transformation",
            },
            temperature=0.7,  # Creative but grounded
            max_tokens=4000,
        )
        super().__init__(config)

        # Database connections
        self.document_store = document_store or DocumentStore()
        self.vector_store = vector_store or VectorStore()

        # Evidence tracking
        self.evidence_mappings: Dict[UUID, EvidenceMapping] = {}

        # Question generation state
        self.pending_questions: Dict[UUID, List[Dict[str, str]]] = {}

        # Register tools
        self._register_synthesis_tools()

        logger.info(f"Scribe '{name}' initialized with RAG capabilities")

    def _register_synthesis_tools(self) -> None:
        """Register Scribe-specific tools"""
        self.register_tool(
            AgentTool(
                name="synthesize_peer_feedback",
                description="Transform raw peer feedback into professional narrative",
                parameters={
                    "feedback_id": {"type": "string"},
                },
                function=self.synthesize_peer_feedback,
            )
        )

        self.register_tool(
            AgentTool(
                name="generate_manager_draft",
                description="Generate manager evaluation draft using RAG",
                parameters={
                    "evaluation_id": {"type": "string"},
                },
                function=self.generate_manager_draft,
            )
        )

        self.register_tool(
            AgentTool(
                name="ask_clarifying_questions",
                description="Generate questions to fill knowledge gaps",
                parameters={
                    "evaluation_id": {"type": "string"},
                },
                function=self.ask_clarifying_questions,
            )
        )

        self.register_tool(
            AgentTool(
                name="clean_voice_dictation",
                description="Clean up voice dictation into polished text",
                parameters={
                    "raw_text": {"type": "string"},
                },
                function=self.clean_voice_dictation,
            )
        )

    async def synthesize_peer_feedback(
        self,
        feedback_id: UUID,
    ) -> Dict[str, Any]:
        """
        Synthesize raw peer feedback into professional narrative

        Args:
            feedback_id: Peer feedback to synthesize

        Returns:
            Synthesized feedback with metadata
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Synthesizing peer feedback {feedback_id}",
        )

        try:
            # Load feedback
            feedback_doc = await self.document_store.find_by_id(
                collection="peer_feedbacks",
                doc_id=str(feedback_id),
            )

            if not feedback_doc:
                raise ValueError(f"Feedback not found: {feedback_id}")

            raw_input = feedback_doc.get("raw_input", "")

            # Clean up voice dictation/informal text
            cleaned_text = await self.clean_voice_dictation(raw_input)

            # Extract key themes using reasoning
            themes = await self._extract_themes(cleaned_text)

            # Generate professional synthesis
            synthesized = await self._generate_professional_narrative(
                cleaned_text,
                themes,
                context_type="peer_feedback",
            )

            # Update feedback document
            await self.document_store.update(
                collection="peer_feedbacks",
                query={"_id": str(feedback_id)},
                update={
                    "$set": {
                        "synthesized_feedback": synthesized,
                        "synthesized_at": datetime.now().isoformat(),
                        "themes": themes,
                    }
                },
            )

            # Add evidence to reasoning
            await self.reasoning.add_evidence(
                content=f"Synthesized peer feedback with {len(themes)} key themes",
                evidence_type=EvidenceType.TESTIMONIAL,
                confidence=0.8,
                source=f"scribe_{self.id}",
            )

            # Store in vector store for RAG
            await self.vector_store.add_document(
                collection="synthesized_feedback",
                document_id=str(feedback_id),
                content=synthesized,
                metadata={
                    "type": "peer_feedback",
                    "evaluation_id": feedback_doc.get("evaluation_id"),
                    "peer_id": feedback_doc.get("peer_id"),
                    "themes": themes,
                },
            )

            logger.info(f"Synthesized peer feedback {feedback_id}")

            return {
                "feedback_id": str(feedback_id),
                "synthesized_text": synthesized,
                "themes": themes,
                "original_length": len(raw_input),
                "synthesized_length": len(synthesized),
                "synthesized_at": datetime.now().isoformat(),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def generate_manager_draft(
        self,
        evaluation_id: UUID,
    ) -> Dict[str, Any]:
        """
        Generate manager evaluation draft using RAG

        This is the CRITICAL function that:
        1. Retrieves all relevant evidence (peer feedback, self-eval, docs)
        2. Uses reasoning to identify patterns and themes
        3. Generates evidence-based evaluation with citations
        4. Identifies gaps and generates clarifying questions

        Args:
            evaluation_id: Evaluation to generate draft for

        Returns:
            Draft evaluation with evidence mapping
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Generating manager draft for evaluation {evaluation_id}",
        )

        try:
            # Load evaluation
            eval_doc = await self.document_store.find_by_id(
                collection="evaluations",
                doc_id=str(evaluation_id),
            )

            if not eval_doc:
                raise ValueError(f"Evaluation not found: {evaluation_id}")

            employee_id = eval_doc["employee_id"]

            # === RAG PHASE 1: RETRIEVE ===
            logger.info(f"RAG Phase 1: Retrieving evidence for {evaluation_id}")

            # Retrieve peer feedback
            peer_feedbacks = await self.document_store.find(
                collection="peer_feedbacks",
                query={"evaluation_id": str(evaluation_id)},
            )

            # Retrieve self-evaluation
            self_eval_docs = await self.document_store.find(
                collection="self_evaluations",
                query={"evaluation_id": str(evaluation_id)},
            )
            self_eval = self_eval_docs[0] if self_eval_docs else None

            # Retrieve historical evaluations (for context)
            historical_evals = await self.document_store.find(
                collection="evaluations",
                query={
                    "employee_id": employee_id,
                    "_id": {"$ne": str(evaluation_id)},
                },
                sort=[("created_at", -1)],
                limit=2,
            )

            # Retrieve vector-similar content
            query_text = f"Performance evaluation for employee {employee_id}"
            similar_docs = await self.vector_store.search(
                collection="synthesized_feedback",
                query_text=query_text,
                limit=10,
            )

            # === RAG PHASE 2: ANALYZE ===
            logger.info(f"RAG Phase 2: Analyzing {len(peer_feedbacks)} peer feedbacks")

            # Extract themes from all feedback
            all_themes = []
            evidence_map = EvidenceMapping()

            for feedback in peer_feedbacks:
                synthesized = feedback.get("synthesized_feedback")
                if synthesized:
                    themes = await self._extract_themes(synthesized)
                    all_themes.extend(themes)

                    # Map evidence
                    for theme in themes:
                        evidence_map.add_evidence(
                            theme,
                            f"Peer feedback from {feedback.get('peer_name')}: {synthesized[:100]}...",
                        )

            # Add self-eval themes
            if self_eval:
                achievements = self_eval.get("synthesized_achievements")
                if achievements:
                    self_themes = await self._extract_themes(achievements)
                    all_themes.extend(self_themes)

                    for theme in self_themes:
                        evidence_map.add_evidence(
                            theme,
                            f"Self-evaluation: {achievements[:100]}...",
                        )

            # Use reasoning to identify patterns
            reasoning_chain = await self.reasoning.reason(
                query=f"What are the key performance patterns for this employee?",
                strategy=ReasoningStrategy.INDUCTIVE,
            )

            # === RAG PHASE 3: GENERATE ===
            logger.info("RAG Phase 3: Generating evidence-based draft")

            # Cluster themes
            theme_clusters = self._cluster_themes(all_themes)

            # Generate draft sections
            draft_sections = {}

            # Technical Assessment
            tech_themes = [t for t in all_themes if self._is_technical_theme(t)]
            if tech_themes:
                draft_sections["technical"] = await self._generate_section(
                    title="Technical Excellence",
                    themes=tech_themes,
                    evidence_map=evidence_map,
                )

            # Leadership Assessment
            leadership_themes = [t for t in all_themes if self._is_leadership_theme(t)]
            if leadership_themes:
                draft_sections["leadership"] = await self._generate_section(
                    title="Leadership & Impact",
                    themes=leadership_themes,
                    evidence_map=evidence_map,
                )

            # Communication
            comm_themes = [t for t in all_themes if self._is_communication_theme(t)]
            if comm_themes:
                draft_sections["communication"] = await self._generate_section(
                    title="Communication & Collaboration",
                    themes=comm_themes,
                    evidence_map=evidence_map,
                )

            # Generate overall summary
            summary = await self._generate_summary(
                peer_feedbacks=peer_feedbacks,
                self_eval=self_eval,
                theme_clusters=theme_clusters,
                evidence_map=evidence_map,
            )

            # === RAG PHASE 4: VALIDATE & QUESTION ===
            logger.info("RAG Phase 4: Identifying gaps")

            # Identify gaps and generate questions
            questions = await self._generate_gap_questions(
                sections=draft_sections,
                peer_count=len(peer_feedbacks),
                has_self_eval=self_eval is not None,
            )

            # Store evidence mapping
            self.evidence_mappings[evaluation_id] = evidence_map

            # Create draft document
            draft = {
                "summary": summary,
                "sections": draft_sections,
                "evidence_citations": len(evidence_map.claim_to_evidence),
                "generated_at": datetime.now().isoformat(),
            }

            # Store draft in evaluation
            await self.document_store.update(
                collection="evaluations",
                query={"_id": str(evaluation_id)},
                update={
                    "$set": {
                        "manager_evaluation.ai_draft_summary": summary,
                        "manager_evaluation.ai_draft_sections": draft_sections,
                        "manager_evaluation.ai_questions": questions,
                        "manager_evaluation.ai_generated_at": datetime.now().isoformat(),
                    }
                },
            )

            # Remember in memory
            await self.memory.remember(
                content={
                    "action": "draft_generated",
                    "evaluation_id": str(evaluation_id),
                    "themes_count": len(all_themes),
                    "questions_count": len(questions),
                },
                importance=0.9,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Generated manager draft for {evaluation_id}: "
                f"{len(all_themes)} themes, {len(questions)} questions"
            )

            return {
                "evaluation_id": str(evaluation_id),
                "draft": draft,
                "questions": questions,
                "peer_feedbacks_analyzed": len(peer_feedbacks),
                "themes_identified": len(all_themes),
                "evidence_citations": len(evidence_map.claim_to_evidence),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def ask_clarifying_questions(
        self,
        evaluation_id: UUID,
    ) -> List[Dict[str, str]]:
        """
        Generate clarifying questions to fill knowledge gaps

        Args:
            evaluation_id: Evaluation to generate questions for

        Returns:
            List of questions with context
        """
        # Load evaluation
        eval_doc = await self.document_store.find_by_id(
            collection="evaluations",
            doc_id=str(evaluation_id),
        )

        if not eval_doc:
            return []

        questions = []

        # Check for missing data
        peer_feedbacks = eval_doc.get("peer_feedbacks", [])
        if len(peer_feedbacks) < 3:
            questions.append(
                {
                    "question": "Only received feedback from few peers. Can you provide additional context on the employee's collaboration and impact?",
                    "category": "peer_coverage",
                    "priority": "high",
                }
            )

        # Check for specific competency gaps
        if not eval_doc.get("manager_evaluation", {}).get("technical_assessment"):
            questions.append(
                {
                    "question": "What are the employee's key technical strengths and areas for growth?",
                    "category": "technical",
                    "priority": "high",
                }
            )

        # Store questions
        self.pending_questions[evaluation_id] = questions

        return questions

    async def clean_voice_dictation(self, raw_text: str) -> str:
        """
        Clean up voice dictation into polished text

        Removes filler words, fixes grammar, maintains meaning

        Args:
            raw_text: Raw dictation text

        Returns:
            Cleaned professional text
        """
        # Remove common filler words
        fillers = ["um", "uh", "like", "you know", "kind of", "sort of"]
        cleaned = raw_text

        for filler in fillers:
            # Remove standalone fillers
            cleaned = re.sub(rf"\b{filler}\b", "", cleaned, flags=re.IGNORECASE)

        # Fix multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned)

        # Capitalize sentences
        sentences = cleaned.split(". ")
        sentences = [s.strip().capitalize() for s in sentences if s.strip()]
        cleaned = ". ".join(sentences)

        # Ensure ends with period
        if cleaned and not cleaned.endswith((".", "!", "?")):
            cleaned += "."

        return cleaned.strip()

    async def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text (simplified)"""
        # In production, use LLM or NLP to extract themes
        # For now, return simulated themes
        themes = []

        # Pattern matching for common themes
        if "technical" in text.lower() or "code" in text.lower():
            themes.append("technical_excellence")

        if "lead" in text.lower() or "mentor" in text.lower():
            themes.append("leadership")

        if "communication" in text.lower() or "collaborate" in text.lower():
            themes.append("collaboration")

        if "innovation" in text.lower() or "creative" in text.lower():
            themes.append("innovation")

        return themes or ["general_performance"]

    async def _generate_professional_narrative(
        self,
        text: str,
        themes: List[str],
        context_type: str,
    ) -> str:
        """Generate professional narrative from informal text"""
        # In production, use LLM to generate
        # For now, return enhanced version
        return f"Demonstrated strong capabilities in {', '.join(themes)}. {text}"

    def _cluster_themes(self, themes: List[str]) -> Dict[str, List[str]]:
        """Cluster similar themes together"""
        clusters = {}
        for theme in themes:
            # Simple clustering by prefix
            category = theme.split("_")[0] if "_" in theme else "general"
            if category not in clusters:
                clusters[category] = []
            clusters[category].append(theme)
        return clusters

    def _is_technical_theme(self, theme: str) -> bool:
        """Check if theme is technical"""
        return "technical" in theme.lower() or "code" in theme.lower()

    def _is_leadership_theme(self, theme: str) -> bool:
        """Check if theme is leadership-related"""
        return "leadership" in theme.lower() or "mentor" in theme.lower()

    def _is_communication_theme(self, theme: str) -> bool:
        """Check if theme is communication-related"""
        return "communication" in theme.lower() or "collaboration" in theme.lower()

    async def _generate_section(
        self,
        title: str,
        themes: List[str],
        evidence_map: EvidenceMapping,
    ) -> str:
        """Generate evaluation section with evidence"""
        # In production, use LLM to generate
        section = f"{title}: "
        section += f"Demonstrated strength in {', '.join(themes)}. "

        # Add evidence citations
        for theme in themes[:2]:  # Top 2 themes
            citations = evidence_map.get_citations(theme)
            if citations:
                section += f"[Supported by: {len(citations)} peer feedback(s)] "

        return section

    async def _generate_summary(
        self,
        peer_feedbacks: List[Dict],
        self_eval: Optional[Dict],
        theme_clusters: Dict[str, List[str]],
        evidence_map: EvidenceMapping,
    ) -> str:
        """Generate overall evaluation summary"""
        summary = f"Based on analysis of {len(peer_feedbacks)} peer reviews"
        if self_eval:
            summary += " and self-evaluation"
        summary += f", identified {len(theme_clusters)} key performance areas. "
        summary += "Employee demonstrates consistent strength across multiple dimensions."
        return summary

    async def _generate_gap_questions(
        self,
        sections: Dict[str, str],
        peer_count: int,
        has_self_eval: bool,
    ) -> List[Dict[str, str]]:
        """Generate questions to fill gaps"""
        questions = []

        if peer_count < 3:
            questions.append(
                {
                    "question": "Limited peer feedback received. Can you provide additional context?",
                    "category": "coverage",
                }
            )

        if "technical" not in sections:
            questions.append(
                {
                    "question": "What are the employee's key technical contributions?",
                    "category": "technical",
                }
            )

        return questions
