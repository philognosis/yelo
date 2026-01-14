"""
Synthesizer Agent

Specializes in:
- Information synthesis
- Report generation
- Multi-source integration
- Summary creation
- Insight combination
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import ReasoningStrategy
from iras.core.state import AgentStatus


class SynthesizerAgent(Agent):
    """
    Specialized agent for synthesizing information from multiple sources

    Capabilities:
    - Multi-source synthesis
    - Report generation
    - Summary creation
    - Insight integration
    - Narrative construction
    """

    def __init__(self, name: str = "Synthesizer"):
        config = AgentConfig(
            name=name,
            role="synthesizer",
            capabilities={
                "information_synthesis",
                "report_generation",
                "summary_creation",
                "insight_integration",
                "narrative_construction",
            },
            temperature=0.7,  # More creative for synthesis
            max_tokens=8000,  # Larger for comprehensive reports
        )
        super().__init__(config)

        # Register specialized tools
        self._register_synthesis_tools()

        # Synthesis-specific state
        self.reports_generated: List[Dict[str, Any]] = []
        self.summaries_created: List[Dict[str, Any]] = []

    def _register_synthesis_tools(self) -> None:
        """Register synthesis-specific tools"""

        # Synthesis tool
        synthesis_tool = AgentTool(
            name="synthesize_information",
            description="Synthesize information from multiple sources",
            parameters={
                "sources": {"type": "array", "description": "Sources to synthesize"},
                "format": {"type": "string", "description": "Output format"},
            },
            function=self._synthesize_information,
        )
        self.register_tool(synthesis_tool)

        # Summary tool
        summary_tool = AgentTool(
            name="create_summary",
            description="Create a concise summary",
            parameters={
                "content": {"type": "string", "description": "Content to summarize"},
                "max_length": {"type": "integer", "description": "Maximum length"},
            },
            function=self._create_summary,
        )
        self.register_tool(summary_tool)

    async def _synthesize_information(
        self,
        sources: List[Dict[str, Any]],
        format: str = "narrative",
    ) -> Dict[str, Any]:
        """
        Synthesize information from multiple sources

        Args:
            sources: Sources to synthesize
            format: Output format (narrative, bullet_points, structured)

        Returns:
            Synthesized information
        """
        synthesis = {
            "sources_used": len(sources),
            "format": format,
            "content": "",
            "key_points": [],
            "synthesis_quality": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

        if not sources:
            synthesis["content"] = "No sources provided for synthesis"
            return synthesis

        # Extract key information from sources
        key_points = []
        for source in sources:
            # Simulated extraction
            point = {
                "source": source.get("url", "unknown"),
                "content": source.get("snippet", source.get("title", "")),
                "relevance": source.get("relevance_score", 0.5),
            }
            key_points.append(point)

        # Sort by relevance
        key_points.sort(key=lambda x: x["relevance"], reverse=True)
        synthesis["key_points"] = key_points[:10]  # Top 10

        # Generate synthesized content based on format
        if format == "narrative":
            synthesis["content"] = self._generate_narrative(key_points)
        elif format == "bullet_points":
            synthesis["content"] = self._generate_bullet_points(key_points)
        elif format == "structured":
            synthesis["content"] = self._generate_structured(key_points)

        # Calculate synthesis quality
        avg_relevance = sum(p["relevance"] for p in key_points) / len(key_points)
        source_diversity = len(set(p["source"] for p in key_points)) / len(sources)
        synthesis["synthesis_quality"] = (avg_relevance + source_diversity) / 2

        logger.info(
            f"Information synthesized: {len(sources)} sources -> "
            f"quality {synthesis['synthesis_quality']:.2f}"
        )

        return synthesis

    def _generate_narrative(self, key_points: List[Dict[str, Any]]) -> str:
        """Generate narrative synthesis"""
        if not key_points:
            return "No key points to synthesize."

        narrative = "Based on analysis of multiple sources, the following synthesis emerges:\n\n"

        for i, point in enumerate(key_points[:5], 1):
            narrative += f"{i}. {point['content']}\n"

        narrative += "\nThese findings suggest a coherent picture that integrates information from diverse sources."

        return narrative

    def _generate_bullet_points(self, key_points: List[Dict[str, Any]]) -> str:
        """Generate bullet point synthesis"""
        if not key_points:
            return "• No key points to synthesize."

        bullets = "Key Findings:\n\n"
        for point in key_points[:10]:
            bullets += f"• {point['content']}\n"

        return bullets

    def _generate_structured(self, key_points: List[Dict[str, Any]]) -> str:
        """Generate structured synthesis"""
        if not key_points:
            return "No structured information available."

        structured = "=== Synthesized Report ===\n\n"
        structured += "## High Confidence Findings\n"

        high_conf = [p for p in key_points if p["relevance"] > 0.7]
        for point in high_conf:
            structured += f"- {point['content']}\n"

        structured += "\n## Supporting Information\n"
        medium_conf = [p for p in key_points if 0.4 <= p["relevance"] <= 0.7]
        for point in medium_conf:
            structured += f"- {point['content']}\n"

        return structured

    async def _create_summary(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """
        Create a concise summary

        Args:
            content: Content to summarize
            max_length: Maximum length in characters

        Returns:
            Summary text
        """
        # Simulated summarization
        # In production: use extractive or abstractive summarization
        words = content.split()

        if len(content) <= max_length:
            return content

        # Simple extractive: take first sentences up to max_length
        summary = ""
        for word in words:
            if len(summary) + len(word) + 1 > max_length:
                break
            summary += word + " "

        summary = summary.strip() + "..."

        logger.info(f"Summary created: {len(content)} chars -> {len(summary)} chars")

        return summary

    async def generate_report(
        self,
        topic: str,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
        verification_results: Optional[Dict[str, Any]] = None,
        format: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive report from multi-agent results

        Args:
            topic: Report topic
            research_results: Results from researcher agent
            analysis_results: Results from analyst agent
            verification_results: Optional results from fact-checker agent
            format: Report format

        Returns:
            Generated report
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Generating report on: {topic}",
        )

        try:
            report = {
                "topic": topic,
                "format": format,
                "sections": {},
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "sources_count": research_results.get("total_sources_found", 0),
                    "analysis_performed": True if analysis_results else False,
                    "fact_checked": True if verification_results else False,
                },
                "quality_score": 0.0,
                "summary": "",
                "full_report": "",
            }

            # Section 1: Executive Summary
            exec_summary = await self._generate_executive_summary(
                topic, research_results, analysis_results
            )
            report["sections"]["executive_summary"] = exec_summary
            report["summary"] = exec_summary

            # Section 2: Research Findings
            research_section = await self._generate_research_section(research_results)
            report["sections"]["research_findings"] = research_section

            # Section 3: Analysis & Insights
            analysis_section = await self._generate_analysis_section(analysis_results)
            report["sections"]["analysis"] = analysis_section

            # Section 4: Verification (if available)
            if verification_results:
                verification_section = await self._generate_verification_section(
                    verification_results
                )
                report["sections"]["verification"] = verification_section

            # Section 5: Conclusions & Recommendations
            conclusions = await self._generate_conclusions(
                research_results, analysis_results, verification_results
            )
            report["sections"]["conclusions"] = conclusions

            # Assemble full report
            report["full_report"] = self._assemble_full_report(report["sections"])

            # Calculate quality score
            report["quality_score"] = self._calculate_report_quality(
                research_results, analysis_results, verification_results
            )

            # Store in memory
            await self.memory.remember(
                content={
                    "report_topic": topic,
                    "quality_score": report["quality_score"],
                    "sections_count": len(report["sections"]),
                },
                importance=0.9,
                memory_type=MemoryType.EPISODIC,
            )

            self.reports_generated.append(report)

            logger.info(
                f"Report generated: '{topic}' - "
                f"quality: {report['quality_score']:.2f}, "
                f"{len(report['sections'])} sections"
            )

            return report

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _generate_executive_summary(
        self,
        topic: str,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
    ) -> str:
        """Generate executive summary"""
        num_sources = research_results.get("quality_sources", 0)
        insights = analysis_results.get("key_insights", [])

        summary = f"## Executive Summary: {topic}\n\n"
        summary += f"This report synthesizes findings from {num_sources} quality sources "
        summary += f"with {len(insights)} key insights identified through comprehensive analysis.\n\n"

        if insights:
            summary += "Key Highlights:\n"
            for insight in insights[:3]:
                summary += f"• {insight.get('insight', 'N/A')}\n"

        return summary

    async def _generate_research_section(
        self,
        research_results: Dict[str, Any],
    ) -> str:
        """Generate research findings section"""
        section = "## Research Findings\n\n"
        section += f"Total sources analyzed: {research_results.get('total_sources_found', 0)}\n"
        section += f"Quality sources: {research_results.get('quality_sources', 0)}\n"
        section += f"Research depth: Level {research_results.get('depth', 1)}\n\n"

        sources = research_results.get("sources", [])
        if sources:
            section += "### Top Sources:\n"
            for i, source in enumerate(sources[:5], 1):
                section += f"{i}. {source.get('title', 'Unknown')}\n"
                section += f"   URL: {source.get('url', 'N/A')}\n"
                eval_score = source.get("evaluation", {}).get("overall_score", 0)
                section += f"   Quality Score: {eval_score:.2f}\n\n"

        return section

    async def _generate_analysis_section(
        self,
        analysis_results: Dict[str, Any],
    ) -> str:
        """Generate analysis section"""
        section = "## Analysis & Insights\n\n"

        insights = analysis_results.get("key_insights", [])
        if insights:
            section += "### Key Insights:\n"
            for insight in insights:
                section += f"• **{insight.get('type', 'General').title()}**: "
                section += f"{insight.get('insight', 'N/A')}\n"

        recommendations = analysis_results.get("recommendations", [])
        if recommendations:
            section += "\n### Recommendations:\n"
            for rec in recommendations:
                section += f"• {rec}\n"

        return section

    async def _generate_verification_section(
        self,
        verification_results: Dict[str, Any],
    ) -> str:
        """Generate verification section"""
        section = "## Fact Verification\n\n"

        summary = verification_results.get("summary", {})
        section += f"Claims verified: {summary.get('verified', 0)}\n"
        section += f"Claims refuted: {summary.get('refuted', 0)}\n"
        section += f"Claims disputed: {summary.get('disputed', 0)}\n"
        section += f"Overall reliability: {verification_results.get('overall_reliability', 0):.1%}\n"

        return section

    async def _generate_conclusions(
        self,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
        verification_results: Optional[Dict[str, Any]],
    ) -> str:
        """Generate conclusions section"""
        section = "## Conclusions\n\n"

        # Synthesize overall conclusion
        section += "Based on comprehensive research, analysis, and verification, "
        section += "the following conclusions can be drawn:\n\n"

        insights = analysis_results.get("key_insights", [])
        for insight in insights[:3]:
            section += f"• {insight.get('insight', 'N/A')}\n"

        if verification_results:
            reliability = verification_results.get("overall_reliability", 0)
            section += f"\nInformation reliability: {reliability:.1%}\n"

        return section

    def _assemble_full_report(self, sections: Dict[str, str]) -> str:
        """Assemble full report from sections"""
        report = "# COMPREHENSIVE RESEARCH REPORT\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "=" * 80 + "\n\n"

        for section_name, content in sections.items():
            report += content + "\n\n"
            report += "-" * 80 + "\n\n"

        return report

    def _calculate_report_quality(
        self,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
        verification_results: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate overall report quality score"""
        scores = []

        # Research quality
        quality_sources = research_results.get("quality_sources", 0)
        if quality_sources >= 10:
            scores.append(0.9)
        elif quality_sources >= 5:
            scores.append(0.7)
        else:
            scores.append(0.5)

        # Analysis quality
        insights = len(analysis_results.get("key_insights", []))
        if insights >= 3:
            scores.append(0.9)
        elif insights >= 1:
            scores.append(0.7)
        else:
            scores.append(0.5)

        # Verification quality
        if verification_results:
            reliability = verification_results.get("overall_reliability", 0)
            scores.append(reliability)

        return sum(scores) / len(scores) if scores else 0.5

    def get_synthesis_summary(self) -> Dict[str, Any]:
        """Get summary of synthesis activities"""
        return {
            "agent_id": str(self.id),
            "agent_name": self.config.name,
            "reports_generated": len(self.reports_generated),
            "summaries_created": len(self.summaries_created),
            "recent_reports": [
                {
                    "topic": r.get("topic"),
                    "quality": r.get("quality_score"),
                    "timestamp": r.get("metadata", {}).get("generated_at"),
                }
                for r in self.reports_generated[-3:]
            ],
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }
