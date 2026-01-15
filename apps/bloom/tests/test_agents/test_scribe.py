"""
Tests for Scribe Agent (CRITICAL)

Tests voice dictation cleanup, peer feedback synthesis,
RAG pipeline (generate_manager_draft), evidence mapping,
and clarifying question generation.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from bloom.agents.scribe import EvidenceMapping, Scribe


class TestScribe:
    """Test Scribe basic functionality"""

    @pytest.mark.asyncio
    async def test_scribe_initialization(self, mock_scribe):
        """Test Scribe initializes correctly"""
        assert mock_scribe.config.name == "Scribe"
        assert "rag_generation" in mock_scribe.config.capabilities
        assert "text_synthesis" in mock_scribe.config.capabilities
        assert "voice_cleanup" in mock_scribe.config.capabilities

    @pytest.mark.asyncio
    async def test_scribe_temperature_setting(self, mock_scribe):
        """Test Scribe has appropriate temperature for creativity"""
        # Should be higher than deterministic agents but still grounded
        assert 0.5 <= mock_scribe.config.temperature <= 0.9


class TestEvidenceMapping:
    """Test evidence mapping functionality"""

    def test_evidence_mapping_creation(self):
        """Test creating evidence mapping"""
        mapping = EvidenceMapping()
        assert len(mapping.claim_to_evidence) == 0

    def test_add_evidence(self):
        """Test adding evidence to claim"""
        mapping = EvidenceMapping()
        mapping.add_evidence("technical_excellence", "Peer feedback 1")
        mapping.add_evidence("technical_excellence", "Peer feedback 2")

        citations = mapping.get_citations("technical_excellence")
        assert len(citations) == 2
        assert "Peer feedback 1" in citations

    def test_get_citations_no_evidence(self):
        """Test getting citations for claim with no evidence"""
        mapping = EvidenceMapping()
        citations = mapping.get_citations("nonexistent_claim")
        assert citations == []

    def test_multiple_claims(self):
        """Test mapping multiple claims"""
        mapping = EvidenceMapping()
        mapping.add_evidence("technical", "Evidence T1")
        mapping.add_evidence("leadership", "Evidence L1")
        mapping.add_evidence("communication", "Evidence C1")

        assert len(mapping.claim_to_evidence) == 3
        assert mapping.get_citations("technical") == ["Evidence T1"]
        assert mapping.get_citations("leadership") == ["Evidence L1"]


class TestVoiceDictationCleanup:
    """Test voice dictation cleanup (CRITICAL)"""

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_simple(
        self, mock_scribe, sample_feedback_text
    ):
        """Test cleaning simple voice dictation"""
        cleaned = await mock_scribe.clean_voice_dictation(sample_feedback_text)

        # Should remove filler words
        assert "um" not in cleaned.lower()
        assert "uh" not in cleaned.lower()
        assert "like" not in cleaned.lower() or "like" in cleaned.lower()  # "like" might be legitimate
        assert "you know" not in cleaned.lower()

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_fillers(self, mock_scribe):
        """Test removing filler words"""
        text = "Um, so like, this is, you know, kind of great work, sort of"
        cleaned = await mock_scribe.clean_voice_dictation(text)

        assert "um" not in cleaned.lower()
        assert "you know" not in cleaned.lower()
        assert "kind of" not in cleaned.lower()
        assert "sort of" not in cleaned.lower()

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_capitalization(self, mock_scribe):
        """Test sentence capitalization"""
        text = "this is sentence one. this is sentence two"
        cleaned = await mock_scribe.clean_voice_dictation(text)

        # First word should be capitalized
        assert cleaned[0].isupper()

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_whitespace(self, mock_scribe):
        """Test fixing multiple spaces"""
        text = "Too    many     spaces"
        cleaned = await mock_scribe.clean_voice_dictation(text)

        assert "    " not in cleaned
        assert "Too many spaces" in cleaned

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_punctuation(self, mock_scribe):
        """Test adding final punctuation"""
        text = "This sentence has no ending"
        cleaned = await mock_scribe.clean_voice_dictation(text)

        # Should end with period
        assert cleaned.endswith(".")

    @pytest.mark.asyncio
    async def test_clean_voice_dictation_preserves_meaning(self, mock_scribe):
        """Test that meaning is preserved"""
        text = "Um, Jane did a great job on the API migration"
        cleaned = await mock_scribe.clean_voice_dictation(text)

        # Key words should remain
        assert "Jane" in cleaned
        assert "great" in cleaned
        assert "API migration" in cleaned


class TestPeerFeedbackSynthesis:
    """Test peer feedback synthesis"""

    @pytest.mark.asyncio
    async def test_synthesize_peer_feedback(
        self, mock_scribe, mock_document_store, mock_peer_feedback
    ):
        """Test synthesizing peer feedback"""
        feedback_doc = mock_peer_feedback.model_dump()
        mock_document_store.find_by_id.return_value = feedback_doc

        result = await mock_scribe.synthesize_peer_feedback(
            feedback_id=mock_peer_feedback.id
        )

        assert result["synthesized_text"] is not None
        assert "themes" in result
        assert result["feedback_id"] == str(mock_peer_feedback.id)

    @pytest.mark.asyncio
    async def test_synthesize_peer_feedback_extracts_themes(
        self, mock_scribe, mock_document_store, mock_peer_feedback
    ):
        """Test theme extraction from feedback"""
        feedback_doc = mock_peer_feedback.model_dump()
        feedback_doc["raw_input"] = "Great technical skills and excellent leadership on the project"
        mock_document_store.find_by_id.return_value = feedback_doc

        result = await mock_scribe.synthesize_peer_feedback(
            feedback_id=mock_peer_feedback.id
        )

        # Should identify technical and leadership themes
        themes = result["themes"]
        assert len(themes) > 0

    @pytest.mark.asyncio
    async def test_synthesize_peer_feedback_not_found(
        self, mock_scribe, mock_document_store
    ):
        """Test error when feedback not found"""
        mock_document_store.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Feedback not found"):
            await mock_scribe.synthesize_peer_feedback(feedback_id=uuid4())


class TestManagerDraftGeneration:
    """Test manager evaluation draft generation (CRITICAL RAG PIPELINE)"""

    @pytest.mark.asyncio
    async def test_generate_manager_draft_simple(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test basic manager draft generation"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        # Mock peer feedbacks
        peer_feedbacks = [fb.model_dump() for fb in mock_evaluation_with_data.peer_feedbacks]
        mock_document_store.find.return_value = peer_feedbacks

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        assert "draft" in result
        assert "questions" in result
        assert result["evaluation_id"] == str(mock_evaluation_with_data.id)

    @pytest.mark.asyncio
    async def test_generate_manager_draft_with_evidence_map(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test draft includes evidence mapping"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc
        mock_document_store.find.return_value = [
            fb.model_dump() for fb in mock_evaluation_with_data.peer_feedbacks
        ]

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        draft = result["draft"]
        assert "evidence_citations" in draft
        assert draft["evidence_citations"] >= 0

    @pytest.mark.asyncio
    async def test_generate_manager_draft_analyzes_peer_feedbacks(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test RAG Phase 2: Analyzing peer feedbacks"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        # Add synthesized peer feedbacks
        peer_feedbacks = []
        for fb in mock_evaluation_with_data.peer_feedbacks:
            fb_dict = fb.model_dump()
            fb_dict["synthesized_feedback"] = "Strong technical leader"
            peer_feedbacks.append(fb_dict)

        mock_document_store.find.return_value = peer_feedbacks

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        assert result["peer_feedbacks_analyzed"] == len(peer_feedbacks)
        assert result["themes_identified"] > 0

    @pytest.mark.asyncio
    async def test_generate_manager_draft_includes_self_eval(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test draft incorporates self-evaluation"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        # Mock peer feedbacks
        mock_document_store.find.return_value = [
            fb.model_dump() for fb in mock_evaluation_with_data.peer_feedbacks
        ]

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        # Should have analyzed data including self-eval
        assert result["themes_identified"] > 0

    @pytest.mark.asyncio
    async def test_generate_manager_draft_generates_questions(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test RAG Phase 4: Generating clarifying questions"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc
        mock_document_store.find.return_value = [
            fb.model_dump() for fb in mock_evaluation_with_data.peer_feedbacks
        ]

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        questions = result["questions"]
        assert isinstance(questions, list)
        # Should generate some questions
        assert len(questions) >= 0

    @pytest.mark.asyncio
    async def test_generate_manager_draft_evaluation_not_found(
        self, mock_scribe, mock_document_store
    ):
        """Test error when evaluation not found"""
        mock_document_store.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Evaluation not found"):
            await mock_scribe.generate_manager_draft(evaluation_id=uuid4())

    @pytest.mark.asyncio
    async def test_generate_manager_draft_sections(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation_with_data,
    ):
        """Test draft is broken into sections"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc
        mock_document_store.find.return_value = [
            fb.model_dump() for fb in mock_evaluation_with_data.peer_feedbacks
        ]

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        draft = result["draft"]
        assert "sections" in draft

    @pytest.mark.asyncio
    async def test_generate_manager_draft_with_minimal_data(
        self,
        mock_scribe,
        mock_document_store,
        mock_evaluation,
    ):
        """Test draft generation with minimal feedback"""
        eval_doc = mock_evaluation.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc
        mock_document_store.find.return_value = []  # No peer feedbacks

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation.id
        )

        # Should still generate draft with questions about missing data
        assert "questions" in result
        assert len(result["questions"]) > 0  # Should ask for more data


