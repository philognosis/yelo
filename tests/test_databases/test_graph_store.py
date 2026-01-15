"""Test Suite for Graph Store"""

import pytest
import asyncio
from iras.databases.graph_store import GraphStore, GraphNode, GraphEdge, GraphQuery


class TestGraphStore:
    """Test graph database operations"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        gs = GraphStore()
        assert len(gs.nodes) == 0
        assert len(gs.edges) == 0

    @pytest.mark.asyncio
    async def test_add_node(self):
        gs = GraphStore()
        node_id = await gs.add_node("entity", "person", {"name": "Alice"})
        assert node_id in gs.nodes

    @pytest.mark.asyncio
    async def test_add_edge(self):
        gs = GraphStore()
        node1 = await gs.add_node("n1", "type1")
        node2 = await gs.add_node("n2", "type2")
        edge_id = await gs.add_edge(node1, node2, "connected")
        assert edge_id in gs.edges

    @pytest.mark.asyncio
    async def test_get_neighbors(self):
        gs = GraphStore()
        n1 = await gs.add_node("n1", "type")
        n2 = await gs.add_node("n2", "type")
        await gs.add_edge(n1, n2, "rel")
        neighbors = await gs.get_neighbors(n1)
        assert len(neighbors) > 0

    @pytest.mark.asyncio
    async def test_query_nodes(self):
        gs = GraphStore()
        await gs.add_node("n1", "person", {"age": 25})
        await gs.add_node("n2", "person", {"age": 30})
        nodes = await gs.query_nodes(node_type="person")
        assert len(nodes) == 2

    @pytest.mark.asyncio
    async def test_delete_node(self):
        gs = GraphStore()
        node_id = await gs.add_node("test", "type")
        deleted = await gs.delete_node(node_id)
        assert deleted is True
        assert node_id not in gs.nodes
