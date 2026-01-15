"""
Researcher Agent

Specializes in:
- Information gathering
- Source discovery
- Data collection
- Query formulation
- Multi-source research
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.planning import Task, TaskPriority
from iras.core.state import AgentStatus


class ResearcherAgent(Agent):
    """
    Specialized agent for research and information gathering

    Capabilities:
    - Web search and information retrieval
    - Source evaluation and ranking
    - Query refinement
    - Multi-perspective research
    - Citation tracking
    """

    def __init__(self, name: str = "Researcher"):
        config = AgentConfig(
            name=name,
            role="researcher",
            capabilities={
                "web_search",
                "source_evaluation",
                "query_formulation",
                "data_collection",
                "citation_tracking",
            },
            temperature=0.5,  # More focused for research
            max_tokens=4000,
        )
        super().__init__(config)

        # Register specialized tools
        self._register_research_tools()

        # Research-specific state
        self.sources_found: List[Dict[str, Any]] = []
        self.queries_executed: List[str] = []
        self.research_depth = 0

    def _register_research_tools(self) -> None:
        """Register research-specific tools"""

        # Web search tool
        search_tool = AgentTool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "default": 10},
            },
            function=self._web_search,
        )
        self.register_tool(search_tool)

        # Source evaluation tool
        eval_tool = AgentTool(
            name="evaluate_source",
            description="Evaluate source credibility and relevance",
            parameters={
                "source": {"type": "object", "description": "Source to evaluate"},
            },
            function=self._evaluate_source,
        )
        self.register_tool(eval_tool)

    async def _web_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Simulate web search (in production, use real search API)

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        self.queries_executed.append(query)

        # Simulated results
        results = []
        for i in range(num_results):
            result = {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a snippet about {query}...",
                "relevance_score": 1.0 - (i * 0.1),
                "source_type": "article",
                "timestamp": datetime.now().isoformat(),
            }
            results.append(result)

        self.sources_found.extend(results)

        # Remember search in memory
        await self.memory.remember(
            content={
                "query": query,
                "num_results": len(results),
                "timestamp": datetime.now().isoformat(),
            },
            importance=0.7,
            memory_type=MemoryType.EPISODIC,
        )

        return results

    async def _evaluate_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate source quality and relevance

        Args:
            source: Source to evaluate

        Returns:
            Evaluation results
        """
        # Simulated evaluation
        evaluation = {
            "source_url": source.get("url"),
            "credibility_score": 0.8,
            "relevance_score": source.get("relevance_score", 0.5),
            "recency_score": 0.9,
            "overall_score": 0.8,
            "recommended": True,
            "concerns": [],
        }

        logger.debug(f"Evaluated source: {source.get('url')} - Score: {evaluation['overall_score']:.2f}")

        return evaluation

    async def research_topic(
        self,
        topic: str,
        depth: int = 2,
        num_sources: int = 10,
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a topic

        Args:
            topic: Topic to research
            depth: Research depth (1-5, higher = more thorough)
            num_sources: Number of sources to gather

        Returns:
            Research results with sources and analysis
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Researching topic: {topic}",
        )

        self.research_depth = depth
        all_sources = []

        try:
            # Generate search queries
            queries = await self._generate_queries(topic, depth)

            # Execute searches
            for query in queries:
                sources = await self._web_search(query, num_sources // len(queries))
                all_sources.extend(sources)

            # Evaluate sources
            evaluated_sources = []
            for source in all_sources:
                evaluation = await self._evaluate_source(source)
                source["evaluation"] = evaluation
                if evaluation["recommended"]:
                    evaluated_sources.append(source)

            # Rank sources
            evaluated_sources.sort(
                key=lambda s: s["evaluation"]["overall_score"],
                reverse=True,
            )

            # Store in memory
            await self.memory.remember(
                content={
                    "topic": topic,
                    "num_sources": len(evaluated_sources),
                    "queries": queries,
                    "depth": depth,
                },
                importance=0.9,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Research completed: {len(evaluated_sources)} quality sources found for '{topic}'"
            )

            return {
                "topic": topic,
                "sources": evaluated_sources[:num_sources],
                "total_sources_found": len(all_sources),
                "quality_sources": len(evaluated_sources),
                "queries_used": queries,
                "depth": depth,
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _generate_queries(self, topic: str, depth: int) -> List[str]:
        """
        Generate search queries for comprehensive coverage

        Args:
            topic: Main topic
            depth: Research depth

        Returns:
            List of search queries
        """
        queries = [topic]  # Main query

        if depth >= 2:
            # Add perspective queries
            queries.extend([
                f"{topic} overview",
                f"{topic} recent developments",
                f"{topic} challenges",
            ])

        if depth >= 3:
            # Add analytical queries
            queries.extend([
                f"{topic} best practices",
                f"{topic} case studies",
                f"{topic} research papers",
            ])

        if depth >= 4:
            # Add comparative queries
            queries.extend([
                f"{topic} comparison",
                f"{topic} alternatives",
                f"{topic} future trends",
            ])

        if depth >= 5:
            # Add expert queries
            queries.extend([
                f"{topic} expert analysis",
                f"{topic} implementation guide",
                f"{topic} advanced techniques",
            ])

        logger.info(f"Generated {len(queries)} search queries for depth {depth}")
        return queries

    async def find_related_topics(self, topic: str) -> List[str]:
        """
        Find topics related to the main topic

        Args:
            topic: Main topic

        Returns:
            List of related topics
        """
        # Simulated related topics
        related = [
            f"{topic} fundamentals",
            f"{topic} applications",
            f"{topic} theory",
            f"{topic} practice",
        ]

        logger.info(f"Found {len(related)} related topics for '{topic}'")
        return related

    def get_research_summary(self) -> Dict[str, Any]:
        """Get summary of research activities"""
        return {
            "agent_id": str(self.id),
            "agent_name": self.config.name,
            "total_queries": len(self.queries_executed),
            "total_sources": len(self.sources_found),
            "recent_queries": self.queries_executed[-5:] if self.queries_executed else [],
            "research_depth": self.research_depth,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }
