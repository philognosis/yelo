"""
Agent Memory System

Implements multi-tiered memory with:
- Working memory (short-term, limited capacity)
- Episodic memory (experience-based)
- Semantic memory (knowledge-based, vector embeddings)
- Procedural memory (skills and procedures)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class MemoryType(str):
    """Memory classification types"""

    WORKING = "working"  # Short-term, high-access
    EPISODIC = "episodic"  # Experience-based
    SEMANTIC = "semantic"  # Knowledge-based
    PROCEDURAL = "procedural"  # Skills/procedures


@dataclass
class MemoryItem:
    """Individual memory item with metadata"""

    id: UUID
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    access_count: int = 0
    last_accessed: datetime = None
    importance: float = 0.5  # 0.0 to 1.0
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        if self.metadata is None:
            self.metadata = {}

    def access(self) -> None:
        """Record memory access"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def recency_score(self, decay_rate: float = 0.1) -> float:
        """
        Calculate recency score with exponential decay

        Args:
            decay_rate: Rate of decay (higher = faster decay)

        Returns:
            Score between 0 and 1
        """
        hours_since_access = (datetime.now() - self.last_accessed).total_seconds() / 3600
        return float(np.exp(-decay_rate * hours_since_access))

    def relevance_score(
        self, query_embedding: Optional[np.ndarray] = None, query_text: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score

        Combines:
        - Semantic similarity (if embeddings available)
        - Recency
        - Importance
        - Access frequency
        """
        scores = []

        # Semantic similarity
        if query_embedding is not None and self.embedding is not None:
            similarity = float(
                np.dot(query_embedding, self.embedding)
                / (np.linalg.norm(query_embedding) * np.linalg.norm(self.embedding) + 1e-8)
            )
            scores.append(similarity)

        # Recency
        scores.append(self.recency_score())

        # Importance
        scores.append(self.importance)

        # Access frequency (normalized)
        max_access = 100  # Assumed maximum
        scores.append(min(1.0, self.access_count / max_access))

        # Weighted average
        weights = [0.4, 0.3, 0.2, 0.1]  # Semantic, recency, importance, frequency
        return float(np.average(scores[: len(scores)], weights=weights[: len(scores)]))


class WorkingMemory:
    """
    Short-term working memory with limited capacity

    Implements:
    - FIFO eviction when capacity exceeded
    - Importance-based retention
    - Fast access patterns
    """

    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.items: Deque[MemoryItem] = deque(maxlen=capacity)
        self._lock = asyncio.Lock()

    async def add(self, content: Any, importance: float = 0.5, metadata: Optional[Dict] = None) -> UUID:
        """Add item to working memory"""
        async with self._lock:
            item = MemoryItem(
                id=uuid4(),
                content=content,
                memory_type=MemoryType.WORKING,
                timestamp=datetime.now(),
                importance=importance,
                metadata=metadata or {},
            )
            self.items.append(item)
            return item.id

    async def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get most recent items"""
        async with self._lock:
            return list(self.items)[-limit:]

    async def clear(self) -> None:
        """Clear working memory"""
        async with self._lock:
            self.items.clear()

    def get_all(self) -> List[MemoryItem]:
        """Get all items (synchronous)"""
        return list(self.items)


class EpisodicMemory:
    """
    Long-term episodic memory for experiences

    Stores:
    - Events and experiences
    - Temporal relationships
    - Contextual information
    """

    def __init__(self, max_episodes: int = 10000):
        self.max_episodes = max_episodes
        self.episodes: List[MemoryItem] = []
        self._lock = asyncio.Lock()
        self._index: Dict[UUID, int] = {}  # Fast lookup

    async def add_episode(
        self,
        content: Any,
        importance: float = 0.5,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict] = None,
    ) -> UUID:
        """Add new episode"""
        async with self._lock:
            item = MemoryItem(
                id=uuid4(),
                content=content,
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now(),
                importance=importance,
                embedding=embedding,
                metadata=metadata or {},
            )

            self.episodes.append(item)
            self._index[item.id] = len(self.episodes) - 1

            # Prune if exceeded capacity
            if len(self.episodes) > self.max_episodes:
                await self._prune_episodes()

            return item.id

    async def get_episode(self, episode_id: UUID) -> Optional[MemoryItem]:
        """Retrieve specific episode"""
        async with self._lock:
            idx = self._index.get(episode_id)
            if idx is not None and idx < len(self.episodes):
                episode = self.episodes[idx]
                episode.access()
                return episode
            return None

    async def search_episodes(
        self,
        query_embedding: Optional[np.ndarray] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryItem]:
        """
        Search episodes by multiple criteria

        Args:
            query_embedding: Semantic search vector
            start_time: Filter by time range
            end_time: Filter by time range
            limit: Maximum results
            min_importance: Minimum importance threshold

        Returns:
            List of matching episodes, ranked by relevance
        """
        async with self._lock:
            # Filter episodes
            candidates = self.episodes

            if start_time:
                candidates = [e for e in candidates if e.timestamp >= start_time]
            if end_time:
                candidates = [e for e in candidates if e.timestamp <= end_time]
            if min_importance > 0:
                candidates = [e for e in candidates if e.importance >= min_importance]

            # Rank by relevance
            scored_episodes = [
                (episode, episode.relevance_score(query_embedding=query_embedding))
                for episode in candidates
            ]
            scored_episodes.sort(key=lambda x: x[1], reverse=True)

            # Mark as accessed
            results = [episode for episode, score in scored_episodes[:limit]]
            for episode in results:
                episode.access()

            return results

    async def _prune_episodes(self, target_size: Optional[int] = None) -> None:
        """
        Prune episodes using importance-weighted recency

        Keeps most important and recent episodes
        """
        if target_size is None:
            target_size = int(self.max_episodes * 0.8)  # Prune to 80%

        # Score each episode
        scored = [
            (
                idx,
                episode,
                episode.importance * 0.6 + episode.recency_score() * 0.4,
            )
            for idx, episode in enumerate(self.episodes)
        ]

        # Sort by score and keep top episodes
        scored.sort(key=lambda x: x[2], reverse=True)
        kept_episodes = [episode for _, episode, _ in scored[:target_size]]

        # Rebuild index
        self.episodes = kept_episodes
        self._index = {episode.id: idx for idx, episode in enumerate(self.episodes)}

        logger.info(f"Pruned episodic memory: {len(scored)} -> {len(self.episodes)} episodes")


