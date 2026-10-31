# Tool Comparison & Effectiveness Record

This document records evidence-based observations regarding coding tools, execution environments, language platforms, and solver libraries evaluated during the assignment.

---

## 1. Environment & Runtime Observations

| Tool / Component | Context / Role | Observed Strengths | Observed Limitations | Evidence / Track Reference |
|:---|:---|:---|:---|:---|
| **Python 3.13 (Windows x64)** | Project Runtime | Broad library support, quick scripting | Unicode encoding considerations when piping CLI outputs with special symbols | Setup phase |
| **PowerShell 5.1 / 7+** | Shell Automation | Robust pipeline support for filesystem operations | Variable escaping when embedding inline blocks via command line strings | Setup phase |
| **pytest** | Test Harness | Simple test discovery and test structure | Requires cleanly isolated fixtures | Shared test suite |

---

## 2. Solver & Algorithmic Tool Evaluations

| Method / Algorithm | Observed Strengths | Observed Limitations | Empirical Evidence / Finding |
|:---|:---|:---|:---|
| **Newton's Method (2nd order)** | Quadratic local convergence; reaches exact quadratic optimum in 2 iterations ($8.7 \times 10^{-9}$ dist) and Rosenbrock in 8 iters ($1.89$ ms). | Inversion cost $O(d^3)$ per step; susceptible to negative eigenvalues without regularization/damping. | `results/track_a/convex_quadratic_results.csv`, `rosenbrock_results.csv` |
| **Gauss-Newton** | Superlinear convergence on non-linear least squares without calculating true 2nd derivative tensor; converges in 5 iters ($2.3$ ms). | Only applicable to sum-of-squares formulations; relies on well-conditioned Jacobian $J^T J$. | `results/track_a/gauss_newton_vs_gd.csv` |
| **Adam (Adaptive Moments)** | Superior handling of sparse/noisy gradients and ill-conditioned valleys; achieves 99.5% accuracy on MLP in 215 ms. | Requires hyperparameter tuning ($\beta_1, \beta_2$); slight step-size jitter near asymptotic minima. | `results/track_a/mlp_training_results.csv` |
| **Hessian-Vector Products (Pearlmutter finite-diff)** | Avoids $O(d^2)$ memory and $O(d^3)$ inversion overhead; accurately calculates $H(x)v$ with error $\approx 8.2 \times 10^{-11}$. | Sensitive to step-size $\epsilon$ under extreme floating point cancellation. | `results/track_a/curvature_and_hvp_results.csv` |
| **SciPy HiGHS (`milp`)** | Industrial-grade branch-and-cut MILP solver with dual simplex / interior-point pre-solve; exact integer optimality on Knapsack in $6$–$22$ ms. | Requires flat matrix canonical form ($A x \le b$, bounds); higher setup overhead on micro-instances ($< 10$ variables). | `results/track_b/knapsack_methods_comparison.csv` |
| **Dynamic Programming (Table Method)** | Guaranteed exact solution with no branching overhead; fastest exact solve on small integer capacities ($0.5$–$1.8$ ms). | Pseudo-polynomial memory and runtime $O(n W)$; unfeasible for non-integer or massive capacities. | `results/track_b/scalability_benchmark.csv` |
| **Simulated Annealing (QUBO)** | Flexible metaheuristic applicable to non-linear binary objectives and penalty formulations; found exact ground state on 8-node Max-Cut. | Stochastic convergence; parameter sensitivity on cooling schedule ($\alpha, T_0$); slower execution ($3.9$ s). | `results/track_b/maxcut_qubo_ising_baseline.csv` |
| **Qiskit Statevector Simulator** | Exact analytical simulation of parameterized circuits and Hamiltonians without shot noise; fast expectation values on $< 12$ qubits. | Memory usage scales exponentially $O(2^n)$; cannot directly represent physical open quantum system decoherence without custom noise channels. | `results/track_c/qaoa_vs_classical_benchmark.csv` |
| **Parameter-Shift Rule (Qiskit)** | Analytically exact quantum gradient without finite-difference truncation error; matches central differences to $10^{-4}$. | Requires $2d$ circuit queries per optimization step ($d$ parameters). | `results/track_c/quantum_gradient_strategies.csv` |
| **SPSA (Quantum Optimizer)** | Highly scalable gradient estimator requiring only 2 circuit queries regardless of parameter dimension $d$. | Gradient estimate has higher stochastic variance; requires careful learning rate decay schedule. | `results/track_c/quantum_gradient_strategies.csv` |
| **ThreadPoolExecutor (Multi-core Parallel)** | Low process-spawning overhead; achieves measurable speedup ($1.30\times$ on 2 workers) with shared-memory reduction. | Subject to Python GIL on pure-Python bytecode; efficiency diminishes ($E_4 = 0.305$) as synchronization overhead dominates small chunks. | `results/track_d/parallel_scaling_results.csv` |
| **Lazy Greedy (Submodular Heap)** | Evaluates fresh marginal gains only on demand; matches exact greedy selection while evaluating only 51 calls vs 90 in standard greedy. | Priority queue management overhead on tiny sets ($k \le 2$). | `results/track_d/submodular_facility_results.csv` |
| **MGDA (Min-norm Pareto Gradient)** | Solves for non-conflicting descent direction; prevents one task from dominating shared updates. | Requires computing full gradient vector per task; stationary points are local Pareto points. | `results/track_d/multitask_optimization_results.csv` |
| **Greedy Timetable Scheduler** | Ultra-fast heuristic scheduling ($< 2$ ms for 32 sessions); produces feasible schedules with zero hard violations. | Myopic local choices yield slightly higher soft penalties on tightly constrained instances ($35.0$ vs $28.0$ on Small). | `results/track_e/timetable_benchmark_results.csv` |
| **SciPy HiGHS (`milp`) for Timetabling** | Proves global optimality with branch-and-cut; achieves lowest soft penalty ($28.0$ vs $35.0$ on Small instance) with mathematical guarantees. | Problem matrix generation and solver runtime scale rapidly ($112$ ms for 288 vars, $821$ ms for 2,560 vars). | `results/track_e/timetable_benchmark_results.csv` |
| **Greedy Graph Coloring (Welsh-Powell)** | Instantaneous register allocation ($< 0.1$ ms); simple heuristic based on node degree. | Can use sub-optimal register counts on general non-chordal graphs. | `results/track_f/compiler_benchmark_results.csv` |
| **ILP Register Allocation (HiGHS)** | Mathematically minimal register allocation count; exact chromatic number calculation. | Formulates $N \times K$ binary variables; requires MILP branch-and-cut solver invocation ($5$–$15$ ms). | `results/track_f/compiler_benchmark_results.csv` |

