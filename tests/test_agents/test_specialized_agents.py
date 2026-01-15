"""Test Suite for Specialized Agents"""

import pytest
import asyncio
from uuid import uuid4

from iras.agents.researcher import ResearchAgent, ResearchConfig
from iras.agents.analyst import AnalystAgent, AnalystConfig
from iras.agents.synthesizer import SynthesizerAgent, SynthesizerConfig
from iras.agents.fact_checker import FactCheckerAgent, FactCheckerConfig


class TestResearchAgent:
    """Test research agent functionality"""

    @pytest.mark.asyncio
    async def test_research_agent_initialization(self):
        config = ResearchConfig(
            name="researcher",
            search_depth=3,
        )
        agent = ResearchAgent(config)

        assert agent.config.name == "researcher"
        assert "research" in agent.capabilities

    @pytest.mark.asyncio
    async def test_conduct_research(self):
        config = ResearchConfig(name="researcher")
        agent = ResearchAgent(config)

        result = await agent.conduct_research(
            query="Test research topic",
            depth=2,
        )

        assert result is not None
        assert "sources" in result or "findings" in result


class TestAnalystAgent:
    """Test analyst agent functionality"""

    @pytest.mark.asyncio
    async def test_analyst_initialization(self):
        config = AnalystConfig(
            name="analyst",
            analysis_methods=["statistical", "qualitative"],
        )
        agent = AnalystAgent(config)

        assert "analyze" in agent.capabilities

    @pytest.mark.asyncio
    async def test_analyze_data(self):
        config = AnalystConfig(name="analyst")
        agent = AnalystAgent(config)

        data = {"values": [1, 2, 3, 4, 5]}
        result = await agent.analyze(
            data=data,
            method="statistical",
        )

        assert result is not None


class TestSynthesizerAgent:
    """Test synthesizer agent functionality"""

    @pytest.mark.asyncio
    async def test_synthesizer_initialization(self):
        config = SynthesizerConfig(name="synthesizer")
        agent = SynthesizerAgent(config)

        assert "synthesize" in agent.capabilities

    @pytest.mark.asyncio
    async def test_synthesize_information(self):
        config = SynthesizerConfig(name="synthesizer")
        agent = SynthesizerAgent(config)

        inputs = [
            {"source": "A", "content": "Data A"},
            {"source": "B", "content": "Data B"},
        ]

        result = await agent.synthesize(inputs)

        assert result is not None


class TestFactCheckerAgent:
    """Test fact checker agent functionality"""

    @pytest.mark.asyncio
    async def test_fact_checker_initialization(self):
        config = FactCheckerConfig(name="fact_checker")
        agent = FactCheckerAgent(config)

        assert "fact_check" in agent.capabilities

    @pytest.mark.asyncio
    async def test_verify_claim(self):
        config = FactCheckerConfig(name="fact_checker")
        agent = FactCheckerAgent(config)

        claim = "The sky is blue"
        result = await agent.verify_claim(claim)

        assert result is not None
        assert "verdict" in result or "confidence" in result


class TestAgentCollaboration:
    """Test agents working together"""

    @pytest.mark.asyncio
    async def test_research_and_analysis_pipeline(self):
        researcher = ResearchAgent(ResearchConfig(name="r"))
        analyst = AnalystAgent(AnalystConfig(name="a"))

        # Research phase
        research_result = await researcher.conduct_research(
            "Test topic",
            depth=1,
        )

        # Analysis phase
        if research_result:
            analysis = await analyst.analyze(
                data=research_result,
                method="qualitative",
            )
            assert analysis is not None
