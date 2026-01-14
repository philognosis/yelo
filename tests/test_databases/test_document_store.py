"""Test Suite for Document Store"""

import pytest
import asyncio
from iras.databases.document_store import DocumentStore, Document, DocumentQuery


class TestDocumentStore:
    """Test document database operations"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        ds = DocumentStore()
        assert len(ds.documents) == 0

    @pytest.mark.asyncio
    async def test_add_document(self):
        ds = DocumentStore()
        doc_id = await ds.add_document(
            content={"title": "Test", "body": "Content"},
            doc_type="article",
            metadata={"author": "Tester"}
        )
        assert doc_id in ds.documents

    @pytest.mark.asyncio
    async def test_get_document(self):
        ds = DocumentStore()
        doc_id = await ds.add_document({"key": "value"}, "test")
        doc = await ds.get_document(doc_id)
        assert doc is not None
        assert doc.content["key"] == "value"

    @pytest.mark.asyncio
    async def test_update_document(self):
        ds = DocumentStore()
        doc_id = await ds.add_document({"v": 1}, "test")
        updated = await ds.update_document(doc_id, {"v": 2})
        assert updated is True
        doc = await ds.get_document(doc_id)
        assert doc.content["v"] == 2

    @pytest.mark.asyncio
    async def test_query_documents(self):
        ds = DocumentStore()
        await ds.add_document({"category": "A"}, "type1")
        await ds.add_document({"category": "B"}, "type1")
        await ds.add_document({"category": "A"}, "type2")

        results = await ds.query(doc_type="type1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_full_text_search(self):
        ds = DocumentStore()
        await ds.add_document(
            {"text": "The quick brown fox"},
            "article"
        )
        await ds.add_document(
            {"text": "The lazy dog sleeps"},
            "article"
        )

        results = await ds.search("fox")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_delete_document(self):
        ds = DocumentStore()
        doc_id = await ds.add_document({"test": "data"}, "type")
        deleted = await ds.delete_document(doc_id)
        assert deleted is True
        assert doc_id not in ds.documents
