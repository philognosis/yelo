"""
Graph Analysis for Multi-Agent Networks.

This module provides graph-based analysis for multi-agent systems:
- Agent network topology analysis
- Centrality measures (degree, betweenness, closeness, eigenvector)
- Clustering coefficients and community detection
- Network flow and connectivity analysis
"""

from typing import List, Dict, Any, Tuple, Set, Optional
import numpy as np
from collections import deque, defaultdict, Counter


class AgentNetwork:
    """
    Represents a network of agents and their connections.

    The network can be directed or undirected, weighted or unweighted.
    """

    def __init__(self, directed: bool = False):
        """
        Initialize an agent network.

        Args:
            directed: If True, edges have direction (A->B != B->A)
        """
        self.directed = directed
        self.adjacency = defaultdict(dict)  # adjacency[u][v] = weight
        self.nodes = set()

    def add_edge(
        self,
        source: int,
        target: int,
        weight: float = 1.0,
    ) -> None:
        """
        Add an edge between two agents.

        Args:
            source: Source agent ID
            target: Target agent ID
            weight: Edge weight (default: 1.0)
        """
        self.nodes.add(source)
        self.nodes.add(target)
        self.adjacency[source][target] = weight

        if not self.directed:
            self.adjacency[target][source] = weight

    def add_node(self, node_id: int) -> None:
        """Add a node to the network."""
        self.nodes.add(node_id)

    def get_neighbors(self, node_id: int) -> Dict[int, float]:
        """
        Get neighbors of a node.

        Returns:
            dict: Mapping of neighbor_id -> edge_weight
        """
        return self.adjacency.get(node_id, {})

    def get_degree(self, node_id: int) -> int:
        """Get the degree (number of connections) of a node."""
        if self.directed:
            in_degree = sum(1 for n in self.adjacency if node_id in self.adjacency[n])
            out_degree = len(self.adjacency.get(node_id, {}))
            return in_degree + out_degree
        else:
            return len(self.adjacency.get(node_id, {}))

    def get_adjacency_matrix(self) -> Tuple[np.ndarray, List[int]]:
        """
        Get adjacency matrix representation.

        Returns:
            tuple: (adjacency_matrix, node_list)
        """
        node_list = sorted(self.nodes)
        n = len(node_list)
        node_to_idx = {node: i for i, node in enumerate(node_list)}

        matrix = np.zeros((n, n))
        for source, targets in self.adjacency.items():
            i = node_to_idx[source]
            for target, weight in targets.items():
                j = node_to_idx[target]
                matrix[i, j] = weight

        return matrix, node_list


def analyze_agent_network(
    edges: List[Tuple[int, int, float]],
    directed: bool = False,
) -> Dict[str, Any]:
    """
    Analyze an agent network topology.

    Args:
        edges: List of tuples (source, target, weight) defining the network
        directed: If True, treat edges as directed

    Returns:
        dict: Network analysis metrics including:
            - n_nodes: Number of agents
            - n_edges: Number of connections
            - density: Network density
            - avg_degree: Average node degree
            - is_connected: Whether the network is connected
            - diameter: Network diameter (longest shortest path)
            - clustering_coefficient: Average clustering coefficient

    Example:
        >>> edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0)]
        >>> metrics = analyze_agent_network(edges, directed=False)
        >>> print(f"Network density: {metrics['density']:.2f}")
    """
    network = AgentNetwork(directed=directed)

    # Build network
    for source, target, weight in edges:
        network.add_edge(source, target, weight)

    n_nodes = len(network.nodes)
    n_edges = len(edges)

    # Calculate density
    if directed:
        max_edges = n_nodes * (n_nodes - 1)
    else:
        max_edges = n_nodes * (n_nodes - 1) / 2

    density = n_edges / max_edges if max_edges > 0 else 0.0

    # Calculate average degree
    degrees = [network.get_degree(node) for node in network.nodes]
    avg_degree = np.mean(degrees) if degrees else 0.0

    # Check connectivity
    is_connected = _is_connected(network)

    # Calculate diameter (if connected)
    diameter = _calculate_diameter(network) if is_connected else float('inf')

    # Calculate average clustering coefficient
    avg_clustering = _average_clustering_coefficient(network)

    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'density': density,
        'avg_degree': avg_degree,
        'max_degree': max(degrees) if degrees else 0,
        'min_degree': min(degrees) if degrees else 0,
        'is_connected': is_connected,
        'diameter': diameter,
        'avg_clustering': avg_clustering,
        'degree_distribution': degrees,
    }


