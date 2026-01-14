"""
Document Store for Flexible Data

Implements:
- JSON document storage
- Flexible schema
- Querying and filtering
- Indexing
- Conversation history
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from loguru import logger


class DocumentStore:
    """
    Document-oriented database

    Simplified implementation for demonstration.
    In production, use MongoDB, CouchDB, or TinyDB.

    Features:
    - Schemaless JSON documents
    - Flexible queries
    - Indexing
    - Collections
    """

    def __init__(self):
        # Collections: collection_name -> document_id -> document
        self.collections: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

        # Indexes: collection_name -> field_name -> field_value -> set of doc_ids
        self.indexes: Dict[str, Dict[str, Dict[Any, Set[str]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(set))
        )

        self._lock = asyncio.Lock()

        logger.info("Document store initialized")

    async def insert(
        self,
        collection: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Insert document into collection

        Args:
            collection: Collection name
            document: Document data
            doc_id: Optional document ID (generated if not provided)

        Returns:
            Document ID
        """
        async with self._lock:
            if doc_id is None:
                doc_id = str(uuid4())

            # Add metadata
            doc_with_meta = {
                "_id": doc_id,
                "_created_at": datetime.now().isoformat(),
                "_updated_at": datetime.now().isoformat(),
                **document,
            }

            self.collections[collection][doc_id] = doc_with_meta

            # Update indexes
            self._update_indexes(collection, doc_id, doc_with_meta)

            logger.debug(f"Inserted document {doc_id} into {collection}")
            return doc_id

    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """Insert multiple documents"""
        doc_ids = []
        for doc in documents:
            doc_id = await self.insert(collection, doc)
            doc_ids.append(doc_id)

        logger.info(f"Inserted {len(doc_ids)} documents into {collection}")
        return doc_ids

    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Find one document matching query

        Args:
            collection: Collection name
            query: Query filter (e.g., {"name": "Alice", "age": 30})

        Returns:
            Matching document or None
        """
        async with self._lock:
            if collection not in self.collections:
                return None

            for doc in self.collections[collection].values():
                if self._match_query(doc, query):
                    return doc.copy()

            return None

    async def find(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        limit: Optional[int] = None,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Find documents matching query

        Args:
            collection: Collection name
            query: Query filter
            sort: Sort specification [(field, direction), ...] where direction is 1 (asc) or -1 (desc)
            limit: Maximum results
            skip: Number of results to skip

        Returns:
            List of matching documents
        """
        async with self._lock:
            if collection not in self.collections:
                return []

            # Get all documents if no query
            if query is None:
                results = list(self.collections[collection].values())
            else:
                # Use index if available
                results = self._query_documents(collection, query)

            # Sort
            if sort:
                for field, direction in reversed(sort):
                    reverse = direction == -1
                    results.sort(
                        key=lambda doc: doc.get(field, ""),
                        reverse=reverse,
                    )

            # Apply skip and limit
            if skip:
                results = results[skip:]
            if limit:
                results = results[:limit]

            return [doc.copy() for doc in results]

    async def find_by_id(
        self,
        collection: str,
        doc_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Find document by ID"""
        async with self._lock:
            if collection not in self.collections:
                return None

            doc = self.collections[collection].get(doc_id)
            return doc.copy() if doc else None

    async def update(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """
        Update documents matching query

        Args:
            collection: Collection name
            query: Query filter
            update: Update operations (e.g., {"$set": {"age": 31}})
            upsert: Insert if no match found

        Returns:
            Number of documents updated
        """
        async with self._lock:
            if collection not in self.collections:
                if upsert:
                    await self.insert(collection, update.get("$set", {}))
                    return 1
                return 0

            updated_count = 0

            for doc_id, doc in self.collections[collection].items():
                if self._match_query(doc, query):
                    # Apply update
                    if "$set" in update:
                        for key, value in update["$set"].items():
                            doc[key] = value

                    if "$inc" in update:
                        for key, value in update["$inc"].items():
                            doc[key] = doc.get(key, 0) + value

                    if "$push" in update:
                        for key, value in update["$push"].items():
                            if key not in doc:
                                doc[key] = []
                            doc[key].append(value)

                    doc["_updated_at"] = datetime.now().isoformat()

                    # Update indexes
                    self._update_indexes(collection, doc_id, doc)

                    updated_count += 1

            if updated_count == 0 and upsert:
                await self.insert(collection, update.get("$set", {}))
                updated_count = 1

            logger.debug(f"Updated {updated_count} documents in {collection}")
            return updated_count

    async def delete(
        self,
        collection: str,
        query: Dict[str, Any],
    ) -> int:
        """
        Delete documents matching query

        Args:
            collection: Collection name
            query: Query filter

        Returns:
            Number of documents deleted
        """
        async with self._lock:
            if collection not in self.collections:
                return 0

            to_delete = []

            for doc_id, doc in self.collections[collection].items():
                if self._match_query(doc, query):
                    to_delete.append(doc_id)

            for doc_id in to_delete:
                # Remove from indexes
                self._remove_from_indexes(collection, doc_id)
                # Remove document
                del self.collections[collection][doc_id]

            logger.debug(f"Deleted {len(to_delete)} documents from {collection}")
            return len(to_delete)

    async def count(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count documents matching query"""
        documents = await self.find(collection, query)
        return len(documents)

    async def create_index(
        self,
        collection: str,
        field: str,
    ) -> None:
        """Create index on field"""
        async with self._lock:
            if collection not in self.collections:
                return

            # Build index for existing documents
            for doc_id, doc in self.collections[collection].items():
                if field in doc:
                    value = doc[field]
                    self.indexes[collection][field][value].add(doc_id)

            logger.info(f"Created index on {collection}.{field}")

    async def drop_collection(self, collection: str) -> None:
        """Drop entire collection"""
        async with self._lock:
            if collection in self.collections:
                del self.collections[collection]
                del self.indexes[collection]
                logger.info(f"Dropped collection: {collection}")

    def _match_query(self, document: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if document matches query

        Supports:
        - Exact match: {"field": value}
        - $gt, $lt, $gte, $lte: {"field": {"$gt": value}}
        - $in: {"field": {"$in": [val1, val2]}}
        - $exists: {"field": {"$exists": True}}
        """
        for key, condition in query.items():
            if key not in document:
                # Field doesn't exist
                if isinstance(condition, dict) and "$exists" in condition:
                    if condition["$exists"]:
                        return False  # Field should exist but doesn't
                else:
                    return False

            doc_value = document.get(key)

            # Handle operators
            if isinstance(condition, dict):
                for operator, value in condition.items():
                    if operator == "$gt" and not (doc_value > value):
                        return False
                    elif operator == "$gte" and not (doc_value >= value):
                        return False
                    elif operator == "$lt" and not (doc_value < value):
                        return False
                    elif operator == "$lte" and not (doc_value <= value):
                        return False
                    elif operator == "$in" and doc_value not in value:
                        return False
                    elif operator == "$ne" and doc_value == value:
                        return False
                    elif operator == "$exists":
                        # Already handled above
                        pass
            else:
                # Exact match
                if doc_value != condition:
                    return False

        return True

    def _query_documents(
        self,
        collection: str,
        query: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Query documents with optional index usage"""
        # Try to use index for first query field
        indexed_field = None
        for field in query.keys():
            if field in self.indexes[collection]:
                indexed_field = field
                break

        if indexed_field:
            # Use index
            query_value = query[indexed_field]
            if not isinstance(query_value, dict):  # Simple equality
                doc_ids = self.indexes[collection][indexed_field].get(query_value, set())
                candidates = [
                    self.collections[collection][doc_id]
                    for doc_id in doc_ids
                    if doc_id in self.collections[collection]
                ]
            else:
                # Operators - fall back to full scan
                candidates = list(self.collections[collection].values())
        else:
            # Full collection scan
            candidates = list(self.collections[collection].values())

        # Filter with full query
        results = [doc for doc in candidates if self._match_query(doc, query)]

        return results

    def _update_indexes(
        self,
        collection: str,
        doc_id: str,
        document: Dict[str, Any],
    ) -> None:
        """Update indexes for document"""
        if collection not in self.indexes:
            return

        for field in self.indexes[collection].keys():
            if field in document:
                value = document[field]
                self.indexes[collection][field][value].add(doc_id)

    def _remove_from_indexes(
        self,
        collection: str,
        doc_id: str,
    ) -> None:
        """Remove document from all indexes"""
        if collection not in self.indexes:
            return

        doc = self.collections[collection].get(doc_id)
        if not doc:
            return

        for field, value_index in self.indexes[collection].items():
            if field in doc:
                value = doc[field]
                if value in value_index:
                    value_index[value].discard(doc_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        stats = {
            "num_collections": len(self.collections),
            "collections": {},
        }

        for collection, docs in self.collections.items():
            stats["collections"][collection] = {
                "num_documents": len(docs),
                "num_indexes": len(self.indexes.get(collection, {})),
                "indexed_fields": list(self.indexes.get(collection, {}).keys()),
            }

        return stats
