# Assignment Deliverables & Implementation Checklist

This checklist tracks assignment requirements, deliverable status, testing status, and completion across all shared files and individual tracks (A–J).

---

## 1. Shared Setup & Governance

- [x] Repository folder structure created (Tracks A–J with exact casing and spaces)
- [x] Shared documentation files initialized (`README.md`, `CHECKLIST.md`, `REPORT.md`, `failure_log.md`, `tool_comparison.md`)
- [x] Version control rules configured (`.gitignore`, `.gitattributes`)
- [x] Dependency specification initialized (`requirements.txt`)
- [x] Prompt records initialized under `prompts/`
- [ ] Assignment requirements document / PDF verified for all tracks

---

## 2. Track Implementation Matrix

| Track | Specification Status | Implementation Status | Test & Validation Status | Results Generated | Track Completion |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Track A** | Fully Specified (Sec. 5 & 6) | Completed | 11/11 Passed | Generated (`results/track_a/`) | 🟢 Complete |
| **Track B** | Fully Specified (Sec. 5 & 6) | Completed | 12/12 Passed | Generated (`results/track_b/`) | 🟢 Complete |
| **Track C** | Fully Specified (Sec. 5 & 6) | Completed | 7/7 Passed | Generated (`results/track_c/`) | 🟢 Complete |
| **Track D** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track E** | Case Study Proposed (Timetabling) | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track F** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track G** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track H** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track I** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track J** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |

---

## 3. Sequential Progress Milestones

- [x] **Phase 0: Setup and Shared Structure**
  - Project structure matches reference organization requirements.
  - No track implementations started prior to setup sign-off and specification confirmation.
- [x] **Phase 1: Track A (Continuous Optimization)**
  - [x] First-order methods: GD, SGD, Mini-batch SGD, Momentum, NAG, AdaGrad, RMSProp, Adam.
  - [x] Second-order & curvature methods: Newton's Method with damping, Gauss-Newton for least squares.
  - [x] Curvature approximations: Empirical diagonal Fisher, Hessian-Vector Products (HVP).
  - [x] Backpropagation distinct from optimizer implemented on TwoLayerMLP.
  - [x] Objective landscapes: Strongly convex quadratic, non-convex Rosenbrock, non-convex saddle escape.
  - [x] Empirical comparisons: Convergence curves, runtime, distance to optimum, learning rate sensitivity.
  - [x] Comprehensive test suite (11 unit tests passed).
  - [x] Artifacts, tables, and plots saved to `results/track_a/`.
- [x] **Phase 2: Track B (Discrete Optimization)**
  - [x] Combinatorial formulations: 0-1 Knapsack and Max-Cut graph partitioning.
  - [x] Greedy algorithms: Density-ratio knapsack packing and local search cut maximization.
  - [x] Dynamic Programming: Bellman recursion table algorithm $O(n W)$.
  - [x] Branch and Bound: Fractional LP continuous relaxation bounding with subtree pruning.
  - [x] Integer Linear Programming (ILP): SciPy HiGHS branch-and-cut optimization.
  - [x] QUBO & Ising formulation: Binary-to-spin conversion ($s_i = 1 - 2x_i$), Hamiltonian energy evaluation, quadratic constraint penalty tuning.
  - [x] Classical baseline for Track C: Exact classical ground state, matrices ($W, Q$), and metrics exported to `results/track_b/`.
  - [x] Comprehensive test suite (12 unit tests passed).
  - [x] Artifacts, tables, and plots saved to `results/track_b/`.
- [x] **Phase 3: Track C (Quantum Optimization)**
  - [x] QAOA formulation: Cost Hamiltonian $H_C = \sum \frac{w_{ij}}{2} Z_i Z_j$, transverse-field mixer $H_M = \sum X_i$, parameter updates $(\gamma, \beta)$.
  - [x] VQE implementation: Hardware-efficient RY-CX ansatz, expectation evaluation, exact diagonalization validation.
  - [x] Gradient strategies: Parameter-shift rule (exact $2d$ queries), SPSA (2 queries), Quantum Natural Gradient (QNG via Fubini-Study metric).
  - [x] Track B comparative baseline: Evaluated QAOA on 8-node Max-Cut ($101.0$ exact cut) achieving 0.92 approximation ratio ($93.0$ cut).
  - [x] Realistic simulations: Finite measurement shots ($128$ to $\infty$) and depolarizing hardware noise ($0.0$ to $0.15$).
  - [x] Barren plateau investigation: Exponential variance decay $\text{Var}[\partial E] \propto 2^{-n}$ across $N \in [2, 10]$ qubits.
  - [x] Comprehensive test suite (7 unit tests passed).
  - [x] Artifacts, tables, and plots saved to `results/track_c/`.
- [ ] **Phase 4: Track D**
- [ ] **Phase 5: Track E** (Verify Smart University Course Timetable Optimization against Track E requirements)
- [ ] **Phase 6: Track F**
- [ ] **Phase 7: Track G**
- [ ] **Phase 8: Track H**
- [ ] **Phase 9: Track I**
- [ ] **Phase 10: Track J**
- [ ] **Phase 11: Final Synthesis** (Consolidate REPORT.md, tool_comparison.md, failure_log.md)

