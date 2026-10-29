# Track B: Discrete Optimization

This directory contains the complete modular implementation, mathematical formulations, benchmarks, and validation tests for **Track B: Discrete Optimization**, in accordance with Assignment 8 requirements (Chapter 6 discrete methods: Greedy, Integer Linear Programming, Branch-and-Bound, Dynamic Programming, and QUBO/Ising formulations).

---

## Architecture & Module Structure

```text
track B/
├── README.md                 # Track documentation and execution instructions
├── problems/                 # Problem definitions & mathematical representations
│   ├── base.py               # DiscreteSolution dataclass container
│   ├── knapsack.py           # 0-1 Knapsack problem with QUBO penalty conversion
│   ├── maxcut.py             # Max-Cut graph formulation, QUBO & Ising transformations
│   └── __init__.py
├── algorithms/               # Discrete optimization algorithms
│   ├── solvers.py            # Greedy, DP, Branch-and-Bound, SciPy HiGHS ILP, QUBO SA, Exact Ising
│   └── __init__.py
├── experiments/              # Benchmark runners & reproducible evaluation
│   └── runner.py             # Knapsack comparison, scalability vs N, QUBO/Ising baselines
└── tests/                    # Unit testing suite
    └── test_track_b.py       # Exactness, bounds, conversions, and validation tests
```

---

## Compulsory Coverage & Mathematical Formulations

### 1. 0-1 Knapsack Problem
- **Formulation**:
  $$\max_{x \in \{0, 1\}^n} \sum_{i=1}^n v_i x_i \quad \text{s.t.} \quad \sum_{i=1}^n w_i x_i \le W$$
- **Solvers Implemented**:
  1. **Greedy Heuristic**: Orders items by density ratio $\frac{v_i}{w_i}$ in descending order; greedily packs items until capacity is reached. $O(n \log n)$.
  2. **Dynamic Programming**: Bellman recursion $dp[i, w] = \max(dp[i-1, w], dp[i-1, w - w_i] + v_i)$. Pseudo-polynomial $O(n W)$.
  3. **Branch and Bound**: Depth-First Search with continuous LP fractional relaxation upper bound:
     $$\text{Bound}(S) = \sum_{j \in S} v_j + \sum_{k \notin S, \text{fits}} v_k + \frac{W_{\text{rem}}}{w_{\text{frac}}} v_{\text{frac}}$$
     Prunes subtrees when $\text{Bound}(S) \le \text{BestVal}$.
  4. **Integer Linear Programming (ILP)**: Solved using SciPy's HiGHS branch-and-cut simplex/interior-point backend (`scipy.optimize.milp`).

### 2. Max-Cut Graph Formulation & QUBO / Ising Conversion
- **Graph Cut**: Given weighted graph $G = (V, E, W)$, partition $V$ into $(S, \bar{S})$ to maximize:
  $$\text{Cut}(x) = \sum_{i < j} w_{ij} (x_i + x_j - 2 x_i x_j), \quad x_i \in \{0, 1\}$$
- **QUBO (Quadratic Unconstrained Binary Optimization)**:
  $$\min_{x \in \{0, 1\}^n} x^T Q x, \quad \text{where } Q_{ii} = -\sum_{j} w_{ij}, \; Q_{ij} = w_{ij} \; (i \neq j)$$
- **Binary-to-Spin Conversion to Ising Model**:
  Using transformation $x_i = \frac{1 - s_i}{2}$ where spin $s_i \in \{-1, +1\}$:
  $$H(s) = \sum_{i < j} J_{ij} s_i s_j + \sum_i h_i s_i + C$$
  For Max-Cut, $J_{ij} = \frac{w_{ij}}{2}$, $h_i = 0$, and $C = -\frac{1}{2} \sum_{i < j} w_{ij}$.
  Minimizing the Ising Hamiltonian $H(s)$ directly yields the Maximum Cut.
- **Track C Baseline Deliverable**:
  The classical exact ground-state cut ($101.0$), ground energy ($-101.0$), and the adjacency/QUBO matrices are exported to `results/track_b/` (`track_b_maxcut_W.npy` and `track_b_maxcut_Q.npy`) for direct baseline comparison in Track C (QAOA).

### 3. Penalty Terms for Constrained QUBO
- Enforces knapsack capacity inequality via quadratic penalty:
  $$\min_{x} -v^T x + P \cdot \max(0, w^T x - W)^2$$
- Penalty tuning experiments demonstrate that when $P \ge \max_i \frac{v_i}{w_i}$ ($P \ge 2.5$), constraint violations drop to $0.0$, generating feasible solutions.

---

## Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track B/tests/test_track_b.py" -v
```

### Run Experimental Benchmarks & Generate Plots
```bash
python "track B/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, adjacency matrices, and plots are saved to `results/track_b/`.

