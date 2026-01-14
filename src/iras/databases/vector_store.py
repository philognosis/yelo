"""
Vector Store for Semantic Search

Implements:
- Embedding storage and retrieval
- Similarity search (cosine, euclidean)
- HNSW index for fast approximate nearest neighbor
- Batch operations
- Metadata filtering
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from loguru import logger


@dataclass
class VectorDocument:
    """Document with vector embedding"""

    id: str
    content: Any
    embedding: np.ndarray
    metadata: Dict[str, Any]


class VectorStore:
    """
    Vector database for semantic search

    Uses in-memory FAISS-like implementation for demonstration.
    In production, replace with ChromaDB, Pinecone, or Weaviate.

    Features:
    - Cosine similarity search
    - Euclidean distance search
    - Metadata filtering
    - Batch operations
    """

    def __init__(self, embedding_dim: int = 384):
        """
        Initialize vector store

        Args:
            embedding_dim: Dimension of embeddings (default: 384 for sentence-transformers)
        """
        self.embedding_dim = embedding_dim
        self.documents: Dict[str, VectorDocument] = {}
        self._lock = asyncio.Lock()

        logger.info(f"Vector store initialized with dimension {embedding_dim}")

    async def add(
        self,
        content: Any,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add document with embedding

        Args:
            content: Document content
            embedding: Vector embedding
            metadata: Optional metadata
            doc_id: Optional document ID (generated if not provided)

        Returns:
            Document ID
        """
        if embedding.shape[0] != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension {embedding.shape[0]} != {self.embedding_dim}"
            )

        async with self._lock:
            if doc_id is None:
                doc_id = str(uuid4())

            doc = VectorDocument(
                id=doc_id,
                content=content,
                embedding=embedding / np.linalg.norm(embedding),  # Normalize
                metadata=metadata or {},
            )

            self.documents[doc_id] = doc
            logger.debug(f"Added document {doc_id} to vector store")

            return doc_id

    async def add_batch(
        self,
        contents: List[Any],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Add multiple documents in batch

        Args:
            contents: List of document contents
            embeddings: Array of embeddings (shape: [n_docs, embedding_dim])
            metadatas: Optional list of metadata dicts

        Returns:
            List of document IDs
        """
        if len(contents) != embeddings.shape[0]:
            raise ValueError("Number of contents must match number of embeddings")

        if metadatas is None:
            metadatas = [{}] * len(contents)

        doc_ids = []
        for content, embedding, metadata in zip(contents, embeddings, metadatas):
            doc_id = await self.add(content, embedding, metadata)
            doc_ids.append(doc_id)

        logger.info(f"Added {len(doc_ids)} documents to vector store")
        return doc_ids

    async def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.0,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filters
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of (document, similarity_score) tuples, sorted by similarity
        """
        if query_embedding.shape[0] != self.embedding_dim:
            raise ValueError(
                f"Query embedding dimension {query_embedding.shape[0]} != {self.embedding_dim}"
            )

        async with self._lock:
            # Normalize query
            query_norm = query_embedding / np.linalg.norm(query_embedding)

            # Calculate similarities
            results = []
            for doc in self.documents.values():
                # Apply metadata filter
                if filter_metadata:
                    if not all(
                        doc.metadata.get(k) == v for k, v in filter_metadata.items()
                    ):
                        continue

                # Cosine similarity (dot product of normalized vectors)
                similarity = float(np.dot(query_norm, doc.embedding))

                if similarity >= similarity_threshold:
                    results.append((doc, similarity))

            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)

            return results[:k]

    async def search_by_id(
        self,
        doc_id: str,
        k: int = 10,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Find similar documents to a document in the store

        Args:
            doc_id: Document ID to find similar documents for
            k: Number of results

        Returns:
            List of similar documents
        """
        async with self._lock:
            if doc_id not in self.documents:
                return []

            query_doc = self.documents[doc_id]
            return await self.search(query_doc.embedding, k=k + 1)

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID"""
        async with self._lock:
            return self.documents.get(doc_id)

    async def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        async with self._lock:
            if doc_id in self.documents:
                del self.documents[doc_id]
                logger.debug(f"Deleted document {doc_id}")
                return True
            return False

    async def update_metadata(
        self,
        doc_id: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Update document metadata"""
        async with self._lock:
            if doc_id in self.documents:
                self.documents[doc_id].metadata.update(metadata)
                return True
            return False

    async def count(self) -> int:
        """Get total number of documents"""
        return len(self.documents)

    async def clear(self) -> None:
        """Clear all documents"""
        async with self._lock:
            self.documents.clear()
            logger.info("Vector store cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        if not self.documents:
            return {
                "total_documents": 0,
                "embedding_dim": self.embedding_dim,
            }

        embeddings = np.array([doc.embedding for doc in self.documents.values()])

        return {
            "total_documents": len(self.documents),
            "embedding_dim": self.embedding_dim,
            "mean_norm": float(np.mean(np.linalg.norm(embeddings, axis=1))),
            "std_norm": float(np.std(np.linalg.norm(embeddings, axis=1))),
        }


class HNSWIndex:
    """
    Hierarchical Navigable Small World (HNSW) index

    Provides fast approximate nearest neighbor search.
    Simplified implementation for demonstration.

    In production, use FAISS or hnswlib.
    """

    def __init__(
        self,
        dim: int,
        max_elements: int = 10000,
        M: int = 16,
        ef_construction: int = 200,
    ):
        """
        Initialize HNSW index

        Args:
            dim: Embedding dimension
            max_elements: Maximum number of elements
            M: Number of connections per element
            ef_construction: Size of dynamic candidate list
        """
        self.dim = dim
        self.max_elements = max_elements
        self.M = M  # Number of bi-directional links
        self.ef_construction = ef_construction

        # Simplified storage
        self.elements: Dict[int, np.ndarray] = {}
        self.id_mapping: Dict[str, int] = {}
        self.reverse_mapping: Dict[int, str] = {}
        self.next_id = 0

        logger.info(
            f"HNSW index initialized: dim={dim}, M={M}, ef={ef_construction}"
        )

    def add_items(
        self,
        embeddings: np.ndarray,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add items to index"""
        n_items = embeddings.shape[0]

        if ids is None:
            ids = [str(uuid4()) for _ in range(n_items)]

        for i, (embedding, doc_id) in enumerate(zip(embeddings, ids)):
            internal_id = self.next_id
            self.elements[internal_id] = embedding
            self.id_mapping[doc_id] = internal_id
            self.reverse_mapping[internal_id] = doc_id
            self.next_id += 1

        logger.info(f"Added {n_items} items to HNSW index")

    def knn_query(
        self,
        query: np.ndarray,
        k: int = 10,
    ) -> Tuple[List[str], List[float]]:
        """
        K-nearest neighbor query

        Returns:
            Tuple of (ids, distances)
        """
        if not self.elements:
            return [], []

        # Simple brute force for demonstration
        # In production, use HNSW graph traversal
        distances = []
        for internal_id, embedding in self.elements.items():
            dist = float(np.linalg.norm(query - embedding))
            distances.append((internal_id, dist))

        # Sort by distance
        distances.sort(key=lambda x: x[1])
        distances = distances[:k]

        # Convert to external IDs
        ids = [self.reverse_mapping[int_id] for int_id, _ in distances]
        dists = [dist for _, dist in distances]

        return ids, dists

    def get_items(self, ids: List[str]) -> np.ndarray:
        """Get embeddings by IDs"""
        internal_ids = [self.id_mapping[id] for id in ids if id in self.id_mapping]
        embeddings = [self.elements[int_id] for int_id in internal_ids]
        return np.array(embeddings) if embeddings else np.array([])
