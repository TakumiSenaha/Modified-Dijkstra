"""
Constrained Max Load Path Algorithms for Weighted Graphs
=========================================================

This module provides an algorithm to compute a path from a source to a target that
maximizes the minimum edge weight along the path (i.e. the bottleneck capacity)
while satisfying delay constraints. This is an extension of the max_load_path algorithm
that adds delay constraint checking to ensure the total delay along the path does not
exceed a specified threshold.
"""

from heapq import heappop, heappush

import networkx as nx

__all__ = ["constrained_max_load_path"]


# @nx._dispatchable(edge_attrs=("weight", "delay"))
def constrained_max_load_path(
    G, source, target, weight="weight", delay="delay", max_delay=float("inf")
):
    """
    Returns a path from source to target that maximizes the minimum edge weight along the path,
    i.e. the bottleneck capacity, while satisfying delay constraints.

    This algorithm is a modification of the max_load_path algorithm. In addition to propagating
    the minimum edge weight (bottleneck) encountered along a path, it also tracks the cumulative
    delay and rejects paths that exceed the specified delay constraint. At every step, the
    algorithm selects the node whose current bottleneck value is the highest, and then it updates
    its neighbors with the minimum of the current bottleneck and the connecting edge's weight,
    but only if the total delay constraint is satisfied.

    Parameters
    ----------
    G : NetworkX graph
        The input graph.
    source : node
        The starting node.
    target : node
        The destination node.
    weight : string or function, optional (default="weight")
        If a string, then the edge weight is obtained from the edge attribute with that key.
        If a function, it should accept exactly three arguments: (u, v, edge_data) and return a numeric weight.
        For multigraphs, the minimum weight among parallel edges is used.
    delay : string or function, optional (default="delay")
        If a string, then the edge delay is obtained from the edge attribute with that key.
        If a function, it should accept exactly three arguments: (u, v, edge_data) and return a numeric delay.
        For multigraphs, the minimum delay among parallel edges is used.
    max_delay : float, optional (default=inf)
        The maximum allowed total delay along the path. Paths exceeding this constraint are rejected.

    Returns
    -------
    path : list
        A list of nodes representing the path from source to target that maximizes the bottleneck capacity
        while satisfying the delay constraint.

    Raises
    ------
    NodeNotFound
        If either the source or target is not in G.
    NetworkXNoPath
        If no path exists between source and target that satisfies the delay constraint.

    Examples
    --------
    >>> G = nx.Graph()
    >>> G.add_edge('a', 'b', weight=5, delay=10)
    >>> G.add_edge('b', 'c', weight=3, delay=5)
    >>> G.add_edge('a', 'c', weight=2, delay=8)
    >>> # With no delay constraint, prefer ['a', 'b', 'c'] (bottleneck=3)
    >>> constrained_max_load_path(G, 'a', 'c')
    ['a', 'b', 'c']
    >>> # With delay constraint of 12ms, still prefer ['a', 'b', 'c'] (delay=15ms > 12ms rejected)
    >>> # Fall back to ['a', 'c'] (bottleneck=2, delay=8ms)
    >>> constrained_max_load_path(G, 'a', 'c', max_delay=12)
    ['a', 'c']
    """
    # Check that the source and target are in the graph.
    if source not in G:
        raise nx.NodeNotFound(f"Source {source} not in graph")
    if target not in G:
        raise nx.NodeNotFound(f"Target {target} not in graph")

    # Priority queue: we use a min-heap with negative values to simulate a max-heap.
    pq = []

    # bottleneck: record the best (i.e. maximum) bottleneck value found so far for each node.
    # Initialize all nodes with negative infinity; the source is set to positive infinity.
    bottleneck = {node: float("-inf") for node in G}
    bottleneck[source] = float("inf")

    # EXTENSION: total_delay tracks the cumulative delay for the best path to each node.
    # Initialize all nodes with positive infinity; the source is set to zero.
    total_delay = {node: float("inf") for node in G}
    total_delay[source] = 0

    # pred: record the predecessor of each node for path reconstruction.
    pred = {node: None for node in G}

    # visited: to keep track of nodes whose best bottleneck value is finalized.
    visited = set()

    # Push the source node into the priority queue. We push (-bottleneck, node)
    # so that the highest bottleneck (largest positive value) comes out first.
    heappush(pq, (-bottleneck[source], source))

    # Main loop: process nodes in order of decreasing bottleneck value.
    while pq:
        curr_bottle_neg, u = heappop(pq)
        curr_bottle = -curr_bottle_neg  # convert back to positive

        # Skip if the node has already been finalized.
        if u in visited:
            continue
        visited.add(u)

        # If the target is reached, exit early.
        if u == target:
            break

        # Process each neighbor v of u.
        for v in G.neighbors(u):
            # Retrieve the edge weight and delay.
            edge_data = G[u][v]
            if G.is_multigraph():
                # For multigraphs, use the minimum edge weight and delay among all parallel edges.
                w = min(data.get(weight, 1) for data in edge_data.values())
                d = min(data.get(delay, 0) for data in edge_data.values())
            else:
                w = edge_data.get(weight, 1)
                d = edge_data.get(delay, 0)

            # EXTENSION: Calculate the new total delay for path to v via u.
            new_delay = total_delay[u] + d

            # EXTENSION: Check delay constraint - reject paths that exceed max_delay.
            if new_delay > max_delay:
                continue  # Skip this path due to delay constraint violation

            # The new bottleneck for v is the minimum of the current bottleneck for u and the weight of edge (u,v).
            new_bottle = min(curr_bottle, w)
            # If the new bottleneck is greater than the best known for v, update it.
            if new_bottle > bottleneck[v]:
                bottleneck[v] = new_bottle
                total_delay[v] = new_delay  # EXTENSION: Also update the delay
                pred[v] = u
                heappush(pq, (-new_bottle, v))

    # If the target's bottleneck value was never updated, no path exists that satisfies the constraint.
    if bottleneck[target] == float("-inf"):
        raise nx.NetworkXNoPath(
            f"No path found from {source} to {target} with delay constraint {max_delay}"
        )

    # Reconstruct the path from target to source using the predecessor dictionary.
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = pred[current]
    path.reverse()

    return path


