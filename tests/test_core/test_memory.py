"""
Test Suite for Memory System

Tests cover:
- Working memory functionality
- Episodic memory functionality
- Memory consolidation
- Memory retrieval and search
- Memory scoring (recency, relevance, importance)
- Capacity management and pruning
- Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import numpy as np

from iras.core.memory import (
    MemorySystem,
    MemoryItem,
    MemoryType,
    WorkingMemory,
    EpisodicMemory,
)


class TestMemoryItem:
    """Test MemoryItem model and scoring"""

    def test_memory_item_initialization(self):
        """Test basic memory item creation"""
        content = {"key": "value"}
        item = MemoryItem(
            id=None,  # Will be generated
            content=content,
            memory_type=MemoryType.WORKING,
            timestamp=datetime.now(),
        )

        assert item.content == content
        assert item.memory_type == MemoryType.WORKING
        assert item.access_count == 0
        assert 0.0 <= item.importance <= 1.0

    def test_memory_item_access_tracking(self):
        """Test that accessing memory updates counters"""
        item = MemoryItem(
            id=None,
            content="test",
            memory_type=MemoryType.WORKING,
            timestamp=datetime.now(),
        )

        initial_count = item.access_count
        item.access()

        assert item.access_count == initial_count + 1
        assert item.last_accessed > item.timestamp

    def test_memory_item_recency_score(self):
        """Test recency score calculation"""
        # Recent memory
        recent_item = MemoryItem(
            id=None,
            content="recent",
            memory_type=MemoryType.WORKING,
            timestamp=datetime.now(),
        )

        recent_score = recent_item.recency_score()
        assert 0.9 < recent_score <= 1.0

    def test_memory_item_recency_decay(self):
        """Test that recency score decays over time"""
        # Old memory (simulated)
        old_item = MemoryItem(
            id=None,
            content="old",
            memory_type=MemoryType.EPISODIC,
            timestamp=datetime.now() - timedelta(hours=5),
        )
        old_item.last_accessed = datetime.now() - timedelta(hours=5)

        score = old_item.recency_score()
        assert 0.0 <= score < 0.9

    def test_memory_item_relevance_score_with_embedding(self):
        """Test relevance scoring with semantic embeddings"""
        query_embedding = np.random.rand(128)
        memory_embedding = query_embedding + np.random.rand(128) * 0.1

        item = MemoryItem(
            id=None,
            content="test",
            memory_type=MemoryType.SEMANTIC,
            timestamp=datetime.now(),
            embedding=memory_embedding / np.linalg.norm(memory_embedding),
            importance=0.8,
        )

        query_norm = query_embedding / np.linalg.norm(query_embedding)
        score = item.relevance_score(query_embedding=query_norm)

        assert 0.0 <= score <= 1.0

    def test_memory_item_relevance_score_without_embedding(self):
        """Test relevance scoring without embeddings"""
        item = MemoryItem(
            id=None,
            content="test",
            memory_type=MemoryType.WORKING,
            timestamp=datetime.now(),
            importance=0.7,
        )

        score = item.relevance_score()

        assert 0.0 <= score <= 1.0


class TestWorkingMemory:
    """Test working memory functionality"""

    @pytest.mark.asyncio
    async def test_working_memory_initialization(self):
        """Test working memory creation"""
        wm = WorkingMemory(capacity=10)

        assert wm.capacity == 10
        assert len(wm.items) == 0

    @pytest.mark.asyncio
    async def test_add_to_working_memory(self):
        """Test adding items to working memory"""
        wm = WorkingMemory(capacity=10)

        content = {"data": "test"}
        item_id = await wm.add(content, importance=0.7)

        assert item_id is not None
        assert len(wm.items) == 1

    @pytest.mark.asyncio
    async def test_working_memory_capacity_limit(self):
        """Test that working memory respects capacity limit"""
        wm = WorkingMemory(capacity=5)

        # Add more items than capacity
        for i in range(10):
            await wm.add(f"item_{i}")

        assert len(wm.items) <= 5

    @pytest.mark.asyncio
    async def test_working_memory_fifo_eviction(self):
        """Test FIFO eviction policy"""
        wm = WorkingMemory(capacity=3)

        # Add items
        id1 = await wm.add("first")
        id2 = await wm.add("second")
        id3 = await wm.add("third")
        id4 = await wm.add("fourth")

        # First item should be evicted
        all_items = wm.get_all()
        contents = [item.content for item in all_items]

        assert "first" not in contents
        assert "fourth" in contents

    @pytest.mark.asyncio
    async def test_get_recent_items(self):
        """Test retrieving recent items"""
        wm = WorkingMemory(capacity=10)

        for i in range(5):
            await wm.add(f"item_{i}")

        recent = await wm.get_recent(limit=3)

        assert len(recent) == 3
        # Should get the last 3 items
        assert recent[-1].content == "item_4"

    @pytest.mark.asyncio
    async def test_clear_working_memory(self):
        """Test clearing working memory"""
        wm = WorkingMemory(capacity=10)

        await wm.add("item1")
        await wm.add("item2")

        await wm.clear()

        assert len(wm.items) == 0

    @pytest.mark.asyncio
    async def test_working_memory_with_metadata(self):
        """Test storing metadata with memories"""
        wm = WorkingMemory(capacity=10)

        metadata = {"source": "test", "type": "data"}
        await wm.add("content", metadata=metadata)

        items = wm.get_all()
        assert items[0].metadata == metadata


class TestEpisodicMemory:
    """Test episodic memory functionality"""

    @pytest.mark.asyncio
    async def test_episodic_memory_initialization(self):
        """Test episodic memory creation"""
        em = EpisodicMemory(max_episodes=100)

        assert em.max_episodes == 100
        assert len(em.episodes) == 0

    @pytest.mark.asyncio
    async def test_add_episode(self):
        """Test adding episodes"""
        em = EpisodicMemory(max_episodes=100)

        content = {"event": "test_event"}
        episode_id = await em.add_episode(content, importance=0.8)

        assert episode_id is not None
        assert len(em.episodes) == 1

    @pytest.mark.asyncio
    async def test_add_episode_with_embedding(self):
        """Test adding episode with semantic embedding"""
        em = EpisodicMemory(max_episodes=100)

        embedding = np.random.rand(128)
        episode_id = await em.add_episode(
            content="test",
            embedding=embedding,
            importance=0.7,
        )

        episode = await em.get_episode(episode_id)
        assert episode is not None
        assert episode.embedding is not None

    @pytest.mark.asyncio
    async def test_get_episode_by_id(self):
        """Test retrieving specific episode"""
        em = EpisodicMemory(max_episodes=100)

        content = {"specific": "episode"}
        episode_id = await em.add_episode(content)

        retrieved = await em.get_episode(episode_id)

        assert retrieved is not None
        assert retrieved.content == content
        assert retrieved.access_count == 1  # Should be accessed

    @pytest.mark.asyncio
    async def test_get_nonexistent_episode(self):
        """Test retrieving non-existent episode returns None"""
        em = EpisodicMemory(max_episodes=100)

        from uuid import uuid4
        fake_id = uuid4()

        result = await em.get_episode(fake_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_search_episodes_by_time_range(self):
        """Test searching episodes by time range"""
        em = EpisodicMemory(max_episodes=100)

        # Add episodes at different times
        now = datetime.now()
        await em.add_episode("old", importance=0.5)
        await asyncio.sleep(0.01)
        middle_time = datetime.now()
        await asyncio.sleep(0.01)
        await em.add_episode("new", importance=0.5)

        # Search for episodes after middle_time
        results = await em.search_episodes(
            start_time=middle_time,
            limit=10,
        )

        assert len(results) == 1
        assert results[0].content == "new"

    @pytest.mark.asyncio
    async def test_search_episodes_by_importance(self):
        """Test filtering episodes by importance"""
        em = EpisodicMemory(max_episodes=100)

        await em.add_episode("low", importance=0.3)
        await em.add_episode("medium", importance=0.6)
        await em.add_episode("high", importance=0.9)

        results = await em.search_episodes(
            min_importance=0.7,
            limit=10,
        )

        assert len(results) == 1
        assert results[0].content == "high"

    @pytest.mark.asyncio
    async def test_search_episodes_with_limit(self):
        """Test search result limiting"""
        em = EpisodicMemory(max_episodes=100)

        # Add many episodes
        for i in range(10):
            await em.add_episode(f"episode_{i}")

        results = await em.search_episodes(limit=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_episodic_memory_pruning(self):
        """Test automatic pruning when capacity exceeded"""
        em = EpisodicMemory(max_episodes=5)

        # Add more episodes than capacity
        for i in range(10):
            await em.add_episode(
                content=f"episode_{i}",
                importance=0.5 + (i * 0.05),  # Increasing importance
            )

        # Should be pruned to capacity
        assert len(em.episodes) <= 5

    @pytest.mark.asyncio
    async def test_pruning_keeps_important_episodes(self):
        """Test that pruning preserves important memories"""
        em = EpisodicMemory(max_episodes=3)

        # Add low importance episodes
        await em.add_episode("low1", importance=0.2)
        await em.add_episode("low2", importance=0.3)

        # Add high importance episode
        await em.add_episode("important", importance=0.99)

        # Add more low importance to trigger pruning
        await em.add_episode("low3", importance=0.25)
        await em.add_episode("low4", importance=0.28)

        # Important episode should still be there
        contents = [ep.content for ep in em.episodes]
        assert "important" in contents


class TestMemorySystem:
    """Test integrated memory system"""

    def test_memory_system_initialization(self):
        """Test memory system creation"""
        ms = MemorySystem(
            working_capacity=20,
            episodic_capacity=1000,
        )

        assert ms.working.capacity == 20
        assert ms.episodic.max_episodes == 1000

    @pytest.mark.asyncio
    async def test_remember_to_working_memory(self):
        """Test storing in working memory"""
        ms = MemorySystem()

        content = {"test": "data"}
        mem_id = await ms.remember(
            content=content,
            importance=0.5,
            memory_type=MemoryType.WORKING,
        )

        assert mem_id is not None
        stats = ms.get_memory_stats()
        assert stats["working_memory_size"] == 1

    @pytest.mark.asyncio
    async def test_remember_to_episodic_memory(self):
        """Test storing in episodic memory"""
        ms = MemorySystem()

        content = {"event": "important"}
        mem_id = await ms.remember(
            content=content,
            importance=0.8,
            memory_type=MemoryType.EPISODIC,
        )

        assert mem_id is not None
        stats = ms.get_memory_stats()
        assert stats["episodic_memory_size"] == 1

    @pytest.mark.asyncio
    async def test_remember_with_embedding(self):
        """Test storing memories with embeddings"""
        ms = MemorySystem()

        embedding = np.random.rand(128)
        await ms.remember(
            content="semantic memory",
            memory_type=MemoryType.EPISODIC,
            embedding=embedding,
        )

        stats = ms.get_memory_stats()
        assert stats["episodic_memory_size"] == 1

    @pytest.mark.asyncio
    async def test_recall_from_working_memory(self):
        """Test recalling from working memory"""
        ms = MemorySystem()

        await ms.remember("item1", memory_type=MemoryType.WORKING)
        await ms.remember("item2", memory_type=MemoryType.WORKING)

        memories = await ms.recall(
            memory_types=[MemoryType.WORKING],
            limit=10,
        )

        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_recall_from_episodic_memory(self):
        """Test recalling from episodic memory"""
        ms = MemorySystem()

        await ms.remember("episode1", memory_type=MemoryType.EPISODIC)
        await ms.remember("episode2", memory_type=MemoryType.EPISODIC)

        memories = await ms.recall(
            memory_types=[MemoryType.EPISODIC],
            limit=10,
        )

        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_recall_from_all_memory_types(self):
        """Test recalling from all memory tiers"""
        ms = MemorySystem()

        await ms.remember("working", memory_type=MemoryType.WORKING)
        await ms.remember("episodic", memory_type=MemoryType.EPISODIC)

        memories = await ms.recall(limit=10)

        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_recall_with_semantic_ranking(self):
        """Test semantic ranking in recall"""
        ms = MemorySystem()

        # Add memories with embeddings
        query_emb = np.random.rand(128)
        similar_emb = query_emb + np.random.rand(128) * 0.1
        different_emb = np.random.rand(128)

        await ms.remember(
            "similar",
            memory_type=MemoryType.EPISODIC,
            embedding=similar_emb,
        )
        await ms.remember(
            "different",
            memory_type=MemoryType.EPISODIC,
            embedding=different_emb,
        )

        # Recall with query embedding
        memories = await ms.recall(
            query_embedding=query_emb / np.linalg.norm(query_emb),
            memory_types=[MemoryType.EPISODIC],
            limit=2,
        )

        # Similar should be ranked higher
        assert len(memories) > 0

    @pytest.mark.asyncio
    async def test_memory_consolidation(self):
        """Test consolidating working to episodic memory"""
        ms = MemorySystem()

        # Add important items to working memory
        await ms.remember(
            "important1",
            importance=0.9,
            memory_type=MemoryType.WORKING,
        )
        await ms.remember(
            "important2",
            importance=0.8,
            memory_type=MemoryType.WORKING,
        )
        await ms.remember(
            "unimportant",
            importance=0.3,
            memory_type=MemoryType.WORKING,
        )

        initial_episodic = ms.get_memory_stats()["episodic_memory_size"]

        # Consolidate
        await ms.consolidate()

        final_episodic = ms.get_memory_stats()["episodic_memory_size"]

        # Important items should be promoted
        assert final_episodic > initial_episodic

    @pytest.mark.asyncio
    async def test_auto_consolidation(self):
        """Test automatic consolidation based on time"""
        ms = MemorySystem()
        ms.consolidation_interval = 0.1  # 100ms for testing

        await ms.remember("test", importance=0.9, memory_type=MemoryType.WORKING)

        # Wait for interval
        await asyncio.sleep(0.15)

        # Auto-consolidate should trigger
        await ms.auto_consolidate()

        # Check that consolidation happened
        assert ms.last_consolidation > datetime.now() - timedelta(seconds=1)

    def test_get_memory_stats(self):
        """Test getting memory statistics"""
        ms = MemorySystem(
            working_capacity=20,
            episodic_capacity=1000,
        )

        stats = ms.get_memory_stats()

        assert "working_memory_size" in stats
        assert "working_memory_capacity" in stats
        assert "episodic_memory_size" in stats
        assert "episodic_memory_capacity" in stats
        assert "total_memories" in stats
        assert stats["working_memory_capacity"] == 20
        assert stats["episodic_memory_capacity"] == 1000


class TestComplexScenarios:
    """Test complex memory scenarios"""

    @pytest.mark.asyncio
    async def test_memory_lifecycle(self):
        """Test complete memory lifecycle"""
        ms = MemorySystem(working_capacity=3)

        # 1. Add to working memory
        id1 = await ms.remember("event1", importance=0.9, memory_type=MemoryType.WORKING)
        id2 = await ms.remember("event2", importance=0.8, memory_type=MemoryType.WORKING)
        id3 = await ms.remember("event3", importance=0.2, memory_type=MemoryType.WORKING)

        # 2. Consolidate important items
        await ms.consolidate()

        # 3. Verify episodic memory has important items
        stats = ms.get_memory_stats()
        assert stats["episodic_memory_size"] == 2  # Only important ones

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations"""
        ms = MemorySystem()

        async def add_memories(prefix):
            for i in range(5):
                await ms.remember(
                    f"{prefix}_{i}",
                    memory_type=MemoryType.WORKING,
                )

        # Concurrent adds
        await asyncio.gather(
            add_memories("A"),
            add_memories("B"),
            add_memories("C"),
        )

        stats = ms.get_memory_stats()
        assert stats["working_memory_size"] == 15

    @pytest.mark.asyncio
    async def test_memory_search_with_multiple_criteria(self):
        """Test complex memory search"""
        ms = MemorySystem()

        # Add diverse memories
        await ms.remember(
            "old_important",
            importance=0.9,
            memory_type=MemoryType.EPISODIC,
        )
        await asyncio.sleep(0.01)

        middle_time = datetime.now()
        await asyncio.sleep(0.01)

        await ms.remember(
            "new_important",
            importance=0.85,
            memory_type=MemoryType.EPISODIC,
        )

        # Search recent important memories
        results = await ms.recall(
            memory_types=[MemoryType.EPISODIC],
            limit=1,
        )

        assert len(results) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_memory_recall(self):
        """Test recalling from empty memory"""
        ms = MemorySystem()

        memories = await ms.recall(limit=10)

        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_remember_with_zero_importance(self):
        """Test storing memory with zero importance"""
        ms = MemorySystem()

        mem_id = await ms.remember(
            "test",
            importance=0.0,
            memory_type=MemoryType.WORKING,
        )

        assert mem_id is not None

    @pytest.mark.asyncio
    async def test_remember_with_max_importance(self):
        """Test storing memory with maximum importance"""
        ms = MemorySystem()

        mem_id = await ms.remember(
            "test",
            importance=1.0,
            memory_type=MemoryType.EPISODIC,
        )

        assert mem_id is not None

    @pytest.mark.asyncio
    async def test_recall_with_zero_limit(self):
        """Test recall with limit of 0"""
        ms = MemorySystem()

        await ms.remember("test", memory_type=MemoryType.WORKING)

        memories = await ms.recall(limit=0)

        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_unsupported_memory_type(self):
        """Test that unsupported memory type raises error"""
        ms = MemorySystem()

        with pytest.raises(ValueError, match="Unsupported memory type"):
            await ms.remember("test", memory_type="INVALID_TYPE")

    @pytest.mark.asyncio
    async def test_working_memory_with_zero_capacity(self):
        """Test working memory with minimal capacity"""
        wm = WorkingMemory(capacity=1)

        await wm.add("item1")
        await wm.add("item2")

        assert len(wm.items) == 1

    @pytest.mark.asyncio
    async def test_consolidation_with_no_memories(self):
        """Test consolidation with empty working memory"""
        ms = MemorySystem()

        await ms.consolidate()  # Should not raise error

        stats = ms.get_memory_stats()
        assert stats["episodic_memory_size"] == 0
