"""
Adaptive Learning System for Autonomous Agents

Enables agents to learn from experience and continuously improve performance:
- Experience replay and storage
- Performance pattern recognition
- Strategy adaptation
- Success/failure analysis
- Continuous improvement

Features:
- Experience buffer with prioritization
- Pattern recognition in task execution
- Strategy effectiveness tracking
- Automated parameter tuning
- Knowledge transfer
- Performance prediction
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class ExperienceType(str, Enum):
    """Types of experiences to learn from"""

    TASK_EXECUTION = "task_execution"
    ERROR_RECOVERY = "error_recovery"
    PLANNING = "planning"
    COMMUNICATION = "communication"
    OPTIMIZATION = "optimization"


class OutcomeType(str, Enum):
    """Outcome of an experience"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class StrategyType(str, Enum):
    """Types of strategies to learn"""

    TASK_DECOMPOSITION = "task_decomposition"
    RESOURCE_ALLOCATION = "resource_allocation"
    ERROR_HANDLING = "error_handling"
    PLANNING = "planning"
    COMMUNICATION = "communication"


class Experience(BaseModel):
    """
    Single experience record

    Captures context, action, and outcome for learning
    """

    id: UUID = Field(default_factory=uuid4)
    type: ExperienceType
    timestamp: datetime = Field(default_factory=datetime.now)

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)
    state_before: Dict[str, Any] = Field(default_factory=dict)

    # Action
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    strategy_used: Optional[str] = None

    # Outcome
    outcome: OutcomeType
    state_after: Dict[str, Any] = Field(default_factory=dict)
    reward: float = 0.0  # Normalized reward (-1.0 to 1.0)
    duration: float = 0.0  # seconds
    success_metrics: Dict[str, float] = Field(default_factory=dict)

    # Learning metadata
    priority: float = 1.0  # For prioritized replay
    replay_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StrategyPerformance(BaseModel):
    """Performance metrics for a strategy"""

    strategy_name: str
    strategy_type: StrategyType
    total_uses: int = 0
    successes: int = 0
    failures: int = 0
    average_reward: float = 0.0
    average_duration: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    effectiveness_score: float = 0.5  # 0.0 to 1.0

    def update(self, experience: Experience) -> None:
        """Update performance metrics with new experience"""
        self.total_uses += 1
        self.last_used = experience.timestamp

        if experience.outcome == OutcomeType.SUCCESS:
            self.successes += 1
        elif experience.outcome == OutcomeType.FAILURE:
            self.failures += 1

        # Update running averages
        n = self.total_uses
        self.average_reward = (
            (self.average_reward * (n - 1) + experience.reward) / n
        )
        self.average_duration = (
            (self.average_duration * (n - 1) + experience.duration) / n
        )
        self.success_rate = self.successes / n if n > 0 else 0.0

        # Calculate effectiveness (weighted combination)
        self.effectiveness_score = (
            0.5 * self.success_rate +
            0.3 * max(0, min(1, (self.average_reward + 1) / 2)) +
            0.2 * max(0, min(1, 1 - (self.average_duration / 300)))  # Normalize duration
        )


class Pattern(BaseModel):
    """Detected pattern in experiences"""

    id: UUID = Field(default_factory=uuid4)
    pattern_type: str
    description: str
    conditions: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    support_count: int = 0  # Number of experiences supporting this pattern
    created_at: datetime = Field(default_factory=datetime.now)