def calculate_centrality(
    edges: List[Tuple[int, int, float]],
    centrality_type: str = 'degree',
    directed: bool = False,
) -> Dict[int, float]:
    """
    Calculate centrality measures for agents in a network.

    Centrality measures identify the most important or influential agents.

    Args:
        edges: List of tuples (source, target, weight) defining the network
        centrality_type: Type of centrality - 'degree', 'betweenness', 'closeness', 'eigenvector'
        directed: If True, treat edges as directed

    Returns:
        dict: Mapping of agent_id -> centrality_score

    Example:
        >>> edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (1, 3, 1.0)]
        >>> degree_centrality = calculate_centrality(edges, 'degree')
        >>> print(f"Agent 1 centrality: {degree_centrality[1]:.2f}")
    """
    network = AgentNetwork(directed=directed)

    # Build network
    for source, target, weight in edges:
        network.add_edge(source, target, weight)

    if centrality_type == 'degree':
        return _degree_centrality(network)
    elif centrality_type == 'betweenness':
        return _betweenness_centrality(network)
    elif centrality_type == 'closeness':
        return _closeness_centrality(network)
    elif centrality_type == 'eigenvector':
        return _eigenvector_centrality(network)
    else:
        raise ValueError(f"Unknown centrality type: {centrality_type}")


def calculate_clustering_coefficient(
    edges: List[Tuple[int, int, float]],
    node_id: Optional[int] = None,
) -> float:
    """
    Calculate clustering coefficient for a node or the entire network.

    The clustering coefficient measures how much nodes tend to cluster together.
    For a node, it's the fraction of possible triangles that exist.

    Args:
        edges: List of tuples (source, target, weight) defining the network
        node_id: If provided, calculate for specific node; otherwise, average for network

    Returns:
        float: Clustering coefficient (0.0 to 1.0)

    Example:
        >>> edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 0, 1.0), (0, 3, 1.0)]
        >>> # Triangle between 0, 1, 2
        >>> cc = calculate_clustering_coefficient(edges, node_id=0)
        >>> print(f"Node 0 clustering: {cc:.2f}")
    """
    network = AgentNetwork(directed=False)

    # Build network
    for source, target, weight in edges:
        network.add_edge(source, target, weight)

    if node_id is not None:
        return _node_clustering_coefficient(network, node_id)
    else:
        return _average_clustering_coefficient(network)


# Helper functions for centrality calculations

def _degree_centrality(network: AgentNetwork) -> Dict[int, float]:
    """Calculate degree centrality for all nodes."""
    n_nodes = len(network.nodes)
    if n_nodes <= 1:
        return {node: 0.0 for node in network.nodes}

    centrality = {}
    max_degree = n_nodes - 1

    for node in network.nodes:
        degree = network.get_degree(node)
        centrality[node] = degree / max_degree

    return centrality


def _betweenness_centrality(network: AgentNetwork) -> Dict[int, float]:
    """
    Calculate betweenness centrality for all nodes.

    Betweenness measures how often a node lies on the shortest path between other nodes.
    """
    centrality = {node: 0.0 for node in network.nodes}

    # For each pair of nodes, find shortest paths
    for source in network.nodes:
        # BFS from source to find shortest paths
        paths = _single_source_shortest_paths(network, source)

        for target in network.nodes:
            if source == target:
                continue

            # Find all shortest paths from source to target
            if target in paths:
                # Count how many shortest paths go through each intermediate node
                for path in paths[target]:
                    for intermediate in path[1:-1]:  # Exclude source and target
                        centrality[intermediate] += 1.0

    # Normalize
    n_nodes = len(network.nodes)
    if n_nodes > 2:
        norm = (n_nodes - 1) * (n_nodes - 2)
        if not network.directed:
            norm = norm / 2
        centrality = {node: c / norm for node, c in centrality.items()}

    return centrality


