"""
Context Optimizer

Main orchestrator that integrates all context optimization strategies:
- Pruning (remove irrelevant/redundant content)
- Compression (reduce size while preserving meaning)
- Validation (ensure quality and consistency)

Provides adaptive optimization based on context size and requirements.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel, Field

from iras.optimization.compression import (
    CompressionConfig,
    CompressionResult,
    CompressionStrategy,
    ContextCompressor,
    TokenCounter,
)
from iras.optimization.pruning import (
    ContextItem,
    ContextPruner,
    PruningConfig,
    PruningStrategy,
)
from iras.optimization.validation import (
    ContextValidator,
    ValidationCheck,
    ValidationConfig,
    ValidationResult,
    ValidationSeverity,
)


class OptimizationMode(str, Enum):
    """Optimization modes"""

    AGGRESSIVE = "aggressive"  # Maximum compression, minimal validation
    BALANCED = "balanced"  # Balance between quality and size
    CONSERVATIVE = "conservative"  # Preserve quality, minimal compression
    CUSTOM = "custom"  # User-defined settings


class OptimizationConfig(BaseModel):
    """Configuration for context optimization"""

    mode: OptimizationMode = OptimizationMode.BALANCED

    # Target constraints
    target_token_count: Optional[int] = None
    max_token_count: Optional[int] = 4000
    min_quality_score: float = Field(default=0.7, ge=0.0, le=1.0)

    # Strategy selection
    enable_pruning: bool = True
    enable_compression: bool = True
    enable_validation: bool = True

    # Sub-configurations
    pruning_config: Optional[PruningConfig] = None
    compression_config: Optional[CompressionConfig] = None
    validation_config: Optional[ValidationConfig] = None

    # Adaptive settings
    adaptive_optimization: bool = True
    optimization_rounds: int = Field(default=3, ge=1, le=10)

    # Performance settings
    parallel_processing: bool = True
    timeout_seconds: float = 30.0

    class Config:
        use_enum_values = True

    def __init__(self, **data):
        super().__init__(**data)
        # Set default sub-configs based on mode if not provided
        if self.pruning_config is None:
            self.pruning_config = self._get_default_pruning_config()
        if self.compression_config is None:
            self.compression_config = self._get_default_compression_config()
        if self.validation_config is None:
            self.validation_config = self._get_default_validation_config()

    def _get_default_pruning_config(self) -> PruningConfig:
        """Get default pruning config based on mode"""
        if self.mode == OptimizationMode.AGGRESSIVE:
            return PruningConfig(
                strategy=PruningStrategy.HYBRID,
                max_tokens=self.max_token_count,
                similarity_threshold=0.75,  # More aggressive deduplication
                relevance_threshold=0.4,
            )
        elif self.mode == OptimizationMode.CONSERVATIVE:
            return PruningConfig(
                strategy=PruningStrategy.IMPORTANCE_WEIGHTED,
                max_tokens=self.max_token_count,
                similarity_threshold=0.95,  # Less deduplication
                relevance_threshold=0.2,
            )
        else:  # BALANCED
            return PruningConfig(
                strategy=PruningStrategy.HYBRID,
                max_tokens=self.max_token_count,
                similarity_threshold=0.85,
                relevance_threshold=0.3,
            )

    def _get_default_compression_config(self) -> CompressionConfig:
        """Get default compression config based on mode"""
        if self.mode == OptimizationMode.AGGRESSIVE:
            return CompressionConfig(
                strategy=CompressionStrategy.HYBRID,
                target_ratio=0.4,  # Aggressive compression
                max_chunk_size=512,
            )
        elif self.mode == OptimizationMode.CONSERVATIVE:
            return CompressionConfig(
                strategy=CompressionStrategy.EXTRACTIVE,
                target_ratio=0.7,  # Light compression
                max_chunk_size=1024,
            )
        else:  # BALANCED
            return CompressionConfig(
                strategy=CompressionStrategy.HYBRID,
                target_ratio=0.5,
                max_chunk_size=768,
            )

    def _get_default_validation_config(self) -> ValidationConfig:
        """Get default validation config based on mode"""
        if self.mode == OptimizationMode.AGGRESSIVE:
            return ValidationConfig(
                max_age_seconds=7200.0,  # More lenient
                relevance_threshold=0.2,
                check_contradictions=False,  # Skip for speed
                check_factual_consistency=False,
                strict_mode=False,
            )
        elif self.mode == OptimizationMode.CONSERVATIVE:
            return ValidationConfig(
                max_age_seconds=1800.0,  # Strict
                relevance_threshold=0.4,
                check_contradictions=True,
                check_factual_consistency=True,
                strict_mode=True,
            )
        else:  # BALANCED
            return ValidationConfig(
                max_age_seconds=3600.0,
                relevance_threshold=0.3,
                check_contradictions=True,
                check_factual_consistency=True,
                strict_mode=False,
            )


@dataclass
class OptimizationMetrics:
    """Metrics from optimization process"""

    # Token metrics
    original_tokens: int
    final_tokens: int
    token_reduction: int
    compression_ratio: float

    # Item metrics
    original_items: int
    final_items: int
    items_removed: int
    removal_ratio: float

    # Quality metrics
    validation_score: float
    quality_preserved: bool

    # Performance metrics
    duration_seconds: float
    rounds_executed: int

    # Stage-specific metrics
    pruning_metrics: Dict[str, Any] = field(default_factory=dict)
    compression_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tokens": {
                "original": self.original_tokens,
                "final": self.final_tokens,
                "reduction": self.token_reduction,
                "compression_ratio": self.compression_ratio,
            },
            "items": {
                "original": self.original_items,
                "final": self.final_items,
                "removed": self.items_removed,
                "removal_ratio": self.removal_ratio,
            },
            "quality": {
                "validation_score": self.validation_score,
                "quality_preserved": self.quality_preserved,
            },
            "performance": {
                "duration_seconds": self.duration_seconds,
                "rounds_executed": self.rounds_executed,
            },
            "stages": {
                "pruning": self.pruning_metrics,
                "compression": self.compression_metrics,
                "validation": self.validation_metrics,
            },
        }


@dataclass
class OptimizationResult:
    """Result of context optimization"""

    success: bool
    optimized_items: List[ContextItem]
    optimized_text: str
    metrics: OptimizationMetrics
    validation_result: ValidationResult
    issues: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of optimization"""
        return {
            "success": self.success,
            "items_count": len(self.optimized_items),
            "token_count": self.metrics.final_tokens,
            "compression_ratio": self.metrics.compression_ratio,
            "validation_score": self.metrics.validation_score,
            "issues_count": len(self.issues),
            "duration": self.metrics.duration_seconds,
        }


class ContextOptimizer:
    """
    Main context optimizer

    Integrates pruning, compression, and validation for optimal context management
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()

        # Initialize components
        self.pruner = ContextPruner(self.config.pruning_config)
        self.compressor = ContextCompressor(self.config.compression_config)
        self.validator = ContextValidator(self.config.validation_config)

        logger.info(
            f"ContextOptimizer initialized in {self.config.mode} mode"
        )

    async def optimize(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> OptimizationResult:
        """
        Optimize context items

        Args:
            items: List of context items to optimize
            query: Optional query for relevance-based optimization

        Returns:
            Optimization result with metrics
        """
        if not items:
            return OptimizationResult(
                success=True,
                optimized_items=[],
                optimized_text="",
                metrics=self._create_empty_metrics(),
                validation_result=ValidationResult(is_valid=True, score=1.0),
            )

        logger.info(
            f"Starting optimization of {len(items)} items "
            f"(mode={self.config.mode}, query={'provided' if query else 'none'})"
        )

        start_time = datetime.now()
        original_items = items.copy()
        original_tokens = sum(
            TokenCounter.count_tokens(item.content) for item in items
        )

        try:
            # Run optimization pipeline
            if self.config.adaptive_optimization:
                result = await self._adaptive_optimize(items, query, original_tokens)
            else:
                result = await self._standard_optimize(items, query)

            # Calculate final metrics
            final_tokens = sum(
                TokenCounter.count_tokens(item.content)
                for item in result.optimized_items
            )

            duration = (datetime.now() - start_time).total_seconds()

            # Create metrics
            metrics = OptimizationMetrics(
                original_tokens=original_tokens,
                final_tokens=final_tokens,
                token_reduction=original_tokens - final_tokens,
                compression_ratio=(
                    final_tokens / original_tokens if original_tokens > 0 else 1.0
                ),
                original_items=len(original_items),
                final_items=len(result.optimized_items),
                items_removed=len(original_items) - len(result.optimized_items),
                removal_ratio=(
                    (len(original_items) - len(result.optimized_items))
                    / len(original_items)
                    if len(original_items) > 0
                    else 0.0
                ),
                validation_score=result.validation_result.score,
                quality_preserved=(
                    result.validation_result.score >= self.config.min_quality_score
                ),
                duration_seconds=duration,
                rounds_executed=getattr(result, "rounds", 1),
            )

            result.metrics = metrics

            logger.info(
                f"Optimization complete: {original_tokens} -> {final_tokens} tokens "
                f"({metrics.compression_ratio:.2%}), "
                f"score={metrics.validation_score:.3f}, {duration:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()

            return OptimizationResult(
                success=False,
                optimized_items=items,
                optimized_text=self._items_to_text(items),
                metrics=OptimizationMetrics(
                    original_tokens=original_tokens,
                    final_tokens=original_tokens,
                    token_reduction=0,
                    compression_ratio=1.0,
                    original_items=len(items),
                    final_items=len(items),
                    items_removed=0,
                    removal_ratio=0.0,
                    validation_score=0.0,
                    quality_preserved=False,
                    duration_seconds=duration,
                    rounds_executed=0,
                ),
                validation_result=ValidationResult(is_valid=False, score=0.0),
                issues=[str(e)],
            )

    async def _standard_optimize(
        self,
        items: List[ContextItem],
        query: Optional[str],
    ) -> OptimizationResult:
        """Standard single-pass optimization"""
        current_items = items.copy()
        issues = []

        # Step 1: Validation (pre-optimization)
        if self.config.enable_validation:
            validation_result = await self.validator.validate(current_items, query)
            if not validation_result.is_valid and self.config.validation_config.strict_mode:
                issues.append("Pre-optimization validation failed")
        else:
            validation_result = ValidationResult(is_valid=True, score=1.0)

        # Step 2: Pruning
        if self.config.enable_pruning:
            current_items = await self.pruner.prune(current_items, query)
            logger.debug(f"After pruning: {len(current_items)} items")

        # Step 3: Compression (if needed)
        if self.config.enable_compression:
            current_text = self._items_to_text(current_items)
            current_tokens = TokenCounter.count_tokens(current_text)

            if (
                self.config.max_token_count
                and current_tokens > self.config.max_token_count
            ):
                compression_result = await self.compressor.compress(current_text)
                # Convert compressed text back to items
                current_items = [
                    ContextItem(
                        id=f"compressed_{datetime.now().timestamp()}",
                        content=compression_result.compressed_text,
                    )
                ]
                logger.debug(
                    f"After compression: {compression_result.compressed_tokens} tokens"
                )

        # Step 4: Final validation
        if self.config.enable_validation:
            validation_result = await self.validator.validate(current_items, query)
            if not validation_result.is_valid:
                issues.append("Post-optimization validation failed")

        return OptimizationResult(
            success=len(issues) == 0,
            optimized_items=current_items,
            optimized_text=self._items_to_text(current_items),
            metrics=None,  # Will be filled by optimize()
            validation_result=validation_result,
            issues=issues,
        )

    async def _adaptive_optimize(
        self,
        items: List[ContextItem],
        query: Optional[str],
        original_tokens: int,
    ) -> OptimizationResult:
        """
        Adaptive multi-round optimization

        Progressively optimizes until constraints are met or max rounds reached
        """
        current_items = items.copy()
        issues = []
        rounds_executed = 0

        for round_num in range(self.config.optimization_rounds):
            rounds_executed += 1
            logger.debug(f"Optimization round {round_num + 1}")

            # Check if we've met our goals
            current_tokens = sum(
                TokenCounter.count_tokens(item.content) for item in current_items
            )

            target_met = True
            if self.config.target_token_count:
                target_met = current_tokens <= self.config.target_token_count
            elif self.config.max_token_count:
                target_met = current_tokens <= self.config.max_token_count

            if target_met and round_num > 0:
                logger.debug(f"Target met after {round_num + 1} rounds")
                break

            # Perform optimization round
            round_result = await self._standard_optimize(current_items, query)
            current_items = round_result.optimized_items

            # Check quality
            if round_result.validation_result.score < self.config.min_quality_score:
                logger.warning(
                    f"Quality threshold not met: "
                    f"{round_result.validation_result.score:.3f} < "
                    f"{self.config.min_quality_score}"
                )
                if self.config.validation_config.strict_mode:
                    issues.append("Quality threshold not met")
                    break

            # Update pruning aggressiveness for next round
            if round_num < self.config.optimization_rounds - 1:
                self._adjust_aggressiveness(current_tokens)

        # Final validation
        validation_result = await self.validator.validate(current_items, query)

        result = OptimizationResult(
            success=len(issues) == 0,
            optimized_items=current_items,
            optimized_text=self._items_to_text(current_items),
            metrics=None,  # Will be filled by optimize()
            validation_result=validation_result,
            issues=issues,
        )
        result.rounds = rounds_executed

        return result

    def _adjust_aggressiveness(self, current_tokens: int) -> None:
        """Adjust optimization aggressiveness based on current state"""
        if not self.config.target_token_count:
            return

        # Calculate how far we are from target
        ratio = current_tokens / self.config.target_token_count

        if ratio > 1.5:
            # Still far from target, increase aggressiveness
            if self.config.pruning_config:
                self.config.pruning_config.similarity_threshold *= 0.95
                self.config.pruning_config.relevance_threshold *= 1.1

            if self.config.compression_config:
                self.config.compression_config.target_ratio *= 0.9

            logger.debug("Increased optimization aggressiveness")

    def _items_to_text(self, items: List[ContextItem]) -> str:
        """Convert items to concatenated text"""
        return "\n\n".join(item.content for item in items)

    def _create_empty_metrics(self) -> OptimizationMetrics:
        """Create empty metrics"""
        return OptimizationMetrics(
            original_tokens=0,
            final_tokens=0,
            token_reduction=0,
            compression_ratio=1.0,
            original_items=0,
            final_items=0,
            items_removed=0,
            removal_ratio=0.0,
            validation_score=1.0,
            quality_preserved=True,
            duration_seconds=0.0,
            rounds_executed=0,
        )

    async def optimize_text(
        self,
        text: str,
        query: Optional[str] = None,
    ) -> OptimizationResult:
        """
        Optimize raw text (convenience method)

        Args:
            text: Text to optimize
            query: Optional query for relevance-based optimization

        Returns:
            Optimization result
        """
        # Convert text to items
        items = [
            ContextItem(
                id=f"text_{datetime.now().timestamp()}",
                content=text,
            )
        ]

        return await self.optimize(items, query)

    def update_config(self, config: OptimizationConfig) -> None:
        """Update optimization configuration"""
        self.config = config

        # Update sub-components
        if config.pruning_config:
            self.pruner.update_config(config.pruning_config)
        if config.compression_config:
            self.compressor.update_config(config.compression_config)
        if config.validation_config:
            self.validator.update_config(config.validation_config)

        logger.info(f"Configuration updated to {config.mode} mode")

    async def validate_only(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> ValidationResult:
        """Run validation only (no optimization)"""
        return await self.validator.validate(items, query)

    async def prune_only(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Run pruning only (no compression or validation)"""
        return await self.pruner.prune(items, query)

    async def compress_only(
        self,
        text: str,
    ) -> CompressionResult:
        """Run compression only (no pruning or validation)"""
        return await self.compressor.compress(text)

    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "mode": self.config.mode,
            "max_token_count": self.config.max_token_count,
            "target_token_count": self.config.target_token_count,
            "min_quality_score": self.config.min_quality_score,
            "pruning_enabled": self.config.enable_pruning,
            "compression_enabled": self.config.enable_compression,
            "validation_enabled": self.config.enable_validation,
            "adaptive_optimization": self.config.adaptive_optimization,
        }


# Convenience functions

async def optimize_context(
    items: List[ContextItem],
    mode: OptimizationMode = OptimizationMode.BALANCED,
    query: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> OptimizationResult:
    """
    Convenience function for context optimization

    Args:
        items: Context items to optimize
        mode: Optimization mode
        query: Optional query for relevance
        max_tokens: Maximum token count

    Returns:
        Optimization result
    """
    config = OptimizationConfig(
        mode=mode,
        max_token_count=max_tokens or 4000,
    )

    optimizer = ContextOptimizer(config)
    return await optimizer.optimize(items, query)


async def optimize_text(
    text: str,
    mode: OptimizationMode = OptimizationMode.BALANCED,
    query: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Convenience function for text optimization

    Args:
        text: Text to optimize
        mode: Optimization mode
        query: Optional query for relevance
        max_tokens: Maximum token count

    Returns:
        Optimized text
    """
    result = await optimize_context(
        items=[ContextItem(id="text", content=text)],
        mode=mode,
        query=query,
        max_tokens=max_tokens,
    )

    return result.optimized_text
