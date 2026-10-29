# Track D: Submodular, Parallel, and Distributed Optimization

This directory contains the complete modular implementation, mathematical formulations, benchmarks, and validation tests for **Track D: Submodular, Parallel, and Distributed Optimization**, in accordance with Assignment 8 requirements (Chapter 6 methods: Submodular maximization, Multi-core parallel scaling with Amdahl/Gustafson laws, Federated Averaging, and Multi-Task Pareto optimization).

---

## Architecture & Module Structure

```text
track D/
├── README.md                 # Track documentation, formulations, and execution instructions
├── submodular/               # Submodular optimization
│   ├── facility_location.py  # Facility location objective, greedy selection, lazy greedy, exact search
│   └── __init__.py
├── parallel/                 # Multi-core parallel optimization & scaling laws
│   ├── parallel_opt.py       # Data-parallel logistic loss & gradient, speedup, Amdahl & Gustafson fit
│   └── __init__.py
├── distributed/              # Distributed & federated optimization
│   ├── fedavg.py             # FederatedDataset (IID & Non-IID), FedAvg algorithm, centralized baseline
│   └── __init__.py
├── multitask/                # Multi-objective / multi-task optimization
│   ├── multi_objective.py    # TwoTaskModel, MGDA Pareto min-norm solver, GradNorm, Equal weighting
│   └── __init__.py
├── experiments/              # Comprehensive benchmark runners
│   └── runner.py             # Executable benchmark suite generating plots and CSV tables
└── tests/                    # Unit testing suite
    └── test_track_d.py       # 9 unit tests for submodularity, parallel reduction, FedAvg, and MGDA
```

---

## Compulsory Coverage & Mathematical Formulations

### 1. Submodular Facility Location Maximization
- **Objective Function**:
  $$F(S) = \sum_{j \in V} \max_{i \in S} M_{ij}$$
  where $M_{ij} = \exp(-d_{ij} / \sigma)$ models client-facility utility.
- **Diminishing Returns (Submodularity)**:
  $$\forall S \subseteq T \subseteq V, \; e \notin T: \quad F(S \cup \{e\}) - F(S) \ge F(T \cup \{e\}) - F(T)$$
- **Greedy Approximation Guarantee (Nemhauser et al. 1978)**:
  $$F(S_{\text{greedy}}) \ge \left(1 - \frac{1}{e}\right) F(S^*) \approx 0.6321 \cdot F(S^*)$$
- **Lazy Greedy Acceleration**: Uses a max-heap with stale bound caching (Minoux 1978), reducing evaluation calls from $O(n \cdot k)$ to $O(n + k \log n)$.

### 2. Multi-Core Parallel Optimization & Scaling Laws
- **Speedup**: $S_p = \frac{T_1}{T_p}$, **Parallel Efficiency**: $E_p = \frac{S_p}{p}$.
- **Amdahl's Law (Fixed Workload)**:
  $$S_p = \frac{1}{s + \frac{1 - s}{p}}$$
  where $s$ is the sequential fraction.
- **Gustafson's Law (Scaled Speedup)**:
  $$S_p = s + p(1 - s)$$
- Empirically measured on a 180,000-sample regression gradient workload across 1, 2, and 4 CPU threads, fitting serial fraction $s \approx 0.05$ and capturing thread synchronization overhead.

### 3. Distributed & Federated Averaging (FedAvg)
- **Local Client Updates**:
  $$\theta_k^{(t, e+1)} = \theta_k^{(t, e)} - \eta \nabla \mathcal{L}_k(\theta_k^{(t, e)}), \quad e = 1, \dots, E$$
- **Server Model Aggregation**:
  $$\theta^{(t+1)} = \sum_{k \in S_t} \frac{n_k}{n} \theta_k^{(t, E)}$$
- Compared against centralized gradient descent on non-IID client distributions across $E \in \{1, 5, 10\}$ local steps over 20 communication rounds.

### 4. Multi-Task Pareto Optimization
- **Problem**: Simultaneous optimization of two conflicting task losses:
  $$\min_\theta \begin{bmatrix} \mathcal{L}_1(\theta) \\ \mathcal{L}_2(\theta) \end{bmatrix}$$
- **MGDA (Multiple Gradient Descent Algorithm)**:
  Finds the minimum-norm vector in the convex hull of task gradients:
  $$\min_{\alpha \in [0, 1]} \|\alpha g_1 + (1 - \alpha) g_2\|^2 \implies \alpha^* = \text{clip}\left(\frac{\|g_2\|^2 - g_1^T g_2}{\|g_1 - g_2\|^2}, 0, 1\right)$$
- **GradNorm**: Dynamically adjusts task gradient weights $w_i(t)$ using relative inverse training rates $r_i(t) = \frac{\mathcal{L}_i(t)/\mathcal{L}_i(0)}{\text{mean}_j(\mathcal{L}_j(t)/\mathcal{L}_j(0))}$.

---

## Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track D/tests/test_track_d.py" -v
```

### Run Experimental Benchmarks & Generate Plots
```bash
python "track D/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, and plots are saved to `results/track_d/`.