| **xv6 Priority Scheduler with Aging** | Achieves 22%–32% turnaround time reduction over default Round-Robin; eliminates process starvation via dynamic priority aging. | Requires timer interrupt bookkeeping and priority queue searching overhead on large process counts. | `results/track_g/scheduler_benchmark_results.csv` |
| **Discrete-Event OS Simulator** | Deterministic, tick-accurate verification of kernel scheduling mechanics on environments lacking native cross-compilers/QEMU. | Models kernel scheduling and process state machine without emulating memory management unit (MMU) or physical device hardware interrupts. | `track G/simulator/scheduler_sim.py` |
| **SQLite B-Tree Index Optimization** | Delivers up to 3.6× speedup on point lookups and 1.74× on joins via targeted index definitions. | Low selectivity range queries suffer slowdown; causes 133% storage growth and 16% write throughput penalty. | `results/track_h/dbms_query_benchmark_results.csv` |
| **Qiskit Statevector Simulator (Algorithms)** | Exact statevector evolution for Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE, and Shor. | Statevector memory scales exponentially $O(2^n)$; incurs 5,586× wall-clock overhead over classical search on CPU. | `results/track_i/grover_vs_classical_scaling.csv` |
| **Variational Quantum Classifier (VQC)** | Expressive non-linear decision boundary using low parameter count (6 parameters achieve 80% accuracy). | High training latency (28.5 s, 10,830 circuit evaluations via parameter shift); vulnerable to depolarizing noise. | `results/track_i/qml_vs_classical_results.csv` |
| **SciPy HiGHS (`milp`) for Test-Suite Set Cover** | Proves mathematical minimum runtime for 100% test coverage; achieves 95.5% CI execution time savings. | Branch-and-cut solve time scales from 17.8 ms (N=50) to 4.4 s (N=400). | `results/track_j/test_suite_minimization_results.csv` |
| **Submodular Greedy Additional Coverage** | Near-instantaneous heuristic solution (< 45 ms at N=400); achieves 95.0% CI time savings. | Slightly larger test subset than exact ILP (20 vs 14 tests on N=150). | `results/track_j/test_suite_minimization_results.csv` |