class MemorySystem:
    """
    Comprehensive memory system integrating all memory types

    Provides:
    - Unified interface to all memory tiers
    - Automatic memory consolidation
    - Memory retrieval optimization
    """

    def __init__(
        self,
        working_capacity: int = 20,
        episodic_capacity: int = 10000,
    ):
        self.working = WorkingMemory(capacity=working_capacity)
        self.episodic = EpisodicMemory(max_episodes=episodic_capacity)

        # Consolidation tracking
        self.last_consolidation = datetime.now()
        self.consolidation_interval = 300  # 5 minutes

    async def remember(
        self,
        content: Any,
        importance: float = 0.5,
        memory_type: MemoryType = MemoryType.WORKING,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict] = None,
    ) -> UUID:
        """
        Store information in appropriate memory tier

        Args:
            content: Content to remember
            importance: Importance score (0-1)
            memory_type: Target memory type
            embedding: Optional semantic embedding
            metadata: Additional metadata

        Returns:
            UUID of stored memory
        """
        if memory_type == MemoryType.WORKING:
            return await self.working.add(content, importance, metadata)
        elif memory_type == MemoryType.EPISODIC:
            return await self.episodic.add_episode(content, importance, embedding, metadata)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

    async def recall(
        self,
        query_embedding: Optional[np.ndarray] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Recall relevant memories across all tiers

        Args:
            query_embedding: Semantic query vector
            memory_types: Filter by memory types
            limit: Maximum results

        Returns:
            List of relevant memories, ranked by relevance
        """
        memories = []

        # Search working memory
        if memory_types is None or MemoryType.WORKING in memory_types:
            working_items = await self.working.get_recent(limit)
            memories.extend(working_items)

        # Search episodic memory
        if memory_types is None or MemoryType.EPISODIC in memory_types:
            episodic_items = await self.episodic.search_episodes(
                query_embedding=query_embedding,
                limit=limit,
            )
            memories.extend(episodic_items)

        # Rank all memories
        if query_embedding is not None:
            scored = [
                (mem, mem.relevance_score(query_embedding=query_embedding)) for mem in memories
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            memories = [mem for mem, score in scored[:limit]]

        return memories

    async def consolidate(self) -> None:
        """
        Consolidate working memory to long-term storage

        Important items from working memory are promoted to episodic memory
        """
        working_items = self.working.get_all()

        # Promote important items
        for item in working_items:
            if item.importance > 0.7:  # Threshold for consolidation
                await self.episodic.add_episode(
                    content=item.content,
                    importance=item.importance,
                    embedding=item.embedding,
                    metadata=item.metadata,
                )

        logger.info(f"Consolidated {len(working_items)} working memory items")
        self.last_consolidation = datetime.now()

    async def auto_consolidate(self) -> None:
        """Automatically consolidate if interval has passed"""
        elapsed = (datetime.now() - self.last_consolidation).total_seconds()
        if elapsed >= self.consolidation_interval:
            await self.consolidate()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            "working_memory_size": len(self.working.items),
            "working_memory_capacity": self.working.capacity,
            "episodic_memory_size": len(self.episodic.episodes),
            "episodic_memory_capacity": self.episodic.max_episodes,
            "total_memories": len(self.working.items) + len(self.episodic.episodes),
            "last_consolidation": self.last_consolidation,
        }