def calculate_path_metrics(graph, path, weight="weight", delay="delay"):
    """
    Calculate the bottleneck capacity and total delay for a given path.

    Parameters
    ----------
    graph : NetworkX graph
        The input graph.
    path : list
        A list of nodes representing the path.
    weight : string, optional (default="weight")
        The edge attribute for weights (bandwidth).
    delay : string, optional (default="delay")
        The edge attribute for delays.

    Returns
    -------
    bottleneck : float
        The bottleneck capacity (minimum edge weight) along the path.
    total_delay : float
        The total delay (sum of edge delays) along the path.
    """
    if len(path) < 2:
        return float("inf"), 0

    bottleneck = float("inf")
    total_delay = 0

    for i in range(len(path) - 1):
        edge_data = graph[path[i]][path[i + 1]]
        if graph.is_multigraph():
            edge_weight = min(data.get(weight, 1) for data in edge_data.values())
            edge_delay = min(data.get(delay, 0) for data in edge_data.values())
        else:
            edge_weight = edge_data.get(weight, 1)
            edge_delay = edge_data.get(delay, 0)

        bottleneck = min(bottleneck, edge_weight)
        total_delay += edge_delay

    return bottleneck, total_delay


if __name__ == "__main__":
    """
    実行例：
    ```bash
    python src/constrained_routing.py networks/sample_graph 30 32 --max_delay 100
    ```
    """
    import argparse

    try:
        from utils.graph_utils import load_graph
    except ImportError:
        # Fallback graph loader for demonstration
        def load_graph(filename):
            G = nx.Graph()
            with open(filename, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        u, v, w = parts[0], parts[1], float(parts[2])
                        d = float(parts[3]) if len(parts) > 3 else 1.0
                        G.add_edge(u, v, weight=w, delay=d)
            return G

    # Create test graph for demonstration
    def create_test_graph():
        G = nx.Graph()
        G.add_edge("A", "B", weight=100, delay=10)  # High bandwidth, high delay
        G.add_edge("A", "C", weight=50, delay=5)  # Medium bandwidth, low delay
        G.add_edge("B", "D", weight=80, delay=3)  # High bandwidth, low delay
        G.add_edge("C", "D", weight=70, delay=4)  # Medium bandwidth, low delay
        G.add_edge("A", "D", weight=30, delay=15)  # Low bandwidth, high delay (direct)
        return G

    parser = argparse.ArgumentParser(
        description="制約付き最大ボトルネック帯域値の経路を探索"
    )
    parser.add_argument(
        "graph_file", nargs="?", type=str, help="エッジリスト形式のネットワークファイル"
    )
    parser.add_argument("start_node", nargs="?", help="開始ノード")
    parser.add_argument("end_node", nargs="?", help="終了ノード")
    parser.add_argument(
        "--max_delay", type=float, default=float("inf"), help="最大遅延制約"
    )
    parser.add_argument(
        "--demo", action="store_true", help="デモンストレーションを実行"
    )
    args = parser.parse_args()

    if args.demo or not args.graph_file:

        G = create_test_graph()
        source, target = "A", "D"
        max_delay = 12 if args.max_delay == float("inf") else args.max_delay

        print("\nネットワーク構成:")
        for u, v, data in G.edges(data=True):
            print(f"  {u}→{v}: {data['weight']}Mbps, {data['delay']}ms")

        print(f"開始ノード: {source}")
        print(f"終了ノード: {target}")
        print(f"最大遅延制約: {max_delay}ms")

    else:
        print(f"ファイル '{args.graph_file}' からグラフをロード中...")
        G = load_graph(args.graph_file)
        source, target = int(args.start_node), int(args.end_node)
        max_delay = args.max_delay

    try:
        path = constrained_max_load_path(G, source, target, max_delay=max_delay)
        bottleneck_value, delay_value = calculate_path_metrics(G, path)

        print(f"経路: {path}")
        print(f"ボトルネック帯域値: {bottleneck_value} Mbps")
        print(f"総遅延: {delay_value} ms")
        print(f"制約充足: {delay_value} ≤ {max_delay}")

    except nx.NetworkXNoPath:
        print(
            f"エラー: 制約 {max_delay}ms 内で {source} から {target} への経路が存在しません。"
        )