class AdaptiveLearningSystem:
    """
    Adaptive learning system for autonomous agents

    Learns from experiences to improve decision-making and performance.

    Features:
    - Experience replay buffer
    - Pattern detection and analysis
    - Strategy effectiveness tracking
    - Automated parameter optimization
    - Performance prediction
    """

    def __init__(
        self,
        agent_id: UUID,
        buffer_size: int = 10000,
        min_experiences_for_learning: int = 100,
        pattern_min_support: int = 5,
    ):
        self.agent_id = agent_id
        self.buffer_size = buffer_size
        self.min_experiences_for_learning = min_experiences_for_learning
        self.pattern_min_support = pattern_min_support

        # Experience storage
        self.experience_buffer: Deque[Experience] = deque(maxlen=buffer_size)
        self.experiences_by_type: Dict[ExperienceType, List[Experience]] = defaultdict(list)

        # Strategy tracking
        self.strategy_performance: Dict[str, StrategyPerformance] = {}

        # Pattern detection
        self.detected_patterns: List[Pattern] = []

        # Learning state
        self.total_experiences = 0
        self.learning_iterations = 0
        self.last_learning_time: Optional[datetime] = None

        # Adaptation parameters
        self.adaptation_rate = 0.1  # How quickly to adapt (0.0 to 1.0)
        self.exploration_rate = 0.2  # How often to try new strategies

        # Performance tracking
        self.performance_history: Deque[Dict[str, float]] = deque(maxlen=1000)

        logger.info(f"Adaptive learning system initialized for agent {agent_id}")

    async def record_experience(
        self,
        experience_type: ExperienceType,
        action: str,
        outcome: OutcomeType,
        context: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        state_before: Optional[Dict[str, Any]] = None,
        state_after: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        success_metrics: Optional[Dict[str, float]] = None,
        strategy_used: Optional[str] = None,
    ) -> Experience:
        """
        Record a new experience

        Args:
            experience_type: Type of experience
            action: Action taken
            outcome: Outcome of action
            context: Contextual information
            parameters: Action parameters
            state_before: State before action
            state_after: State after action
            duration: Duration in seconds
            success_metrics: Success metrics
            strategy_used: Strategy that was used

        Returns:
            Created experience
        """
        # Calculate reward based on outcome
        reward = self._calculate_reward(outcome, duration, success_metrics or {})

        experience = Experience(
            type=experience_type,
            context=context or {},
            state_before=state_before or {},
            action=action,
            parameters=parameters or {},
            strategy_used=strategy_used,
            outcome=outcome,
            state_after=state_after or {},
            reward=reward,
            duration=duration,
            success_metrics=success_metrics or {},
        )

        # Add to buffer
        self.experience_buffer.append(experience)
        self.experiences_by_type[experience_type].append(experience)
        self.total_experiences += 1

        # Update strategy performance
        if strategy_used:
            await self._update_strategy_performance(strategy_used, experience)

        # Periodically trigger learning
        if self.total_experiences % 50 == 0:
            asyncio.create_task(self.learn_from_experiences())

        logger.debug(f"Recorded {experience_type.value} experience: {outcome.value}")

        return experience

    def _calculate_reward(
        self,
        outcome: OutcomeType,
        duration: float,
        success_metrics: Dict[str, float],
    ) -> float:
        """
        Calculate reward for an experience

        Returns value between -1.0 and 1.0
        """
        # Base reward from outcome
        outcome_rewards = {
            OutcomeType.SUCCESS: 1.0,
            OutcomeType.PARTIAL: 0.5,
            OutcomeType.FAILURE: -0.5,
            OutcomeType.TIMEOUT: -0.3,
            OutcomeType.CANCELLED: 0.0,
        }
        reward = outcome_rewards.get(outcome, 0.0)

        # Adjust for duration (prefer faster completion)
        if duration > 0:
            # Penalize long durations (exponential decay)
            time_factor = np.exp(-duration / 100)  # 100s half-life
            reward *= time_factor

        # Incorporate success metrics
        if success_metrics:
            metrics_avg = np.mean(list(success_metrics.values()))
            reward = 0.7 * reward + 0.3 * metrics_avg

        return float(np.clip(reward, -1.0, 1.0))

    async def _update_strategy_performance(
        self,
        strategy_name: str,
        experience: Experience,
    ) -> None:
        """Update performance metrics for a strategy"""
        if strategy_name not in self.strategy_performance:
            # Infer strategy type from name or default to generic
            strategy_type = StrategyType.PLANNING  # Default
            if "error" in strategy_name.lower():
                strategy_type = StrategyType.ERROR_HANDLING
            elif "task" in strategy_name.lower():
                strategy_type = StrategyType.TASK_DECOMPOSITION
            elif "comm" in strategy_name.lower():
                strategy_type = StrategyType.COMMUNICATION

            self.strategy_performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                strategy_type=strategy_type,
            )

        self.strategy_performance[strategy_name].update(experience)

    async def learn_from_experiences(self) -> None:
        """
        Perform learning from accumulated experiences

        This includes:
        - Pattern detection
        - Strategy evaluation
        - Parameter optimization
        """
        if len(self.experience_buffer) < self.min_experiences_for_learning:
            logger.debug("Not enough experiences for learning")
            return

        logger.info("Starting learning iteration...")
        self.learning_iterations += 1
        self.last_learning_time = datetime.now()

        try:
            # Detect patterns
            await self._detect_patterns()

            # Evaluate strategies
            await self._evaluate_strategies()

            # Adapt parameters
            await self._adapt_parameters()

            # Update performance history
            self._update_performance_tracking()

            logger.info(
                f"Learning iteration {self.learning_iterations} completed. "
                f"Patterns: {len(self.detected_patterns)}, "
                f"Strategies tracked: {len(self.strategy_performance)}"
            )

        except Exception as e:
            logger.error(f"Error during learning: {e}")

    async def _detect_patterns(self) -> None:
        """Detect patterns in experiences"""
        # Group experiences by context similarity
        success_contexts = []
        failure_contexts = []

        for exp in list(self.experience_buffer):
            if exp.outcome == OutcomeType.SUCCESS:
                success_contexts.append(exp.context)
            elif exp.outcome == OutcomeType.FAILURE:
                failure_contexts.append(exp.context)

        # Detect success patterns
        if len(success_contexts) >= self.pattern_min_support:
            common_keys = self._find_common_keys(success_contexts)
            if common_keys:
                pattern = Pattern(
                    pattern_type="success_conditions",
                    description=f"Common conditions in successful outcomes",
                    conditions={k: "present" for k in common_keys},
                    recommendations=["Apply these conditions for better success"],
                    confidence=len(common_keys) / max(1, len(success_contexts[0])),
                    support_count=len(success_contexts),
                )
                self._add_or_update_pattern(pattern)

        # Detect failure patterns
        if len(failure_contexts) >= self.pattern_min_support:
            common_keys = self._find_common_keys(failure_contexts)
            if common_keys:
                pattern = Pattern(
                    pattern_type="failure_conditions",
                    description=f"Common conditions in failed outcomes",
                    conditions={k: "present" for k in common_keys},
                    recommendations=["Avoid these conditions", "Consider alternative strategies"],
                    confidence=len(common_keys) / max(1, len(failure_contexts[0])),
                    support_count=len(failure_contexts),
                )
                self._add_or_update_pattern(pattern)

    def _find_common_keys(
        self,
        contexts: List[Dict[str, Any]],
        min_frequency: float = 0.7,
    ) -> Set[str]:
        """Find keys that appear frequently across contexts"""
        if not contexts:
            return set()

        key_counts = defaultdict(int)
        for context in contexts:
            for key in context.keys():
                key_counts[key] += 1

        threshold = len(contexts) * min_frequency
        common_keys = {
            key for key, count in key_counts.items()
            if count >= threshold
        }

        return common_keys

    def _add_or_update_pattern(self, pattern: Pattern) -> None:
        """Add new pattern or update existing one"""
        # Check if similar pattern exists
        existing_pattern = None
        for p in self.detected_patterns:
            if p.pattern_type == pattern.pattern_type:
                existing_pattern = p
                break

        if existing_pattern:
            # Update existing pattern
            existing_pattern.conditions = pattern.conditions
            existing_pattern.confidence = pattern.confidence
            existing_pattern.support_count = pattern.support_count
            existing_pattern.recommendations = pattern.recommendations
        else:
            # Add new pattern
            self.detected_patterns.append(pattern)
            logger.info(f"New pattern detected: {pattern.description}")

    async def _evaluate_strategies(self) -> None:
        """Evaluate effectiveness of different strategies"""
        # Sort strategies by effectiveness
        sorted_strategies = sorted(
            self.strategy_performance.values(),
            key=lambda s: s.effectiveness_score,
            reverse=True,
        )

        if sorted_strategies:
            best_strategy = sorted_strategies[0]
            logger.info(
                f"Best performing strategy: {best_strategy.strategy_name} "
                f"(effectiveness: {best_strategy.effectiveness_score:.2f}, "
                f"success rate: {best_strategy.success_rate:.2f})"
            )

            # Identify underperforming strategies
            for strategy in sorted_strategies:
                if (
                    strategy.total_uses >= 10 and
                    strategy.effectiveness_score < 0.3
                ):
                    logger.warning(
                        f"Strategy '{strategy.strategy_name}' is underperforming "
                        f"(effectiveness: {strategy.effectiveness_score:.2f})"
                    )

    async def _adapt_parameters(self) -> None:
        """Adapt learning parameters based on performance"""
        if len(self.performance_history) < 10:
            return

        # Calculate recent performance trend
        recent_performance = list(self.performance_history)[-10:]
        avg_rewards = [p.get("avg_reward", 0) for p in recent_performance]

        if len(avg_rewards) >= 2:
            trend = avg_rewards[-1] - avg_rewards[0]

            # Adapt exploration rate based on performance
            if trend > 0:
                # Performance improving, reduce exploration
                self.exploration_rate = max(0.05, self.exploration_rate * 0.95)
            else:
                # Performance declining, increase exploration
                self.exploration_rate = min(0.5, self.exploration_rate * 1.1)

            logger.debug(f"Adapted exploration rate to {self.exploration_rate:.3f}")

    def _update_performance_tracking(self) -> None:
        """Update overall performance tracking"""
        if not self.experience_buffer:
            return

        # Calculate recent performance
        recent_experiences = list(self.experience_buffer)[-100:]
        avg_reward = np.mean([exp.reward for exp in recent_experiences])
        success_rate = sum(
            1 for exp in recent_experiences
            if exp.outcome == OutcomeType.SUCCESS
        ) / len(recent_experiences)

        self.performance_history.append({
            "timestamp": datetime.now().isoformat(),
            "avg_reward": float(avg_reward),
            "success_rate": float(success_rate),
            "total_experiences": self.total_experiences,
        })

    def recommend_strategy(
        self,
        strategy_type: StrategyType,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Recommend best strategy based on learning

        Args:
            strategy_type: Type of strategy needed
            context: Current context

        Returns:
            Recommended strategy name or None
        """
        # Filter strategies by type
        candidates = [
            s for s in self.strategy_performance.values()
            if s.strategy_type == strategy_type and s.total_uses >= 3
        ]

        if not candidates:
            return None

        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            # Explore: choose randomly
            strategy = np.random.choice(candidates)
            logger.debug(f"Exploring strategy: {strategy.strategy_name}")
        else:
            # Exploit: choose best performing
            strategy = max(candidates, key=lambda s: s.effectiveness_score)
            logger.debug(f"Exploiting best strategy: {strategy.strategy_name}")

        return strategy.strategy_name

    def get_pattern_recommendations(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Get recommendations based on detected patterns"""
        recommendations = []

        for pattern in self.detected_patterns:
            if pattern.confidence >= 0.5:  # Only use high-confidence patterns
                recommendations.extend(pattern.recommendations)

        return recommendations

    def predict_success_probability(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Predict probability of success for an action

        Args:
            action: Action to predict
            context: Current context

        Returns:
            Predicted success probability (0.0 to 1.0)
        """
        # Find similar past experiences
        similar_experiences = [
            exp for exp in self.experience_buffer
            if exp.action == action
        ]

        if not similar_experiences:
            return 0.5  # No data, neutral prediction

        # Calculate success rate from similar experiences
        successes = sum(
            1 for exp in similar_experiences
            if exp.outcome == OutcomeType.SUCCESS
        )

        return successes / len(similar_experiences)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        avg_reward = (
            np.mean([exp.reward for exp in self.experience_buffer])
            if self.experience_buffer else 0.0
        )

        success_count = sum(
            1 for exp in self.experience_buffer
            if exp.outcome == OutcomeType.SUCCESS
        )

        return {
            "agent_id": str(self.agent_id),
            "total_experiences": self.total_experiences,
            "buffer_size": len(self.experience_buffer),
            "learning_iterations": self.learning_iterations,
            "last_learning_time": (
                self.last_learning_time.isoformat()
                if self.last_learning_time else None
            ),
            "average_reward": float(avg_reward),
            "success_rate": (
                success_count / len(self.experience_buffer)
                if self.experience_buffer else 0.0
            ),
            "strategies_tracked": len(self.strategy_performance),
            "patterns_detected": len(self.detected_patterns),
            "exploration_rate": self.exploration_rate,
            "adaptation_rate": self.adaptation_rate,
            "top_strategies": [
                {
                    "name": s.strategy_name,
                    "effectiveness": s.effectiveness_score,
                    "success_rate": s.success_rate,
                    "uses": s.total_uses,
                }
                for s in sorted(
                    self.strategy_performance.values(),
                    key=lambda x: x.effectiveness_score,
                    reverse=True,
                )[:5]
            ],
        }

    async def export_knowledge(self) -> Dict[str, Any]:
        """
        Export learned knowledge for sharing or persistence

        Returns:
            Knowledge dictionary
        """
        return {
            "agent_id": str(self.agent_id),
            "timestamp": datetime.now().isoformat(),
            "strategy_performance": {
                name: {
                    "type": str(perf.strategy_type),
                    "effectiveness": perf.effectiveness_score,
                    "success_rate": perf.success_rate,
                    "total_uses": perf.total_uses,
                }
                for name, perf in self.strategy_performance.items()
            },
            "patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "recommendations": p.recommendations,
                }
                for p in self.detected_patterns
            ],
            "performance_summary": self.get_learning_summary(),
        }

    async def import_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """
        Import knowledge from another agent or storage

        Args:
            knowledge: Knowledge dictionary
        """
        logger.info(f"Importing knowledge from {knowledge.get('agent_id')}")

        # Import strategy performance (weighted merge with existing)
        if "strategy_performance" in knowledge:
            for name, perf_data in knowledge["strategy_performance"].items():
                if name in self.strategy_performance:
                    # Merge with existing
                    existing = self.strategy_performance[name]
                    weight = 0.3  # Weight for imported knowledge

                    existing.effectiveness_score = (
                        (1 - weight) * existing.effectiveness_score +
                        weight * perf_data["effectiveness"]
                    )
                    existing.success_rate = (
                        (1 - weight) * existing.success_rate +
                        weight * perf_data["success_rate"]
                    )
                # else: could import new strategies

        logger.info("Knowledge import completed")
