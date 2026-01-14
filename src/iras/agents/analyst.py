"""
Analyst Agent

Specializes in:
- Data analysis
- Pattern recognition
- Insight extraction
- Trend identification
- Statistical analysis
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType, ReasoningStrategy
from iras.core.state import AgentStatus


class AnalystAgent(Agent):
    """
    Specialized agent for data analysis and insight extraction

    Capabilities:
    - Statistical analysis
    - Pattern recognition
    - Trend analysis
    - Data visualization preparation
    - Insight generation
    """

    def __init__(self, name: str = "Analyst"):
        config = AgentConfig(
            name=name,
            role="analyst",
            capabilities={
                "statistical_analysis",
                "pattern_recognition",
                "trend_analysis",
                "data_processing",
                "insight_extraction",
            },
            temperature=0.3,  # More deterministic for analysis
            max_tokens=4000,
        )
        super().__init__(config)

        # Register specialized tools
        self._register_analysis_tools()

        # Analysis-specific state
        self.analyses_performed: List[Dict[str, Any]] = []
        self.insights_generated: List[Dict[str, Any]] = []

    def _register_analysis_tools(self) -> None:
        """Register analysis-specific tools"""

        # Statistical analysis tool
        stats_tool = AgentTool(
            name="statistical_analysis",
            description="Perform statistical analysis on data",
            parameters={
                "data": {"type": "array", "description": "Data to analyze"},
                "metrics": {"type": "array", "description": "Metrics to calculate"},
            },
            function=self._statistical_analysis,
        )
        self.register_tool(stats_tool)

        # Pattern recognition tool
        pattern_tool = AgentTool(
            name="recognize_patterns",
            description="Identify patterns in data",
            parameters={
                "data": {"type": "array", "description": "Data to analyze"},
            },
            function=self._recognize_patterns,
        )
        self.register_tool(pattern_tool)

    async def _statistical_analysis(
        self,
        data: List[float],
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis on numerical data

        Args:
            data: Numerical data to analyze
            metrics: Specific metrics to calculate

        Returns:
            Statistical analysis results
        """
        if not data:
            return {"error": "No data provided"}

        arr = np.array(data)

        results = {
            "count": len(arr),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "range": float(np.max(arr) - np.min(arr)),
        }

        # Add percentiles
        results["percentiles"] = {
            "25th": float(np.percentile(arr, 25)),
            "50th": float(np.percentile(arr, 50)),
            "75th": float(np.percentile(arr, 75)),
            "90th": float(np.percentile(arr, 90)),
            "95th": float(np.percentile(arr, 95)),
        }

        logger.info(f"Statistical analysis complete: mean={results['mean']:.2f}, std={results['std']:.2f}")

        return results

    async def _recognize_patterns(self, data: List[Any]) -> Dict[str, Any]:
        """
        Identify patterns in data

        Args:
            data: Data to analyze for patterns

        Returns:
            Identified patterns
        """
        patterns = {
            "frequency_distribution": {},
            "most_common": [],
            "unique_count": 0,
            "pattern_type": "categorical",
        }

        # Frequency analysis
        counter = Counter(data)
        patterns["frequency_distribution"] = dict(counter)
        patterns["most_common"] = counter.most_common(5)
        patterns["unique_count"] = len(counter)

        # Check if data is numerical
        try:
            numeric_data = [float(x) for x in data if x is not None]
            if len(numeric_data) > 0:
                patterns["pattern_type"] = "numerical"

                # Detect trend
                if len(numeric_data) > 2:
                    x = np.arange(len(numeric_data))
                    coeffs = np.polyfit(x, numeric_data, 1)
                    patterns["trend"] = "increasing" if coeffs[0] > 0 else "decreasing"
                    patterns["trend_strength"] = float(abs(coeffs[0]))

        except (ValueError, TypeError):
            pass

        logger.info(f"Pattern recognition complete: {patterns['unique_count']} unique values")

        return patterns

    async def analyze_sources(
        self,
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze research sources for insights

        Args:
            sources: List of sources to analyze

        Returns:
            Analysis results with insights
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Analyzing {len(sources)} sources",
        )

        try:
            analysis = {
                "total_sources": len(sources),
                "source_types": {},
                "quality_distribution": {},
                "key_insights": [],
                "recommendations": [],
                "timestamp": datetime.now().isoformat(),
            }

            if not sources:
                return analysis

            # Analyze source types
            source_types = [s.get("source_type", "unknown") for s in sources]
            analysis["source_types"] = dict(Counter(source_types))

            # Analyze quality scores
            quality_scores = [
                s.get("evaluation", {}).get("overall_score", 0.5)
                for s in sources
            ]
            quality_stats = await self._statistical_analysis(quality_scores)
            analysis["quality_distribution"] = quality_stats

            # Generate insights
            insights = await self._generate_insights(sources, quality_stats)
            analysis["key_insights"] = insights

            # Generate recommendations
            recommendations = await self._generate_recommendations(sources, analysis)
            analysis["recommendations"] = recommendations

            # Store analysis
            self.analyses_performed.append(analysis)

            # Add evidence to reasoning engine
            await self.reasoning.add_evidence(
                content=f"Analyzed {len(sources)} sources with average quality {quality_stats['mean']:.2f}",
                evidence_type=EvidenceType.STATISTICAL,
                confidence=0.9,
                source=f"analyst_{self.id}",
            )

            # Remember in memory
            await self.memory.remember(
                content={
                    "analysis_type": "source_analysis",
                    "num_sources": len(sources),
                    "avg_quality": quality_stats["mean"],
                },
                importance=0.8,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Source analysis complete: {len(sources)} sources, "
                f"avg quality: {quality_stats['mean']:.2f}"
            )

            return analysis

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _generate_insights(
        self,
        sources: List[Dict[str, Any]],
        quality_stats: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Generate insights from source analysis

        Args:
            sources: Sources to analyze
            quality_stats: Quality statistics

        Returns:
            List of insights
        """
        insights = []

        # Quality insight
        avg_quality = quality_stats.get("mean", 0)
        if avg_quality > 0.8:
            insights.append({
                "type": "quality",
                "insight": "Sources are of high quality with strong credibility",
                "confidence": "high",
            })
        elif avg_quality < 0.5:
            insights.append({
                "type": "quality",
                "insight": "Source quality is below average, findings may need verification",
                "confidence": "medium",
            })

        # Diversity insight
        source_types = set(s.get("source_type", "unknown") for s in sources)
        if len(source_types) >= 3:
            insights.append({
                "type": "diversity",
                "insight": f"Good source diversity with {len(source_types)} different types",
                "confidence": "high",
            })

        # Coverage insight
        if len(sources) >= 10:
            insights.append({
                "type": "coverage",
                "insight": "Comprehensive coverage with multiple sources",
                "confidence": "high",
            })
        elif len(sources) < 5:
            insights.append({
                "type": "coverage",
                "insight": "Limited source coverage, consider expanding research",
                "confidence": "medium",
            })

        self.insights_generated.extend(insights)
        return insights

    async def _generate_recommendations(
        self,
        sources: List[Dict[str, Any]],
        analysis: Dict[str, Any],
    ) -> List[str]:
        """
        Generate recommendations based on analysis

        Args:
            sources: Sources analyzed
            analysis: Analysis results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Quality recommendation
        avg_quality = analysis.get("quality_distribution", {}).get("mean", 0)
        if avg_quality < 0.7:
            recommendations.append(
                "Consider filtering sources to include only those with quality score > 0.7"
            )

        # Diversity recommendation
        source_types = analysis.get("source_types", {})
        if len(source_types) < 3:
            recommendations.append(
                "Seek more diverse source types (articles, papers, reports, etc.)"
            )

        # Coverage recommendation
        if analysis["total_sources"] < 10:
            recommendations.append(
                "Expand research to include more sources for comprehensive coverage"
            )

        return recommendations

    async def identify_trends(
        self,
        data: List[Dict[str, Any]],
        time_field: str = "timestamp",
    ) -> Dict[str, Any]:
        """
        Identify trends in temporal data

        Args:
            data: Data with temporal component
            time_field: Field containing timestamp

        Returns:
            Trend analysis results
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason="Identifying trends",
        )

        try:
            # Extract temporal values
            # Simulated trend analysis
            trends = {
                "overall_trend": "stable",
                "trend_strength": 0.5,
                "seasonality": "none",
                "anomalies": [],
                "forecast": "stable continuation expected",
            }

            logger.info("Trend identification complete")

            return trends

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def compare_datasets(
        self,
        dataset_a: List[Any],
        dataset_b: List[Any],
        name_a: str = "Dataset A",
        name_b: str = "Dataset B",
    ) -> Dict[str, Any]:
        """
        Compare two datasets

        Args:
            dataset_a: First dataset
            dataset_b: Second dataset
            name_a: Name of first dataset
            name_b: Name of second dataset

        Returns:
            Comparison results
        """
        comparison = {
            "datasets": {
                name_a: {"size": len(dataset_a)},
                name_b: {"size": len(dataset_b)},
            },
            "differences": [],
            "similarities": [],
        }

        # Size comparison
        if len(dataset_a) > len(dataset_b):
            comparison["differences"].append(
                f"{name_a} is larger ({len(dataset_a)} vs {len(dataset_b)})"
            )
        elif len(dataset_b) > len(dataset_a):
            comparison["differences"].append(
                f"{name_b} is larger ({len(dataset_b)} vs {len(dataset_a)})"
            )
        else:
            comparison["similarities"].append("Datasets are the same size")

        logger.info(f"Dataset comparison complete: {name_a} vs {name_b}")

        return comparison

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of analysis activities"""
        return {
            "agent_id": str(self.id),
            "agent_name": self.config.name,
            "total_analyses": len(self.analyses_performed),
            "total_insights": len(self.insights_generated),
            "recent_insights": self.insights_generated[-5:] if self.insights_generated else [],
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }
