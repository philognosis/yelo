"""
Context Pruning Strategies

Implements various pruning strategies to reduce context size while
maintaining relevance and quality:
- Recency-based pruning
- Semantic similarity pruning
- Query-relevance pruning
- Importance-weighted pruning
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class PruningStrategy(str, Enum):
    """Available pruning strategies"""

    RECENCY = "recency"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    QUERY_RELEVANCE = "query_relevance"
    IMPORTANCE_WEIGHTED = "importance_weighted"
    HYBRID = "hybrid"


class ContextItem(BaseModel):
    """Represents a single context item"""

    id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True


class PruningConfig(BaseModel):
    """Configuration for pruning operations"""

    strategy: PruningStrategy = PruningStrategy.HYBRID
    max_items: Optional[int] = None
    max_tokens: Optional[int] = None
    max_age_seconds: Optional[float] = None
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    relevance_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    importance_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    recency_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    relevance_weight: float = Field(default=0.3, ge=0.0, le=1.0)


class BasePruner(ABC):
    """Base class for all pruning strategies"""

    def __init__(self, config: PruningConfig):
        self.config = config

    @abstractmethod
    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """
        Prune context items

        Args:
            items: List of context items to prune
            query: Optional query for relevance-based pruning

        Returns:
            Pruned list of context items
        """
        pass

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text (placeholder implementation)

        In production, this would use a real embedding model
        """
        # Simple hash-based pseudo-embedding for demonstration
        # Replace with actual embedding model (e.g., sentence-transformers)
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(384)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


class RecencyPruner(BasePruner):
    """
    Recency-based pruning

    Keeps most recent items based on timestamp
    """

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Prune based on recency"""
        if not items:
            return []

        # Sort by timestamp (newest first)
        sorted_items = sorted(
            items,
            key=lambda x: x.timestamp,
            reverse=True,
        )

        # Filter by age if configured
        if self.config.max_age_seconds:
            cutoff_time = datetime.now() - timedelta(seconds=self.config.max_age_seconds)
            sorted_items = [item for item in sorted_items if item.timestamp >= cutoff_time]

        # Limit by count
        if self.config.max_items:
            sorted_items = sorted_items[: self.config.max_items]

        # Limit by tokens
        if self.config.max_tokens:
            sorted_items = self._limit_by_tokens(sorted_items, self.config.max_tokens)

        logger.debug(
            f"Recency pruning: {len(items)} -> {len(sorted_items)} items"
        )

        return sorted_items

    def _limit_by_tokens(
        self,
        items: List[ContextItem],
        max_tokens: int,
    ) -> List[ContextItem]:
        """Limit items by token count"""
        total_tokens = 0
        result = []

        for item in items:
            item_tokens = item.token_count or len(item.content.split())
            if total_tokens + item_tokens <= max_tokens:
                result.append(item)
                total_tokens += item_tokens
            else:
                break

        return result


class SemanticSimilarityPruner(BasePruner):
    """
    Semantic similarity-based pruning

    Removes redundant content that is semantically similar
    """

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Prune based on semantic similarity"""
        if not items:
            return []

        # Generate embeddings for all items
        for item in items:
            if item.embedding is None:
                embedding = self._get_embedding(item.content)
                item.embedding = embedding.tolist()

        # Keep track of unique items
        unique_items = []
        embeddings = []

        for item in items:
            item_embedding = np.array(item.embedding)

            # Check similarity with existing unique items
            is_unique = True
            for existing_embedding in embeddings:
                similarity = self._cosine_similarity(item_embedding, existing_embedding)
                if similarity >= self.config.similarity_threshold:
                    is_unique = False
                    break

            if is_unique:
                unique_items.append(item)
                embeddings.append(item_embedding)

        logger.debug(
            f"Semantic pruning: {len(items)} -> {len(unique_items)} items "
            f"(threshold={self.config.similarity_threshold})"
        )

        return unique_items


class QueryRelevancePruner(BasePruner):
    """
    Query-relevance based pruning

    Keeps only items relevant to the current query
    """

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Prune based on query relevance"""
        if not items:
            return []

        if not query:
            logger.warning("Query relevance pruning requires a query")
            return items

        # Get query embedding
        query_embedding = self._get_embedding(query)

        # Calculate relevance scores
        scored_items = []
        for item in items:
            if item.embedding is None:
                item.embedding = self._get_embedding(item.content).tolist()

            item_embedding = np.array(item.embedding)
            relevance = self._cosine_similarity(query_embedding, item_embedding)

            if relevance >= self.config.relevance_threshold:
                scored_items.append((relevance, item))

        # Sort by relevance (highest first)
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Extract items
        relevant_items = [item for _, item in scored_items]

        # Apply limits
        if self.config.max_items:
            relevant_items = relevant_items[: self.config.max_items]

        logger.debug(
            f"Relevance pruning: {len(items)} -> {len(relevant_items)} items "
            f"(threshold={self.config.relevance_threshold})"
        )

        return relevant_items


class ImportanceWeightedPruner(BasePruner):
    """
    Importance-weighted pruning

    Combines multiple factors (importance, recency, relevance) with weights
    """

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Prune based on weighted importance score"""
        if not items:
            return []

        # Get query embedding if available
        query_embedding = None
        if query:
            query_embedding = self._get_embedding(query)

        # Calculate composite scores
        scored_items = []
        now = datetime.now()

        for item in items:
            # Importance score (from item)
            importance_score = item.importance

            # Recency score (0-1, based on age)
            age_seconds = (now - item.timestamp).total_seconds()
            max_age = self.config.max_age_seconds or 3600  # Default 1 hour
            recency_score = max(0.0, 1.0 - (age_seconds / max_age))

            # Relevance score (if query provided)
            relevance_score = 0.5  # Default neutral score
            if query_embedding is not None:
                if item.embedding is None:
                    item.embedding = self._get_embedding(item.content).tolist()
                item_embedding = np.array(item.embedding)
                relevance_score = (
                    self._cosine_similarity(query_embedding, item_embedding) + 1.0
                ) / 2.0  # Normalize to 0-1

            # Composite score
            composite_score = (
                self.config.importance_weight * importance_score
                + self.config.recency_weight * recency_score
                + self.config.relevance_weight * relevance_score
            )

            scored_items.append((composite_score, item))

        # Sort by composite score (highest first)
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Extract items
        pruned_items = [item for _, item in scored_items]

        # Apply limits
        if self.config.max_items:
            pruned_items = pruned_items[: self.config.max_items]

        if self.config.max_tokens:
            pruned_items = self._limit_by_tokens(pruned_items, self.config.max_tokens)

        logger.debug(
            f"Importance-weighted pruning: {len(items)} -> {len(pruned_items)} items"
        )

        return pruned_items

    def _limit_by_tokens(
        self,
        items: List[ContextItem],
        max_tokens: int,
    ) -> List[ContextItem]:
        """Limit items by token count"""
        total_tokens = 0
        result = []

        for item in items:
            item_tokens = item.token_count or len(item.content.split())
            if total_tokens + item_tokens <= max_tokens:
                result.append(item)
                total_tokens += item_tokens
            else:
                break

        return result


class HybridPruner(BasePruner):
    """
    Hybrid pruning strategy

    Combines multiple pruning strategies in sequence
    """

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
    ) -> List[ContextItem]:
        """Apply multiple pruning strategies in sequence"""
        if not items:
            return []

        current_items = items.copy()

        # Step 1: Remove duplicates/similar items
        semantic_pruner = SemanticSimilarityPruner(self.config)
        current_items = await semantic_pruner.prune(current_items, query)

        # Step 2: Filter by relevance if query provided
        if query:
            relevance_pruner = QueryRelevancePruner(self.config)
            current_items = await relevance_pruner.prune(current_items, query)

        # Step 3: Apply importance-weighted scoring
        weighted_pruner = ImportanceWeightedPruner(self.config)
        current_items = await weighted_pruner.prune(current_items, query)

        logger.debug(f"Hybrid pruning: {len(items)} -> {len(current_items)} items")

        return current_items


class ContextPruner:
    """
    Main context pruner that dispatches to specific strategies
    """

    def __init__(self, config: Optional[PruningConfig] = None):
        self.config = config or PruningConfig()
        self._pruners: Dict[PruningStrategy, BasePruner] = {
            PruningStrategy.RECENCY: RecencyPruner(self.config),
            PruningStrategy.SEMANTIC_SIMILARITY: SemanticSimilarityPruner(self.config),
            PruningStrategy.QUERY_RELEVANCE: QueryRelevancePruner(self.config),
            PruningStrategy.IMPORTANCE_WEIGHTED: ImportanceWeightedPruner(self.config),
            PruningStrategy.HYBRID: HybridPruner(self.config),
        }

    async def prune(
        self,
        items: List[ContextItem],
        query: Optional[str] = None,
        strategy: Optional[PruningStrategy] = None,
    ) -> List[ContextItem]:
        """
        Prune context items using specified strategy

        Args:
            items: List of context items to prune
            query: Optional query for relevance-based pruning
            strategy: Pruning strategy to use (overrides config)

        Returns:
            Pruned list of context items
        """
        if not items:
            return []

        strategy = strategy or self.config.strategy
        pruner = self._pruners[strategy]

        logger.info(
            f"Pruning {len(items)} items using {strategy.value} strategy"
        )

        start_time = datetime.now()
        pruned_items = await pruner.prune(items, query)
        duration = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Pruning complete: {len(items)} -> {len(pruned_items)} items "
            f"({duration:.3f}s)"
        )

        return pruned_items

    def update_config(self, config: PruningConfig) -> None:
        """Update pruning configuration"""
        self.config = config
        # Recreate pruners with new config
        self._pruners = {
            PruningStrategy.RECENCY: RecencyPruner(self.config),
            PruningStrategy.SEMANTIC_SIMILARITY: SemanticSimilarityPruner(self.config),
            PruningStrategy.QUERY_RELEVANCE: QueryRelevancePruner(self.config),
            PruningStrategy.IMPORTANCE_WEIGHTED: ImportanceWeightedPruner(self.config),
            PruningStrategy.HYBRID: HybridPruner(self.config),
        }


async def prune_context(
    items: List[ContextItem],
    strategy: PruningStrategy = PruningStrategy.HYBRID,
    query: Optional[str] = None,
    max_items: Optional[int] = None,
    max_tokens: Optional[int] = None,
) -> List[ContextItem]:
    """
    Convenience function for context pruning

    Args:
        items: List of context items to prune
        strategy: Pruning strategy to use
        query: Optional query for relevance-based pruning
        max_items: Maximum number of items to keep
        max_tokens: Maximum token count to keep

    Returns:
        Pruned list of context items
    """
    config = PruningConfig(
        strategy=strategy,
        max_items=max_items,
        max_tokens=max_tokens,
    )

    pruner = ContextPruner(config)
    return await pruner.prune(items, query)
