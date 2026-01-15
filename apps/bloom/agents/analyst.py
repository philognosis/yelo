"""
Bloom Analyst Agent - Evaluation Metrics and Insights

The BloomAnalyst specializes in calculating evaluation metrics,
generating calibration decks, and analyzing performance trends.

Responsibilities:
- Calculate completion rates and cycle statistics
- Generate calibration committee decks
- Performance trend analysis across cycles
- Rating distribution analysis
- Promotion readiness metrics
- Manager evaluation quality scoring

Design Pattern: Statistical Analysis + Visualization Preparation
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from loguru import logger

from apps.bloom.models.evaluation import (
    Evaluation,
    EvaluationPhase,
    PromotionEligibility,
    Rating,
)
from iras.agents.analyst import AnalystAgent
from iras.core.agent import AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore
from iras.databases.timeseries_store import TimeSeriesStore


class BloomAnalyst(AnalystAgent):
    """
    Specialized analyst for Bloom evaluation system

    Extends the base IRAS AnalystAgent with domain-specific
    capabilities for performance evaluation analytics.

    Capabilities:
    - Evaluation cycle metrics
    - Calibration deck generation
    - Rating distribution analysis
    - Performance trend tracking
    - Manager effectiveness scoring
    - Promotion pipeline analysis
    """

    def __init__(
        self,
        name: str = "BloomAnalyst",
        document_store: Optional[DocumentStore] = None,
        timeseries_store: Optional[TimeSeriesStore] = None,
    ):
        # Initialize base AnalystAgent
        super().__init__(name=name)

        # Update config for Bloom-specific capabilities
        self.config.capabilities.add("evaluation_analytics")
        self.config.capabilities.add("calibration_analysis")
        self.config.capabilities.add("trend_forecasting")

        # Database connections
        self.document_store = document_store or DocumentStore()
        self.timeseries_store = timeseries_store or TimeSeriesStore()

        # Register Bloom-specific tools
        self._register_bloom_tools()

        logger.info(f"BloomAnalyst '{name}' initialized with evaluation analytics")

    def _register_bloom_tools(self) -> None:
        """Register Bloom-specific analysis tools"""
        self.register_tool(
            AgentTool(
                name="calculate_cycle_metrics",
                description="Calculate comprehensive metrics for evaluation cycle",
                parameters={
                    "cycle_name": {"type": "string"},
                },
                function=self.calculate_cycle_metrics,
            )
        )

        self.register_tool(
            AgentTool(
                name="generate_calibration_deck",
                description="Generate calibration committee deck",
                parameters={
                    "cycle_name": {"type": "string"},
                    "level": {"type": "string"},
                },
                function=self.generate_calibration_deck,
            )
        )

        self.register_tool(
            AgentTool(
                name="analyze_rating_distribution",
                description="Analyze rating distribution and identify outliers",
                parameters={
                    "cycle_name": {"type": "string"},
                },
                function=self.analyze_rating_distribution,
            )
        )

        self.register_tool(
            AgentTool(
                name="analyze_performance_trends",
                description="Analyze performance trends across cycles",
                parameters={
                    "employee_id": {"type": "string"},
                },
                function=self.analyze_performance_trends,
            )
        )

    async def calculate_cycle_metrics(
        self,
        cycle_name: str,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for evaluation cycle

        Args:
            cycle_name: Cycle to analyze

        Returns:
            Detailed cycle metrics
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Calculating metrics for cycle {cycle_name}",
        )

        try:
            # Load all evaluations in cycle
            evaluations = await self.document_store.find(
                collection="evaluations",
                query={"cycle_name": cycle_name},
            )

            total = len(evaluations)
            if total == 0:
                return {"cycle_name": cycle_name, "total": 0, "error": "No evaluations found"}

            # Phase distribution
            phase_counts = Counter(e["current_phase"] for e in evaluations)

            # Completion rates
            completed = sum(1 for e in evaluations if e["current_phase"] == "completed")
            completion_rate = completed / total

            # Timeline analysis
            started_dates = [
                datetime.fromisoformat(e["created_at"])
                for e in evaluations
                if e.get("created_at")
            ]
            completed_dates = [
                datetime.fromisoformat(e["completed_at"])
                for e in evaluations
                if e.get("completed_at")
            ]

            avg_duration_days = None
            if completed_dates and started_dates:
                # Calculate average duration for completed evaluations
                durations = []
                for eval_doc in evaluations:
                    if eval_doc.get("completed_at") and eval_doc.get("created_at"):
                        start = datetime.fromisoformat(eval_doc["created_at"])
                        end = datetime.fromisoformat(eval_doc["completed_at"])
                        durations.append((end - start).days)

                if durations:
                    avg_duration_days = float(np.mean(durations))

            # Peer feedback metrics
            total_peer_feedbacks = sum(
                len(e.get("peer_feedbacks", [])) for e in evaluations
            )
            avg_peer_feedbacks = total_peer_feedbacks / total if total > 0 else 0

            # Self-eval completion
            self_eval_complete = sum(
                1 for e in evaluations if e.get("self_evaluation") is not None
            )
            self_eval_rate = self_eval_complete / total

            # Manager eval completion
            manager_eval_complete = sum(
                1 for e in evaluations if e.get("manager_evaluation") is not None
            )
            manager_eval_rate = manager_eval_complete / total

            # Rating distribution (for completed evals)
            ratings = []
            for eval_doc in evaluations:
                mgr_eval = eval_doc.get("manager_evaluation")
                if mgr_eval and mgr_eval.get("overall_rating"):
                    ratings.append(mgr_eval["overall_rating"])

            rating_distribution = Counter(ratings)

            # Promotion analysis
            promotions = []
            for eval_doc in evaluations:
                mgr_eval = eval_doc.get("manager_evaluation")
                if mgr_eval and mgr_eval.get("promotion_eligibility"):
                    promotions.append(mgr_eval["promotion_eligibility"])

            promotion_distribution = Counter(promotions)

            # Calculate health score
            health_score = self._calculate_cycle_health(
                completion_rate=completion_rate,
                self_eval_rate=self_eval_rate,
                manager_eval_rate=manager_eval_rate,
                avg_peer_feedbacks=avg_peer_feedbacks,
            )

            metrics = {
                "cycle_name": cycle_name,
                "total_evaluations": total,
                "completion_rate": completion_rate,
                "health_score": health_score,
                "phase_distribution": dict(phase_counts),
                "timeline": {
                    "avg_duration_days": avg_duration_days,
                    "earliest_start": min(started_dates).isoformat() if started_dates else None,
                    "latest_completion": max(completed_dates).isoformat() if completed_dates else None,
                },
                "feedback_metrics": {
                    "total_peer_feedbacks": total_peer_feedbacks,
                    "avg_peer_feedbacks_per_eval": avg_peer_feedbacks,
                    "self_eval_completion_rate": self_eval_rate,
                    "manager_eval_completion_rate": manager_eval_rate,
                },
                "rating_distribution": dict(rating_distribution),
                "promotion_distribution": dict(promotion_distribution),
                "calculated_at": datetime.now().isoformat(),
            }

            # Store metrics in timeseries
            await self._store_cycle_metrics(cycle_name, metrics)

            # Remember analysis
            await self.memory.remember(
                content={
                    "action": "cycle_metrics",
                    "cycle_name": cycle_name,
                    "completion_rate": completion_rate,
                    "health_score": health_score,
                },
                importance=0.8,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Cycle metrics calculated for {cycle_name}: "
                f"{total} evals, {completion_rate:.1%} complete, health={health_score:.2f}"
            )

            return metrics

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def generate_calibration_deck(
        self,
        cycle_name: str,
        level: str,
    ) -> Dict[str, Any]:
        """
        Generate calibration committee deck for review session

        This deck helps calibration committees ensure consistent
        rating standards across teams.

        Args:
            cycle_name: Evaluation cycle
            level: Employee level (L6, L5, etc.)

        Returns:
            Calibration deck data
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Generating calibration deck for {level} in {cycle_name}",
        )

        try:
            # Load evaluations for this level
            evaluations = await self.document_store.find(
                collection="evaluations",
                query={
                    "cycle_name": cycle_name,
                    # In production, filter by employee level
                },
            )

            # Filter evaluations that have manager ratings
            rated_evals = [
                e
                for e in evaluations
                if e.get("manager_evaluation", {}).get("overall_rating")
            ]

            if not rated_evals:
                return {
                    "cycle_name": cycle_name,
                    "level": level,
                    "error": "No rated evaluations found",
                }

            # Group by rating
            by_rating = defaultdict(list)
            for eval_doc in rated_evals:
                rating = eval_doc["manager_evaluation"]["overall_rating"]
                by_rating[rating].append(eval_doc)

            # Generate deck sections
            deck = {
                "cycle_name": cycle_name,
                "level": level,
                "total_evaluations": len(rated_evals),
                "rating_summary": {},
                "calibration_focus_areas": [],
                "outlier_cases": [],
                "generated_at": datetime.now().isoformat(),
            }

            # Rating summary with examples
            for rating in Rating:
                count = len(by_rating[rating.value])
                if count > 0:
                    percentage = count / len(rated_evals)

                    # Get sample cases
                    samples = by_rating[rating.value][:3]  # Top 3 examples

                    deck["rating_summary"][rating.value] = {
                        "count": count,
                        "percentage": percentage,
                        "sample_cases": [
                            {
                                "employee_id": s["employee_id"],
                                "summary": s["manager_evaluation"].get("final_summary", "")[:200],
                            }
                            for s in samples
                        ],
                    }

            # Identify calibration focus areas
            deck["calibration_focus_areas"] = await self._identify_focus_areas(
                rated_evals
            )

            # Identify outliers
            deck["outlier_cases"] = await self._identify_outlier_cases(rated_evals)

            # Add statistical insights
            ratings_numeric = {
                Rating.EXCEPTIONAL: 5,
                Rating.EXCEEDS: 4,
                Rating.MEETS: 3,
                Rating.DEVELOPING: 2,
                Rating.NOT_MEETING: 1,
            }

            rating_values = [
                ratings_numeric.get(Rating(e["manager_evaluation"]["overall_rating"]), 3)
                for e in rated_evals
            ]

            deck["statistics"] = {
                "mean_rating": float(np.mean(rating_values)),
                "std_rating": float(np.std(rating_values)),
                "median_rating": float(np.median(rating_values)),
            }

            logger.info(
                f"Calibration deck generated for {level}/{cycle_name}: "
                f"{len(rated_evals)} evaluations, {len(deck['outlier_cases'])} outliers"
            )

            return deck

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def analyze_rating_distribution(
        self,
        cycle_name: str,
    ) -> Dict[str, Any]:
        """
        Analyze rating distribution and identify potential issues

        Args:
            cycle_name: Cycle to analyze

        Returns:
            Distribution analysis with recommendations
        """
        # Get all rated evaluations
        evaluations = await self.document_store.find(
            collection="evaluations",
            query={"cycle_name": cycle_name},
        )

        rated_evals = [
            e
            for e in evaluations
            if e.get("manager_evaluation", {}).get("overall_rating")
        ]

        if not rated_evals:
            return {"error": "No rated evaluations found"}

        # Count ratings
        rating_counts = Counter(
            e["manager_evaluation"]["overall_rating"] for e in rated_evals
        )

        total = len(rated_evals)

        # Calculate percentages
        distribution = {}
        for rating in Rating:
            count = rating_counts.get(rating.value, 0)
            distribution[rating.value] = {
                "count": count,
                "percentage": count / total if total > 0 else 0,
            }

        # Expected distribution (approximate Bell curve)
        expected = {
            Rating.EXCEPTIONAL.value: 0.10,  # 10%
            Rating.EXCEEDS.value: 0.25,  # 25%
            Rating.MEETS.value: 0.50,  # 50%
            Rating.DEVELOPING.value: 0.10,  # 10%
            Rating.NOT_MEETING.value: 0.05,  # 5%
        }

        # Identify deviations
        issues = []
        for rating, expected_pct in expected.items():
            actual_pct = distribution[rating]["percentage"]
            deviation = actual_pct - expected_pct

            if abs(deviation) > 0.15:  # More than 15% deviation
                issues.append(
                    {
                        "rating": rating,
                        "expected": expected_pct,
                        "actual": actual_pct,
                        "deviation": deviation,
                        "severity": "high" if abs(deviation) > 0.25 else "medium",
                    }
                )

        analysis = {
            "cycle_name": cycle_name,
            "total_rated": total,
            "distribution": distribution,
            "expected_distribution": expected,
            "issues": issues,
            "recommendations": self._generate_distribution_recommendations(issues),
            "analyzed_at": datetime.now().isoformat(),
        }

        logger.info(
            f"Rating distribution analyzed for {cycle_name}: "
            f"{len(issues)} potential issues identified"
        )

        return analysis

    async def analyze_performance_trends(
        self,
        employee_id: UUID,
        num_cycles: int = 4,
    ) -> Dict[str, Any]:
        """
        Analyze performance trends for an employee across cycles

        Args:
            employee_id: Employee to analyze
            num_cycles: Number of recent cycles to include

        Returns:
            Trend analysis
        """
        # Load employee's evaluations
        evaluations = await self.document_store.find(
            collection="evaluations",
            query={"employee_id": str(employee_id)},
            sort=[("created_at", -1)],
            limit=num_cycles,
        )

        if not evaluations:
            return {"employee_id": str(employee_id), "error": "No evaluations found"}

        # Extract ratings over time
        rating_history = []
        ratings_numeric = {
            Rating.EXCEPTIONAL.value: 5,
            Rating.EXCEEDS.value: 4,
            Rating.MEETS.value: 3,
            Rating.DEVELOPING.value: 2,
            Rating.NOT_MEETING.value: 1,
        }

        for eval_doc in reversed(evaluations):  # Chronological order
            mgr_eval = eval_doc.get("manager_evaluation")
            if mgr_eval and mgr_eval.get("overall_rating"):
                rating_history.append(
                    {
                        "cycle": eval_doc["cycle_name"],
                        "rating": mgr_eval["overall_rating"],
                        "rating_numeric": ratings_numeric.get(
                            mgr_eval["overall_rating"], 3
                        ),
                        "date": eval_doc["created_at"],
                    }
                )

        if len(rating_history) < 2:
            trend = "insufficient_data"
        else:
            # Calculate trend
            values = [r["rating_numeric"] for r in rating_history]
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)

            if slope > 0.3:
                trend = "improving"
            elif slope < -0.3:
                trend = "declining"
            else:
                trend = "stable"

        analysis = {
            "employee_id": str(employee_id),
            "cycles_analyzed": len(rating_history),
            "rating_history": rating_history,
            "trend": trend,
            "current_rating": rating_history[-1]["rating"] if rating_history else None,
            "analyzed_at": datetime.now().isoformat(),
        }

        logger.info(
            f"Performance trend for {employee_id}: {trend} over {len(rating_history)} cycles"
        )

        return analysis

    def _calculate_cycle_health(
        self,
        completion_rate: float,
        self_eval_rate: float,
        manager_eval_rate: float,
        avg_peer_feedbacks: float,
    ) -> float:
        """Calculate overall cycle health score (0-1)"""
        # Weighted components
        weights = {
            "completion": 0.4,
            "self_eval": 0.2,
            "manager_eval": 0.3,
            "peer_feedback": 0.1,
        }

        # Normalize peer feedback (expect avg of 5)
        peer_score = min(avg_peer_feedbacks / 5.0, 1.0)

        health = (
            completion_rate * weights["completion"]
            + self_eval_rate * weights["self_eval"]
            + manager_eval_rate * weights["manager_eval"]
            + peer_score * weights["peer_feedback"]
        )

        return health

    async def _store_cycle_metrics(
        self,
        cycle_name: str,
        metrics: Dict[str, Any],
    ) -> None:
        """Store cycle metrics in timeseries database"""
        timestamp = datetime.now()
        tags = {"cycle": cycle_name}

        await self.timeseries_store.write_point(
            metric="bloom.cycle.completion_rate",
            value=metrics["completion_rate"],
            timestamp=timestamp,
            tags=tags,
        )

        await self.timeseries_store.write_point(
            metric="bloom.cycle.health_score",
            value=metrics["health_score"],
            timestamp=timestamp,
            tags=tags,
        )

    async def _identify_focus_areas(
        self,
        evaluations: List[Dict],
    ) -> List[Dict[str, str]]:
        """Identify areas requiring calibration focus"""
        focus_areas = []

        # Check for manager variance
        by_manager = defaultdict(list)
        for eval_doc in evaluations:
            manager_id = eval_doc["manager_id"]
            rating = eval_doc["manager_evaluation"]["overall_rating"]
            by_manager[manager_id].append(rating)

        # Identify managers with unusual distributions
        for manager_id, ratings in by_manager.items():
            if len(ratings) >= 3:
                # Check if all ratings are the same (lack of differentiation)
                if len(set(ratings)) == 1:
                    focus_areas.append(
                        {
                            "area": "manager_differentiation",
                            "manager_id": manager_id,
                            "issue": "All ratings identical - may lack differentiation",
                        }
                    )

        return focus_areas

    async def _identify_outlier_cases(
        self,
        evaluations: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Identify outlier cases for calibration review"""
        outliers = []

        # Identify extreme ratings with limited peer feedback
        for eval_doc in evaluations:
            mgr_eval = eval_doc["manager_evaluation"]
            rating = mgr_eval["overall_rating"]
            peer_count = len(eval_doc.get("peer_feedbacks", []))

            # Extreme rating with few peer inputs
            if rating in [Rating.EXCEPTIONAL.value, Rating.NOT_MEETING.value]:
                if peer_count < 3:
                    outliers.append(
                        {
                            "employee_id": eval_doc["employee_id"],
                            "rating": rating,
                            "peer_feedback_count": peer_count,
                            "reason": "Extreme rating with limited peer input",
                        }
                    )

        return outliers

    def _generate_distribution_recommendations(
        self,
        issues: List[Dict],
    ) -> List[str]:
        """Generate recommendations based on distribution issues"""
        recommendations = []

        for issue in issues:
            if issue["deviation"] > 0:
                recommendations.append(
                    f"Consider reviewing {issue['rating']} ratings - "
                    f"{issue['actual']:.1%} vs expected {issue['expected']:.1%}"
                )
            else:
                recommendations.append(
                    f"Low {issue['rating']} rate may indicate lenient rating or talent concentration"
                )

        return recommendations
