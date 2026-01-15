"""
Graph Database for Relationships

Implements:
- Knowledge graph storage
- Relationship queries
- Graph algorithms (centrality, clustering, pathfinding)
- Agent network topology
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import networkx as nx
import numpy as np
from loguru import logger


@dataclass
class Node:
    """Graph node"""

    id: str
    node_type: str
    properties: Dict[str, Any]


@dataclass
class Edge:
    """Graph edge"""

    source: str
    target: str
    edge_type: str
    properties: Dict[str, Any]
    weight: float = 1.0


class GraphStore:
    """
    Graph database for multi-agent systems

    Uses NetworkX for in-memory graph operations.
    In production, replace with Neo4j, ArangoDB, or DGraph.

    Features:
    - Entity and relationship storage
    - Graph traversal
    - Centrality analysis
    - Community detection
    - Shortest path finding
    """

    def __init__(self, directed: bool = True):
        """
        Initialize graph store

        Args:
            directed: Use directed graph (default: True)
        """
        self.graph = nx.DiGraph() if directed else nx.Graph()
        self.directed = directed
        self._lock = asyncio.Lock()

        logger.info(f"Graph store initialized ({'directed' if directed else 'undirected'})")

    async def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add node to graph

        Args:
            node_id: Unique node identifier
            node_type: Type of node (e.g., 'agent', 'task', 'concept')
            properties: Node properties
        """
        async with self._lock:
            self.graph.add_node(
                node_id,
                node_type=node_type,
                properties=properties or {},
            )
            logger.debug(f"Added node: {node_id} (type: {node_type})")

    async def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
    ) -> None:
        """
        Add edge to graph

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Type of relationship
            properties: Edge properties
            weight: Edge weight
        """
        async with self._lock:
            self.graph.add_edge(
                source,
                target,
                edge_type=edge_type,
                properties=properties or {},
                weight=weight,
            )
            logger.debug(f"Added edge: {source} --[{edge_type}]--> {target}")

    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        async with self._lock:
            if node_id not in self.graph:
                return None

            data = self.graph.nodes[node_id]
            return Node(
                id=node_id,
                node_type=data.get("node_type", "unknown"),
                properties=data.get("properties", {}),
            )

    async def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[str] = None,
        direction: str = "out",
    ) -> List[str]:
        """
        Get neighboring nodes

        Args:
            node_id: Node to get neighbors for
            edge_type: Filter by edge type
            direction: 'in', 'out', or 'both'

        Returns:
            List of neighbor node IDs
        """
        async with self._lock:
            if node_id not in self.graph:
                return []

            if direction == "out":
                neighbors = list(self.graph.successors(node_id))
            elif direction == "in":
                neighbors = list(self.graph.predecessors(node_id))
            else:  # both
                neighbors = list(set(self.graph.successors(node_id)) | set(self.graph.predecessors(node_id)))

            # Filter by edge type if specified
            if edge_type:
                filtered = []
                for neighbor in neighbors:
                    if direction in ["out", "both"]:
                        if self.graph.has_edge(node_id, neighbor):
                            if self.graph[node_id][neighbor].get("edge_type") == edge_type:
                                filtered.append(neighbor)
                    if direction in ["in", "both"]:
                        if self.graph.has_edge(neighbor, node_id):
                            if self.graph[neighbor][node_id].get("edge_type") == edge_type:
                                if neighbor not in filtered:
                                    filtered.append(neighbor)
                neighbors = filtered

            return neighbors

    async def find_path(
        self,
        source: str,
        target: str,
        max_length: Optional[int] = None,
    ) -> Optional[List[str]]:
        """
        Find shortest path between nodes

        Args:
            source: Source node
            target: Target node
            max_length: Maximum path length

        Returns:
            Path as list of node IDs, or None if no path exists
        """
        async with self._lock:
            try:
                if max_length:
                    # Use cutoff for max length
                    path = nx.shortest_path(
                        self.graph,
                        source,
                        target,
                        weight="weight",
                    )
                    if len(path) - 1 > max_length:  # -1 because path includes endpoints
                        return None
                    return path
                else:
                    return nx.shortest_path(self.graph, source, target, weight="weight")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return None

    async def get_centrality(
        self,
        algorithm: str = "pagerank",
        node_type: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Calculate node centrality

        Args:
            algorithm: 'pagerank', 'betweenness', 'closeness', 'degree'
            node_type: Filter by node type

        Returns:
            Dict mapping node IDs to centrality scores
        """
        async with self._lock:
            # Filter nodes by type if specified
            if node_type:
                subgraph_nodes = [
                    n for n, d in self.graph.nodes(data=True)
                    if d.get("node_type") == node_type
                ]
                subgraph = self.graph.subgraph(subgraph_nodes)
            else:
                subgraph = self.graph

            if len(subgraph) == 0:
                return {}

            # Calculate centrality
            if algorithm == "pagerank":
                centrality = nx.pagerank(subgraph, weight="weight")
            elif algorithm == "betweenness":
                centrality = nx.betweenness_centrality(subgraph, weight="weight")
            elif algorithm == "closeness":
                centrality = nx.closeness_centrality(subgraph, distance="weight")
            elif algorithm == "degree":
                centrality = dict(subgraph.degree(weight="weight"))
                # Normalize
                max_degree = max(centrality.values()) if centrality else 1
                centrality = {k: v / max_degree for k, v in centrality.items()}
            else:
                raise ValueError(f"Unknown centrality algorithm: {algorithm}")

            return centrality

    async def detect_communities(
        self,
        algorithm: str = "louvain",
    ) -> Dict[str, int]:
        """
        Detect communities/clusters in graph

        Args:
            algorithm: 'louvain' or 'label_propagation'

        Returns:
            Dict mapping node IDs to community IDs
        """
        async with self._lock:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()

            if algorithm == "louvain":
                # Use greedy modularity communities as approximation
                communities = nx.community.greedy_modularity_communities(undirected)
            elif algorithm == "label_propagation":
                communities = nx.community.label_propagation_communities(undirected)
            else:
                raise ValueError(f"Unknown community detection algorithm: {algorithm}")

            # Convert to dict
            node_to_community = {}
            for i, community in enumerate(communities):
                for node in community:
                    node_to_community[node] = i

            return node_to_community

    async def query_subgraph(
        self,
        node_ids: List[str],
        depth: int = 1,
    ) -> nx.DiGraph:
        """
        Extract subgraph around nodes

        Args:
            node_ids: Center nodes
            depth: How many hops to include

        Returns:
            Subgraph
        """
        async with self._lock:
            # Collect all nodes within depth
            all_nodes = set(node_ids)

            for _ in range(depth):
                new_nodes = set()
                for node in all_nodes:
                    if node in self.graph:
                        new_nodes.update(self.graph.successors(node))
                        new_nodes.update(self.graph.predecessors(node))
                all_nodes.update(new_nodes)

            return self.graph.subgraph(all_nodes).copy()

    async def delete_node(self, node_id: str) -> bool:
        """Delete node and its edges"""
        async with self._lock:
            if node_id in self.graph:
                self.graph.remove_node(node_id)
                logger.debug(f"Deleted node: {node_id}")
                return True
            return False

    async def delete_edge(self, source: str, target: str) -> bool:
        """Delete edge"""
        async with self._lock:
            if self.graph.has_edge(source, target):
                self.graph.remove_edge(source, target)
                logger.debug(f"Deleted edge: {source} --> {target}")
                return True
            return False

    async def clear(self) -> None:
        """Clear entire graph"""
        async with self._lock:
            self.graph.clear()
            logger.info("Graph store cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        stats = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "directed": self.directed,
        }

        if stats["num_nodes"] > 0:
            stats["density"] = nx.density(self.graph)

            # Calculate average degree
            degrees = [d for n, d in self.graph.degree()]
            stats["avg_degree"] = np.mean(degrees) if degrees else 0.0
            stats["max_degree"] = np.max(degrees) if degrees else 0

            # Check connectivity (for undirected or weakly for directed)
            if self.directed:
                stats["weakly_connected"] = nx.is_weakly_connected(self.graph)
                if stats["weakly_connected"]:
                    stats["diameter"] = nx.diameter(self.graph.to_undirected())
            else:
                stats["connected"] = nx.is_connected(self.graph)
                if stats["connected"]:
                    stats["diameter"] = nx.diameter(self.graph)

        return stats

    async def export_to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary format"""
        async with self._lock:
            return nx.node_link_data(self.graph)

    async def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import graph from dictionary format"""
        async with self._lock:
            self.graph = nx.node_link_graph(data)
            logger.info("Graph imported from dictionary")