def _closeness_centrality(network: AgentNetwork) -> Dict[int, float]:
    """
    Calculate closeness centrality for all nodes.

    Closeness measures the average distance from a node to all other nodes.
    """
    centrality = {}

    for node in network.nodes:
        # Calculate shortest paths to all other nodes
        distances = _single_source_shortest_path_lengths(network, node)

        if len(distances) <= 1:
            centrality[node] = 0.0
            continue

        # Sum of distances to all reachable nodes
        total_distance = sum(distances.values())

        if total_distance > 0:
            # Closeness = (n - 1) / sum_of_distances
            centrality[node] = (len(distances) - 1) / total_distance
        else:
            centrality[node] = 0.0

    return centrality


def _eigenvector_centrality(
    network: AgentNetwork,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> Dict[int, float]:
    """
    Calculate eigenvector centrality using power iteration.

    Eigenvector centrality assigns scores based on connections to high-scoring nodes.
    """
    adjacency_matrix, node_list = network.get_adjacency_matrix()
    n = len(node_list)

    if n == 0:
        return {}

    # Initialize centrality vector
    centrality = np.ones(n) / n

    # Power iteration
    for _ in range(max_iterations):
        new_centrality = adjacency_matrix @ centrality

        # Normalize
        norm = np.linalg.norm(new_centrality)
        if norm > 0:
            new_centrality = new_centrality / norm

        # Check convergence
        if np.allclose(centrality, new_centrality, atol=tolerance):
            break

        centrality = new_centrality

    # Convert to dictionary
    return {node_list[i]: centrality[i] for i in range(n)}


# Helper functions for network analysis

def _is_connected(network: AgentNetwork) -> bool:
    """Check if the network is connected."""
    if not network.nodes:
        return True

    # For directed graphs, check weak connectivity
    start_node = next(iter(network.nodes))
    visited = _bfs(network, start_node, ignore_direction=network.directed)

    return len(visited) == len(network.nodes)


def _bfs(
    network: AgentNetwork,
    start_node: int,
    ignore_direction: bool = False,
) -> Set[int]:
    """
    Breadth-first search from start_node.

    Returns set of visited nodes.
    """
    visited = set()
    queue = deque([start_node])
    visited.add(start_node)

    while queue:
        node = queue.popleft()

        # Get neighbors
        neighbors = set(network.get_neighbors(node).keys())

        # If ignoring direction, also include incoming edges
        if ignore_direction:
            for n in network.nodes:
                if node in network.get_neighbors(n):
                    neighbors.add(n)

        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return visited


def _calculate_diameter(network: AgentNetwork) -> float:
    """Calculate network diameter (longest shortest path)."""
    max_distance = 0

    for source in network.nodes:
        distances = _single_source_shortest_path_lengths(network, source)

        if distances:
            max_dist = max(distances.values())
            max_distance = max(max_distance, max_dist)

    return max_distance


def _single_source_shortest_path_lengths(
    network: AgentNetwork,
    source: int,
) -> Dict[int, int]:
    """
    Calculate shortest path lengths from source to all other nodes using BFS.

    Returns dict of node -> distance.
    """
    distances = {source: 0}
    queue = deque([source])

    while queue:
        node = queue.popleft()
        current_distance = distances[node]

        for neighbor in network.get_neighbors(node):
            if neighbor not in distances:
                distances[neighbor] = current_distance + 1
                queue.append(neighbor)

    return distances


def _single_source_shortest_paths(
    network: AgentNetwork,
    source: int,
) -> Dict[int, List[List[int]]]:
    """
    Find all shortest paths from source to all other nodes.

    Returns dict of target -> list of paths (each path is a list of nodes).
    """
    # BFS with path tracking
    paths = {source: [[source]]}
    distances = {source: 0}
    queue = deque([source])

    while queue:
        node = queue.popleft()
        current_distance = distances[node]

        for neighbor in network.get_neighbors(node):
            if neighbor not in distances:
                # First time reaching this neighbor
                distances[neighbor] = current_distance + 1
                queue.append(neighbor)
                paths[neighbor] = []

            if distances[neighbor] == current_distance + 1:
                # Found a shortest path to neighbor through node
                for path in paths[node]:
                    paths[neighbor].append(path + [neighbor])

    return paths


def _node_clustering_coefficient(network: AgentNetwork, node_id: int) -> float:
    """Calculate clustering coefficient for a single node."""
    neighbors = list(network.get_neighbors(node_id).keys())
    k = len(neighbors)

    if k < 2:
        return 0.0

    # Count edges between neighbors
    edges_between_neighbors = 0
    for i, neighbor1 in enumerate(neighbors):
        for neighbor2 in neighbors[i + 1:]:
            if neighbor2 in network.get_neighbors(neighbor1):
                edges_between_neighbors += 1

    # Maximum possible edges between k neighbors
    max_edges = k * (k - 1) / 2

    return edges_between_neighbors / max_edges if max_edges > 0 else 0.0


def _average_clustering_coefficient(network: AgentNetwork) -> float:
    """Calculate average clustering coefficient for the network."""
    if not network.nodes:
        return 0.0

    coefficients = [
        _node_clustering_coefficient(network, node)
        for node in network.nodes
    ]

    return np.mean(coefficients)


def detect_communities(
    edges: List[Tuple[int, int, float]],
    method: str = 'label_propagation',
) -> Dict[int, int]:
    """
    Detect communities (clusters) in the agent network.

    Args:
        edges: List of tuples (source, target, weight) defining the network
        method: Community detection method - 'label_propagation' or 'connected_components'

    Returns:
        dict: Mapping of agent_id -> community_id

    Example:
        >>> edges = [(0, 1, 1.0), (1, 2, 1.0), (3, 4, 1.0), (4, 5, 1.0)]
        >>> communities = detect_communities(edges)
        >>> # Should find two communities: {0,1,2} and {3,4,5}
    """
    network = AgentNetwork(directed=False)

    for source, target, weight in edges:
        network.add_edge(source, target, weight)

    if method == 'connected_components':
        return _connected_components(network)
    elif method == 'label_propagation':
        return _label_propagation(network)
    else:
        raise ValueError(f"Unknown method: {method}")


def _connected_components(network: AgentNetwork) -> Dict[int, int]:
    """Find connected components in the network."""
    communities = {}
    community_id = 0
    visited = set()

    for node in network.nodes:
        if node not in visited:
            # BFS to find all nodes in this component
            component = _bfs(network, node)
            for n in component:
                communities[n] = community_id
                visited.add(n)
            community_id += 1

    return communities


def _label_propagation(
    network: AgentNetwork,
    max_iterations: int = 100,
) -> Dict[int, int]:
    """
    Simple label propagation algorithm for community detection.

    Each node adopts the label most common among its neighbors.
    """
    # Initialize: each node has its own label
    labels = {node: node for node in network.nodes}

    for _ in range(max_iterations):
        updated = False
        nodes = list(network.nodes)
        np.random.shuffle(nodes)  # Random order

        for node in nodes:
            neighbors = network.get_neighbors(node)
            if not neighbors:
                continue

            # Count neighbor labels
            neighbor_labels = [labels[n] for n in neighbors]
            label_counts = Counter(neighbor_labels)

            # Choose most common label
            most_common_label = label_counts.most_common(1)[0][0]

            if labels[node] != most_common_label:
                labels[node] = most_common_label
                updated = True

        if not updated:
            break

    # Renumber labels to be consecutive integers
    unique_labels = sorted(set(labels.values()))
    label_mapping = {old: new for new, old in enumerate(unique_labels)}
    labels = {node: label_mapping[label] for node, label in labels.items()}

    return labels