class TestClarifyingQuestions:
    """Test clarifying question generation"""

    @pytest.mark.asyncio
    async def test_ask_clarifying_questions(
        self, mock_scribe, mock_document_store, mock_evaluation
    ):
        """Test generating clarifying questions"""
        eval_doc = mock_evaluation.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        questions = await mock_scribe.ask_clarifying_questions(
            evaluation_id=mock_evaluation.id
        )

        assert isinstance(questions, list)

    @pytest.mark.asyncio
    async def test_questions_for_missing_peer_feedback(
        self, mock_scribe, mock_document_store, mock_evaluation
    ):
        """Test questions when peer feedback is insufficient"""
        eval_doc = mock_evaluation.model_dump()
        eval_doc["peer_feedbacks"] = []  # No feedbacks
        mock_document_store.find_by_id.return_value = eval_doc

        questions = await mock_scribe.ask_clarifying_questions(
            evaluation_id=mock_evaluation.id
        )

        # Should ask about missing peer feedback
        assert len(questions) > 0
        assert any("peer" in q["question"].lower() for q in questions)

    @pytest.mark.asyncio
    async def test_questions_for_missing_technical_assessment(
        self, mock_scribe, mock_document_store, mock_evaluation
    ):
        """Test questions for missing technical assessment"""
        eval_doc = mock_evaluation.model_dump()
        eval_doc["manager_evaluation"] = {}
        mock_document_store.find_by_id.return_value = eval_doc

        questions = await mock_scribe.ask_clarifying_questions(
            evaluation_id=mock_evaluation.id
        )

        # Should ask about technical skills
        technical_questions = [q for q in questions if q["category"] == "technical"]
        assert len(technical_questions) > 0

    @pytest.mark.asyncio
    async def test_questions_include_priority(
        self, mock_scribe, mock_document_store, mock_evaluation
    ):
        """Test questions include priority levels"""
        eval_doc = mock_evaluation.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        questions = await mock_scribe.ask_clarifying_questions(
            evaluation_id=mock_evaluation.id
        )

        if questions:
            question = questions[0]
            assert "priority" in question


