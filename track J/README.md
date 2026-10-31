# Track J: Software-Engineering Optimization (CI Test-Suite Minimization & Prioritization)

## 1. Overview & Scope
Track J investigates software-engineering optimization applied to continuous integration (CI) workflows. In large commercial and open-source codebases, regression test suites grow continuously, introducing severe CI bottlenecks and developer turnaround delays.

As specified by **Assignment 8**:
- **Domain**: Software engineering (test-suite minimization and prioritization).
- **Mathematical Formulations**:
  1. **Minimum-Weight Set Cover (ILP via HiGHS)**:
     $$\min \sum_{i=1}^n c_i x_i \quad \text{s.t.} \quad \sum_{i : r \in C_i} x_i \ge 1 \quad \forall r \in R, \quad x_i \in \{0, 1\}$$
     where $c_i$ is execution duration of test $i$ and $R$ is the set of system coverage requirements.
  2. **Submodular Greedy Additional Coverage**: Iteratively picks test case maximizing marginal new coverage per execution millisecond:
     $$\arg\max_{i} \frac{|C_i \cap U|}{c_i}$$
  3. **Budget-Constrained Dynamic Programming (0-1 Knapsack)**: Given a hard latency budget $B$ for pull-request gating, maximizes cumulative requirement coverage without exceeding $B$.
  4. **Average Percentage of Faults Detected (APFD)**: Evaluates prioritization effectiveness:
     $$\text{APFD} = 1 - \frac{\sum_{i=1}^m TF_i}{n \cdot m} + \frac{1}{2n}$$

---

## 2. Directory Structure
```
track J/
├── README.md               # Scope, formulation, setup, and results
├── src/
│   ├── models.py           # Test case models, CI suite generator, APFD calculator
│   └── solvers.py          # Naive, Greedy, Exact ILP, and Budgeted DP solvers
├── experiments/
│   └── runner.py           # Benchmark runner across suite sizes and APFD curves
└── tests/
    └── test_track_j.py     # Automated unit test suite (5 passed)
```

---

## 3. Execution Instructions

### Prerequisites
Ensure project dependencies are installed:
```bash
pip install -r requirements.txt
```

### Run Experiments
```bash
python "track J/experiments/runner.py"
```
Generated artifacts and plots will be placed in `results/track_j/`:
- `results/track_j/test_suite_minimization_results.csv`
- `results/track_j/test_suite_scalability_results.csv`
- `results/track_j/test_suite_minimization_analysis.png`

### Run Tests
```bash
pytest "track J/tests/test_track_j.py" -q
```

---

## 4. Key Empirical Findings

### A. Test Suite Minimization on 150-Test Suite (`results/track_j/test_suite_minimization_results.csv`)
- **Naive Full Suite**: 150 tests, total duration **$4,524.26$ ms** (100% coverage, 80 requirements).
- **Greedy Minimization**: 20 tests (**86.7% suite reduction**), duration **$227.11$ ms** (**95.0% time savings**), achieving **100% coverage**.
- **Exact ILP (HiGHS)**: 14 tests (**90.7% suite reduction**), duration **$201.51$ ms** (**95.5% time savings**), achieving **100% coverage** and provable minimum cost.
- **Budgeted DP ($B=400$ ms)**: 34 tests, duration **$412.85$ ms**, retaining 92.5% coverage within strict latency bounds.

### B. Scalability across Suite Sizes ($N \in \{50, 100, 200, 400\}$)
- As test suite size scales to $N=400$ (200 requirements), naive execution takes **$14.08$ seconds**, whereas exact ILP reduces execution to **$0.54$ seconds** (**$26.04\times$ speedup**).
- ILP solve time scales from $17.8$ ms ($N=50$) to $4,428.6$ ms ($N=400$), demonstrating that offline test-suite optimization easily amortizes across frequent CI commits.

