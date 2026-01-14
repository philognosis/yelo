"""
Test Suite for Vector Store

Tests cover:
- Vector document storage and retrieval
- Similarity search (cosine)
- Metadata filtering
- Batch operations
- HNSW index functionality
- Edge cases and error handling
"""

import pytest
import asyncio
import numpy as np
from uuid import uuid4

from iras.databases.vector_store import VectorStore, VectorDocument, HNSWIndex


class TestVectorStoreBasics:
    """Test basic vector store operations"""

    @pytest.mark.asyncio
    async def test_vector_store_initialization(self):
        """Test creating vector store"""
        vs = VectorStore(embedding_dim=128)

        assert vs.embedding_dim == 128
        assert len(vs.documents) == 0

    @pytest.mark.asyncio
    async def test_add_document(self):
        """Test adding a single document"""
        vs = VectorStore(embedding_dim=128)

        content = "Test document"
        embedding = np.random.rand(128)

        doc_id = await vs.add(content, embedding)

        assert doc_id is not None
        assert await vs.count() == 1

    @pytest.mark.asyncio
    async def test_add_document_with_metadata(self):
        """Test adding document with metadata"""
        vs = VectorStore(embedding_dim=128)

        metadata = {"category": "test", "author": "tester"}
        embedding = np.random.rand(128)

        doc_id = await vs.add("content", embedding, metadata=metadata)

        doc = await vs.get(doc_id)
        assert doc.metadata == metadata

    @pytest.mark.asyncio
    async def test_add_document_wrong_dimension(self):
        """Test that wrong embedding dimension raises error"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(64)  # Wrong dimension

        with pytest.raises(ValueError, match="Embedding dimension"):
            await vs.add("content", embedding)

    @pytest.mark.asyncio
    async def test_add_document_custom_id(self):
        """Test adding document with custom ID"""
        vs = VectorStore(embedding_dim=128)

        custom_id = "custom_doc_123"
        embedding = np.random.rand(128)

        doc_id = await vs.add("content", embedding, doc_id=custom_id)

        assert doc_id == custom_id


class TestBatchOperations:
    """Test batch document operations"""

    @pytest.mark.asyncio
    async def test_add_batch_documents(self):
        """Test adding multiple documents at once"""
        vs = VectorStore(embedding_dim=128)

        contents = ["doc1", "doc2", "doc3"]
        embeddings = np.random.rand(3, 128)

        doc_ids = await vs.add_batch(contents, embeddings)

        assert len(doc_ids) == 3
        assert await vs.count() == 3

    @pytest.mark.asyncio
    async def test_add_batch_with_metadata(self):
        """Test batch add with metadata"""
        vs = VectorStore(embedding_dim=128)

        contents = ["doc1", "doc2"]
        embeddings = np.random.rand(2, 128)
        metadatas = [{"type": "A"}, {"type": "B"}]

        doc_ids = await vs.add_batch(contents, embeddings, metadatas=metadatas)

        doc = await vs.get(doc_ids[0])
        assert doc.metadata["type"] == "A"

    @pytest.mark.asyncio
    async def test_add_batch_size_mismatch(self):
        """Test batch add with mismatched sizes"""
        vs = VectorStore(embedding_dim=128)

        contents = ["doc1", "doc2"]
        embeddings = np.random.rand(3, 128)  # Mismatch

        with pytest.raises(ValueError, match="must match"):
            await vs.add_batch(contents, embeddings)


class TestSimilaritySearch:
    """Test similarity search functionality"""

    @pytest.mark.asyncio
    async def test_simple_similarity_search(self):
        """Test basic similarity search"""
        vs = VectorStore(embedding_dim=128)

        # Add documents
        query_emb = np.random.rand(128)
        similar_emb = query_emb + np.random.rand(128) * 0.1
        different_emb = np.random.rand(128)

        await vs.add("similar", similar_emb)
        await vs.add("different", different_emb)

        # Search
        results = await vs.search(query_emb, k=2)

        assert len(results) == 2
        # Similar should have higher similarity
        assert results[0][1] > results[1][1]

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """Test search result limiting"""
        vs = VectorStore(embedding_dim=128)

        # Add 10 documents
        for i in range(10):
            await vs.add(f"doc{i}", np.random.rand(128))

        # Search with k=5
        results = await vs.search(np.random.rand(128), k=5)

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self):
        """Test filtering search by metadata"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128)

        await vs.add("catA1", embedding, metadata={"category": "A"})
        await vs.add("catA2", embedding, metadata={"category": "A"})
        await vs.add("catB", embedding, metadata={"category": "B"})

        # Search only category A
        results = await vs.search(
            embedding,
            k=10,
            filter_metadata={"category": "A"},
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_similarity_threshold(self):
        """Test filtering by similarity threshold"""
        vs = VectorStore(embedding_dim=128)

        query_emb = np.random.rand(128)
        query_norm = query_emb / np.linalg.norm(query_emb)

        # Add very similar document
        similar = query_norm * 1.01
        await vs.add("similar", similar)

        # Add dissimilar document
        dissimilar = np.random.rand(128)
        await vs.add("dissimilar", dissimilar)

        # Search with high threshold
        results = await vs.search(query_emb, k=10, similarity_threshold=0.9)

        # Should only get very similar ones
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_by_id(self):
        """Test finding similar documents by ID"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128)
        doc_id = await vs.add("query_doc", embedding)

        # Add similar documents
        await vs.add("similar", embedding + np.random.rand(128) * 0.1)

        # Search by ID
        results = await vs.search_by_id(doc_id, k=2)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_wrong_dimension(self):
        """Test search with wrong embedding dimension"""
        vs = VectorStore(embedding_dim=128)

        wrong_emb = np.random.rand(64)

        with pytest.raises(ValueError, match="Query embedding dimension"):
            await vs.search(wrong_emb)


class TestDocumentOperations:
    """Test document CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_document(self):
        """Test retrieving document by ID"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128)
        doc_id = await vs.add("content", embedding)

        doc = await vs.get(doc_id)

        assert doc is not None
        assert doc.content == "content"

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self):
        """Test getting non-existent document"""
        vs = VectorStore(embedding_dim=128)

        doc = await vs.get("nonexistent_id")

        assert doc is None

    @pytest.mark.asyncio
    async def test_delete_document(self):
        """Test deleting document"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128)
        doc_id = await vs.add("content", embedding)

        deleted = await vs.delete(doc_id)

        assert deleted is True
        assert await vs.get(doc_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self):
        """Test deleting non-existent document"""
        vs = VectorStore(embedding_dim=128)

        deleted = await vs.delete("nonexistent")

        assert deleted is False

    @pytest.mark.asyncio
    async def test_update_metadata(self):
        """Test updating document metadata"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128)
        doc_id = await vs.add("content", embedding, metadata={"old": "value"})

        updated = await vs.update_metadata(doc_id, {"new": "value"})

        assert updated is True
        doc = await vs.get(doc_id)
        assert "new" in doc.metadata

    @pytest.mark.asyncio
    async def test_count_documents(self):
        """Test counting documents"""
        vs = VectorStore(embedding_dim=128)

        for i in range(5):
            await vs.add(f"doc{i}", np.random.rand(128))

        count = await vs.count()

        assert count == 5

    @pytest.mark.asyncio
    async def test_clear_store(self):
        """Test clearing all documents"""
        vs = VectorStore(embedding_dim=128)

        for i in range(5):
            await vs.add(f"doc{i}", np.random.rand(128))

        await vs.clear()

        assert await vs.count() == 0


class TestStatistics:
    """Test store statistics"""

    def test_statistics_empty_store(self):
        """Test statistics on empty store"""
        vs = VectorStore(embedding_dim=128)

        stats = vs.get_statistics()

        assert stats["total_documents"] == 0
        assert stats["embedding_dim"] == 128

    @pytest.mark.asyncio
    async def test_statistics_with_documents(self):
        """Test statistics with documents"""
        vs = VectorStore(embedding_dim=128)

        for i in range(10):
            await vs.add(f"doc{i}", np.random.rand(128))

        stats = vs.get_statistics()

        assert stats["total_documents"] == 10
        assert "mean_norm" in stats
        assert "std_norm" in stats


class TestHNSWIndex:
    """Test HNSW index functionality"""

    def test_hnsw_initialization(self):
        """Test HNSW index creation"""
        index = HNSWIndex(dim=128, max_elements=1000)

        assert index.dim == 128
        assert index.max_elements == 1000

    def test_add_items_to_index(self):
        """Test adding items to HNSW index"""
        index = HNSWIndex(dim=128)

        embeddings = np.random.rand(5, 128)
        ids = [f"doc_{i}" for i in range(5)]

        index.add_items(embeddings, ids)

        assert len(index.elements) == 5

    def test_knn_query(self):
        """Test k-nearest neighbor query"""
        index = HNSWIndex(dim=128)

        embeddings = np.random.rand(10, 128)
        index.add_items(embeddings)

        query = np.random.rand(128)
        ids, distances = index.knn_query(query, k=5)

        assert len(ids) == 5
        assert len(distances) == 5

    def test_get_items(self):
        """Test retrieving items by IDs"""
        index = HNSWIndex(dim=128)

        embeddings = np.random.rand(3, 128)
        ids = ["doc_0", "doc_1", "doc_2"]

        index.add_items(embeddings, ids)

        retrieved = index.get_items(["doc_0", "doc_1"])

        assert retrieved.shape[0] == 2


class TestConcurrency:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_adds(self):
        """Test adding documents concurrently"""
        vs = VectorStore(embedding_dim=128)

        async def add_doc(i):
            await vs.add(f"doc{i}", np.random.rand(128))

        await asyncio.gather(*[add_doc(i) for i in range(10)])

        assert await vs.count() == 10

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test concurrent searches"""
        vs = VectorStore(embedding_dim=128)

        # Add documents
        for i in range(10):
            await vs.add(f"doc{i}", np.random.rand(128))

        # Concurrent searches
        queries = [np.random.rand(128) for _ in range(5)]
        results = await asyncio.gather(
            *[vs.search(q, k=3) for q in queries]
        )

        assert len(results) == 5


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_store_search(self):
        """Test searching empty store"""
        vs = VectorStore(embedding_dim=128)

        results = await vs.search(np.random.rand(128), k=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_by_nonexistent_id(self):
        """Test search by non-existent ID"""
        vs = VectorStore(embedding_dim=128)

        results = await vs.search_by_id("nonexistent", k=5)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_normalized_embeddings(self):
        """Test that embeddings are normalized"""
        vs = VectorStore(embedding_dim=128)

        embedding = np.random.rand(128) * 10  # Large values
        doc_id = await vs.add("test", embedding)

        doc = await vs.get(doc_id)
        norm = np.linalg.norm(doc.embedding)

        assert abs(norm - 1.0) < 0.01  # Should be normalized

    @pytest.mark.asyncio
    async def test_search_k_larger_than_store(self):
        """Test search with k larger than number of documents"""
        vs = VectorStore(embedding_dim=128)

        await vs.add("doc1", np.random.rand(128))
        await vs.add("doc2", np.random.rand(128))

        results = await vs.search(np.random.rand(128), k=100)

        assert len(results) == 2  # Only what's available
