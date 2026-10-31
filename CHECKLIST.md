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
| **Track D** | Fully Specified (Sec. 5 & 6) | Completed | 9/9 Passed | Generated (`results/track_d/`) | 🟢 Complete |
| **Track E** | Case Study Verified & Specified | Completed | 7/7 Passed | Generated (`results/track_e/`) | 🟢 Complete |
| **Track F** | Fully Specified (Sec. 5 & 6) | Completed | 8/8 Passed | Generated (`results/track_f/`) | 🟢 Complete |
| **Track G** | Fully Specified (Sec. 5 & 6) | Completed | 6/6 Passed | Generated (`results/track_g/`) | 🟢 Complete |
| **Track H** | Fully Specified (Sec. 5 & 6) | Completed | 5/5 Passed | Generated (`results/track_h/`) | 🟢 Complete |
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
- [x] **Phase 4: Track D (Submodular, Parallel & Distributed Optimization)**
  - [x] Submodular optimization: Facility location / set coverage objective, diminishing returns verification, standard greedy and lazy greedy (heap-accelerated) selection, $(1 - 1/e)$ approximation verification against exact exhaustive search.
  - [x] Parallel program optimization: Multi-core data parallelism on continuous optimization workload, speedup and parallel efficiency measurements, Amdahl's Law and Gustafson's Law theoretical parameter estimation ($s \approx 0.05$).
  - [x] Distributed and federated optimization: Federated Averaging (FedAvg) vs. centralized training across varying local steps $E \in \{1, 5, 10\}$ and communication rounds on non-IID client distributions.
  - [x] Multi-task Pareto optimization: Two-task conflicting regression model, analytical MGDA minimum-norm gradient solver, GradNorm dynamic weighting, and comparison against equal task weighting.
  - [x] Comprehensive test suite (9 unit tests passed).
  - [x] Artifacts, tables, and plots saved to `results/track_d/`.
- [x] **Phase 5: Track E (Smart University Course Timetable Optimization)**
  - [x] Verification against Track E open-domain case study criteria (Sections 3, 4, 5, 6).
  - [x] Problem formulation: Courses/sessions, faculty, rooms with capacities, time slots, student cohorts.
  - [x] Hard constraints: Room, faculty, and cohort double-booking prevention, room capacity sufficiency, faculty availability.
  - [x] Soft constraints: Undesirable slot avoidance, excess capacity minimization, faculty preference adherence, student gap reduction.
  - [x] Algorithms: Greedy most-constrained-first scheduler vs. Exact Integer Linear Programming (SciPy HiGHS backend).
  - [x] Independent validator: Validates all hard/soft constraints separately; verified with deliberately injected conflicts.
  - [x] Empirical evaluation across Small, Medium, Large instances (Feasibility, violations, penalties, utilization, runtime).
  - [x] Comprehensive test suite (7 unit tests passed).
  - [x] Artifacts, tables, and schedule grid occupancy plots saved to `results/track_e/`.
- [x] **Phase 6: Track F (Compiler Optimization)**
  - [x] MiniLang compiler frontend: Lexer, recursive descent parser, AST construction (variables, conditionals, while-loops, prints).
  - [x] Intermediate Representation: Linear 3-Address Code (TAC), temporary variables, branch labels, IR generator.
  - [x] Four compulsory optimizations: Constant Folding & Propagation, Dead-Code Elimination, Common Subexpression Elimination, Strength Reduction.
  - [x] Compiler decision posed as Chapter 6 optimization: Register Allocation via Graph Coloring (ILP HiGHS solver vs. Greedy Welsh-Powell).
  - [x] Code execution: 3-Address Code Virtual Machine (`TACVirtualMachine`) evaluating dynamic cycle counts and runtime.
  - [x] Correctness verification: Tested 100% output equivalence between unoptimized and optimized code.
  - [x] Comprehensive test suite (8 unit tests passed).
  - [x] Artifacts, benchmark tables, and comparative plots saved to `results/track_f/`.
- [x] **Phase 7: Track G (Operating-System Optimization)**
  - [x] Target optimization: Priority-Based Process Scheduler with Dynamic Aging in MIT xv6-riscv.
  - [x] Kernel source modifications: PCB extensions (`priority`, `dynamic_priority`, `wait_ticks`), priority scheduler loop, dynamic aging promotion, and syscalls `setpriority` / `getpinfo`.
  - [x] Unified kernel patch: Generated `xv6_priority_scheduler.patch`.
  - [x] Discrete-event simulator: Built cycle-accurate xv6 scheduler simulator reproducing state transitions, quantum yields, and aging.
  - [x] Empirical evaluation across 3 workloads: CPU-Bound Batch, Interactive I/O Burst, and Mixed Heterogeneous.
  - [x] Metrics evaluated: Turnaround time, waiting time, response time, context switches, and Jain's Fairness Index.
  - [x] Comprehensive test suite (6 unit tests passed).
  - [x] Artifacts, tables, and performance plots saved to `results/track_g/`.
- [ ] **Phase 8: Track H**
- [ ] **Phase 9: Track I**
- [ ] **Phase 10: Track J**
- [ ] **Phase 11: Final Synthesis** (Consolidate REPORT.md, tool_comparison.md, failure_log.md)