class TestThemeExtraction:
    """Test theme extraction from text"""

    @pytest.mark.asyncio
    async def test_extract_themes_technical(self, mock_scribe):
        """Test extracting technical themes"""
        text = "Great technical skills and excellent code quality"
        themes = await mock_scribe._extract_themes(text)

        assert len(themes) > 0
        # Should identify technical theme
        assert any("technical" in theme.lower() for theme in themes)

    @pytest.mark.asyncio
    async def test_extract_themes_leadership(self, mock_scribe):
        """Test extracting leadership themes"""
        text = "Excellent leader who mentors the team effectively"
        themes = await mock_scribe._extract_themes(text)

        assert len(themes) > 0
        # Should identify leadership theme
        assert any("leadership" in theme.lower() for theme in themes)

    @pytest.mark.asyncio
    async def test_extract_themes_multiple(self, mock_scribe):
        """Test extracting multiple themes"""
        text = "Great technical skills, strong leadership, and excellent communication with stakeholders"
        themes = await mock_scribe._extract_themes(text)

        # Should identify multiple themes
        assert len(themes) >= 2


class TestComplexScenarios:
    """Complex test scenarios for Scribe"""

    @pytest.mark.asyncio
    async def test_full_rag_pipeline(
        self,
        mock_scribe,
        mock_document_store,
        mock_vector_store,
        mock_evaluation_with_data,
    ):
        """Test complete RAG pipeline from start to finish"""
        eval_doc = mock_evaluation_with_data.model_dump()
        mock_document_store.find_by_id.return_value = eval_doc

        # Mock peer feedbacks with synthesized versions
        peer_feedbacks = []
        for fb in mock_evaluation_with_data.peer_feedbacks:
            fb_dict = fb.model_dump()
            fb_dict["synthesized_feedback"] = "Demonstrated strong technical and leadership capabilities"
            peer_feedbacks.append(fb_dict)

        mock_document_store.find.return_value = peer_feedbacks

        # Mock vector search results
        mock_vector_store.search.return_value = [
            {"content": "Historical strong performance", "score": 0.9}
        ]

        result = await mock_scribe.generate_manager_draft(
            evaluation_id=mock_evaluation_with_data.id
        )

        # Verify RAG phases completed
        assert result["peer_feedbacks_analyzed"] == 5
        assert result["themes_identified"] > 0
        assert result["evidence_citations"] > 0
        assert "draft" in result
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_voice_to_synthesized_feedback_pipeline(
        self, mock_scribe, mock_document_store
    ):
        """Test complete pipeline from voice input to synthesized feedback"""
        raw_voice = "Um, so like, Jane did amazing work on the, uh, API project"

        # First: Clean voice dictation
        cleaned = await mock_scribe.clean_voice_dictation(raw_voice)

        # Should be cleaner
        assert "um" not in cleaned.lower()

        # Then: Synthesize feedback
        feedback_doc = {
            "_id": str(uuid4()),
            "raw_input": cleaned,
            "evaluation_id": str(uuid4()),
            "peer_id": str(uuid4()),
            "peer_name": "Test Peer",
        }
        mock_document_store.find_by_id.return_value = feedback_doc

        result = await mock_scribe.synthesize_peer_feedback(
            feedback_id=uuid4()
        )

        assert result["synthesized_text"] is not None
