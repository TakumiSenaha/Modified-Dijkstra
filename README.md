# Modified Dijkstra Algorithm

## Overview
This repository provides an implementation of the **Modified Dijkstra Algorithm** for finding the **maximum load path** in a weighted graph. Unlike the traditional Dijkstra algorithm, which finds the shortest path by minimizing the sum of edge weights, this modified version finds a path that **maximizes the minimum edge weight** (bottleneck capacity) along the path.

This problem is particularly relevant for applications in **network routing, transportation logistics, and data communication**, where maximizing the weakest link in a path is more critical than minimizing the total cost.

## Problem Definition
Given a directed or undirected graph **G = (V, E)** where each edge **(u, v) \in E** has a weight **w(u, v) > 0**, the goal is to find a path from source **s** to destination **t** such that the **bottleneck capacity** of the path is maximized. The bottleneck capacity is defined as:

\[ \max_{P} \min_{(u, v) \in P} w(u, v) \]

where **P** is any valid path from **s** to **t**.

## Algorithm Description
The modified Dijkstra algorithm works as follows:

1. **Initialization**:
   - Set the bottleneck value for each node to \(-\infty\), except for the source node, which is set to \(+\infty\).
   - Use a **max-heap (priority queue)** to always expand the node with the highest bottleneck value.
   
2. **Processing Nodes**:
   - Extract the node with the largest bottleneck value.
   - For each neighboring node, update its bottleneck value as the **minimum of its current bottleneck and the weight of the connecting edge**.
   - If this new bottleneck is greater than the previously recorded bottleneck, update it and push the node into the priority queue.

3. **Path Reconstruction**:
   - Once the destination node is reached, backtrack using a predecessor list to reconstruct the path.

## Time Complexity Analysis
The modified Dijkstra algorithm has a time complexity of:
\[ O((n + m) \log n) \]
where:
- **n** is the number of nodes,
- **m** is the number of edges,
- **log n** arises from the priority queue operations (insertion and deletion).

Since each node is processed once and each edge is relaxed at most once, the overall complexity remains comparable to standard Dijkstra's algorithm, but with a **max-heap** instead of a **min-heap**.

## Implementation
The algorithm is implemented in Python using **NetworkX** for graph representation and **heapq** for efficient priority queue operations.

### Dependencies
To set up the environment, use the following command:
```bash
conda env create -f environment.yml
conda activate modified_dijkstra_env
```

### Usage
Run the algorithm with a given graph file and source-destination pair:
```bash
python src/modified_dijkstra.py networks/sample_graph.txt 1 10
```

### Example
```python
import networkx as nx
from src.modified_dijkstra import max_load_path

G = nx.Graph()
G.add_edge('A', 'B', weight=5)
G.add_edge('B', 'C', weight=10)
G.add_edge('A', 'C', weight=2)

path = max_load_path(G, 'A', 'C')
print(path)  # Expected: ['A', 'B', 'C']
```

## References
This algorithm is based on the work presented in:
- Wei, K., Gao, Y., Zhang, W., & Lin, S. (2019). "A Modified Dijkstra's Algorithm for Solving the Problem of Finding the Maximum Load Path." 2019 IEEE 2nd International Conference on Information and Computer Technologies. IEEE.
- Dijkstra, E. W. (1959). "A note on two problems in connexion with graphs." Numerische Mathematik, 1(1), 269–271.

## Citation

This implementation is based on the following research paper:

**Kaicong Wei, Ying Gao, Wei Zhang, Sheng Lin**,  
"A Modified Dijkstra’s Algorithm for Solving the Problem of Finding the Maximum Load Path,"  
2019 IEEE 2nd International Conference on Information and Computer Technologies (ICICT), pp. 10-13,  
DOI: [10.1109/INFOCT.2019.8711024](https://doi.org/10.1109/INFOCT.2019.8711024)

If you use this project for academic or research purposes, please consider citing their work:

```bibtex
@INPROCEEDINGS{8711024,
  author={Wei, Kaicong and Gao, Ying and Zhang, Wei and Lin, Sheng},
  booktitle={2019 IEEE 2nd International Conference on Information and Computer Technologies (ICICT)}, 
  title={A Modified Dijkstra’s Algorithm for Solving the Problem of Finding the Maximum Load Path}, 
  year={2019},
  pages={10-13},
  doi={10.1109/INFOCT.2019.8711024}
}
```

## License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Acknowledgments
This work was supported by the **Science and Technology Projects of Guangdong Province, China**, and the **Guangzhou Teaching Achievements Cultivation Project**.

---
This repository provides a robust implementation of the **Modified Dijkstra Algorithm** for **maximum load path finding**, offering a significant improvement over traditional shortest-path methods for applications where **bottleneck capacity** is the key factor.

