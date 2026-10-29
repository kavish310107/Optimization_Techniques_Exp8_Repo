# Final Assignment Report: Optimize Anything

## Executive Summary
*To be completed after empirical runs across Tracks A–J.*

---

## 1. Introduction & Objectives
This report compiles the methodology, mathematical formulations, algorithmic implementations, and empirical results for the "Optimize Anything" Optimization Techniques assignment.

---

## 2. Track Methodologies and Implementations
*(Detailed per track as implementations are developed)*

### 2.1 Track A: Continuous Optimization
- **Problem Formulations & Landscapes**:
  - **Strongly Convex Quadratic**: $f(x) = \frac{1}{2} x^T Q x - b^T x + c$ with $Q = \text{diag}(20, 2)$, condition number $\kappa = 10$. Optimum $x^* = [0.25, 0.5]^T$, $f^* = -0.875$.
  - **Non-Convex Rosenbrock Valley**: $f(x_1, x_2) = (1 - x_1)^2 + 100(x_2 - x_1^2)^2$. Optimum $x^* = [1.0, 1.0]^T$, $f^* = 0.0$. Exhibits an ill-conditioned, curved parabolic valley that tests adaptive moment tracking and momentum damping.
  - **Non-Convex Saddle Point Escape**: $f(x_1, x_2) = \frac{1}{2} x_1^2 - \frac{1}{2} x_2^2 + 0.1 x_2^4$. Origin $(0, 0)$ has $\nabla f(0, 0) = [0, 0]^T$ with indefinite Hessian eigenvalues $+1$ and $-1$.
  - **Non-Linear Least Squares**: Exponential decay model $y(t) = \theta_0 e^{-\theta_1 t}$.
  - **Binary Classification Neural Network**: Two-layer MLP (2-8-1) trained with binary cross-entropy loss, demonstrating analytical backpropagation separated from optimizer parameter updates.
- **Algorithms Evaluated**:
  - First-order: Gradient Descent (GD), Polyak Momentum, Nesterov Accelerated Gradient (NAG), AdaGrad, RMSProp, Adam.
  - Second-order: Damped Newton's Method (Levenberg-Marquardt), Gauss-Newton.
  - Curvature Approximations: Diagonal empirical Fisher natural gradient, Hessian-Vector Products (Pearlmutter finite-difference formulation).
- **Key Empirical Findings**:
  - **Newton's Method**: Exhibits quadratic local convergence, reaching the exact quadratic optimum in 2 iterations ($8.7 \times 10^{-9}$ distance) and Rosenbrock in 8 iterations ($1.89$ ms).
  - **Accelerated First-Order (NAG vs. Momentum vs. GD)**: On the convex quadratic, NAG converged in 89 iterations to within $4.95 \times 10^{-7}$ of the optimum, outperforming unaccelerated GD (which reached $8.37 \times 10^{-4}$ after 100 iterations).
  - **Valley Traversal (Rosenbrock)**: Momentum and NAG reached lower loss values ($1.82 \times 10^{-3}$ and $2.51 \times 10^{-3}$) than standard GD ($2.28$) within 500 iterations due to momentum carrying updates along the valley floor.
  - **Saddle Point Escape**: While unregularized Newton is attracted to the stationary saddle point $(0, 0)$, first-order momentum, Adam, and RMSProp successfully escaped along the negative curvature direction to the global minimum ($f^* = -0.625$).
  - **Gauss-Newton vs. GD**: Gauss-Newton reached the least-squares optimum in 5 iterations ($2.3$ ms), whereas GD required 50+ iterations with residual loss $0.383$.
  - **Backpropagation & Batch Size**: Pure SGD (batch size 1) achieved 98.0% accuracy in 4793 ms; Mini-batch Adam (batch size 32) achieved the best accuracy (99.5%) in only 215 ms.
  - **Hessian-Vector Products**: HVP computed via Pearlmutter's difference quotient matched analytic $H v$ with Euclidean error $< 8.2 \times 10^{-11}$ without storing the $n \times n$ Hessian matrix.
- **Artifacts Generated**:
  - Tables: `convex_quadratic_results.csv`, `rosenbrock_results.csv`, `saddle_escape_results.csv`, `gauss_newton_vs_gd.csv`, `mlp_training_results.csv`, `lr_sensitivity.csv`, `curvature_and_hvp_results.csv`.
  - Figures: `convex_quadratic_convergence.png`, `rosenbrock_convergence.png`, `saddle_escape.png`, `gauss_newton_comparison.png`, `mlp_backprop_training.png`, `lr_sensitivity.png`.

### 2.2 Track B: Discrete Optimization
- **Problem Formulations**:
  - **0-1 Knapsack Problem**: Combinatorial maximization of $\sum_{i=1}^n v_i x_i$ subject to capacity constraint $\sum_{i=1}^n w_i x_i \le W$ with binary variables $x_i \in \{0, 1\}$.
  - **Max-Cut Problem**: Graph partitioning maximizing cut edge weights $\sum_{i < j} w_{ij} (x_i + x_j - 2 x_i x_j)$.
  - **QUBO (Quadratic Unconstrained Binary Optimization)**: Formulates Max-Cut as minimization $\min x^T Q x$, where $Q_{ii} = -\sum_j w_{ij}$ and $Q_{ij} = w_{ij}$.
  - **Ising Spin Model Formulation**: Exact binary-to-spin substitution $s_i = 1 - 2x_i \in \{-1, +1\}$. Energy Hamiltonian $H(s) = \sum_{i<j} \frac{w_{ij}}{2} s_i s_j - \frac{1}{2} \sum_{i<j} w_{ij}$. Ground-state energy corresponds directly to the maximum cut: $\min H(s) = - \max \text{Cut}(x)$.
  - **Penalty Terms for Constraints**: Penalty formulation $P \cdot \max(0, w^T x - W)^2$ converting constrained discrete problems into QUBOs.
- **Algorithms Evaluated**:
  - **Greedy Heuristic**: Value-to-weight density sorting $O(n \log n)$; Sahni-Gonzales local search for Max-Cut.
  - **Dynamic Programming (DP)**: Exact Bellman table recursion $O(n W)$.
  - **Branch and Bound (B&B)**: DFS tree search with greedy continuous linear relaxation fractional upper bounds and bounding pruning.
  - **Integer Linear Programming (ILP)**: SciPy HiGHS branch-and-cut solver (`milp`).
  - **Simulated Annealing (SA)**: Thermal stochastic local search for QUBO minimization.
  - **Exact Classical Ground-State Solver**: Exhaustive state enumeration for classical baseline verification.
- **Key Empirical Findings**:
  - **Knapsack Exactness & Runtime**: On a 15-item instance, DP ($1.89$ ms), Branch and Bound ($0.64$ ms), and ILP ($22.7$ ms) all found the exact global optimum of $549.0$. Greedy density heuristic achieved the exact optimum with zero optimality gap in $0.27$ ms.
  - **Scalability vs. $N$**: Greedy and DP scaled smoothly ($< 2$ ms up to $N=100$), whereas unpruned Branch-and-Bound exhibits combinatorial explosion ($O(2^n)$ in worst-case instances). ILP (HiGHS) demonstrated robust industrial-scale branch-and-cut performance across all problem sizes ($< 25$ ms).
  - **Max-Cut Classical Baseline for Track C**: On an 8-node complete weighted graph, the Exact Classical Ground State achieved maximum cut $101.0$ (Ising ground state energy $-101.0$) in $22.1$ ms with spin configuration $[+1, -1, -1, -1, +1, +1, -1, +1]$. Simulated Annealing on QUBO found the exact optimal cut ($101.0$, $0.0\%$ gap), while Greedy local search found cut $82.0$ ($18.8\%$ gap).
  - **QUBO Penalty Multiplier Dynamics**: When penalty multiplier $P < 2.5$, the capacity constraint was violated (excess weight up to $+19$). At $P \ge 2.5$ ($\ge \max_i v_i / w_i$), constraint violations dropped to zero, validating the theoretical penalty threshold.
- **Artifacts Generated**:
  - Tables: `knapsack_methods_comparison.csv`, `scalability_benchmark.csv`, `maxcut_qubo_ising_baseline.csv`, `qubo_penalty_tuning.csv`.
  - Figures: `knapsack_methods_comparison.png`, `scalability_runtime.png`, `maxcut_classical_baseline.png`, `qubo_penalty_tuning.png`.
  - Stored Matrices for Track C: `track_b_maxcut_W.npy` (adjacency matrix), `track_b_maxcut_Q.npy` (QUBO matrix).

### 2.3 Track C: Quantum Optimization
- **Problem Formulations & Hamiltonians**:
  - **Max-Cut Ising Mapping**: Evaluated on the 8-node weighted graph directly imported from Track B (`track_b_maxcut_W.npy`). Hamiltonian: $H_C = \sum_{i < j} \frac{w_{ij}}{2} Z_i Z_j$, offset $C = -\frac{1}{2} \sum_{i<j} w_{ij}$.
  - **QAOA Circuit Architecture**: Layered unitary evolution $|\psi(\gamma, \beta)\rangle = \prod_{l=1}^p e^{-i \beta_l H_M} e^{-i \gamma_l H_C} |+\rangle^{\otimes n}$ where transverse-field mixer $H_M = \sum X_i$ is implemented via $R_x(2\beta)$ rotations.
  - **VQE Architecture**: Hardware-efficient parameterized quantum circuit (RealAmplitudes RY-CX ladder) minimizing ground-state energy expectation $\langle\psi(\theta)| H |\psi(\theta)\rangle$.
  - **Quantum Gradient Formulations**:
    - Parameter-Shift Rule: Exact analytic gradient $\frac{\partial \langle H \rangle}{\partial \theta_i} = \frac{\langle H(\theta + \frac{\pi}{2} e_i)\rangle - \langle H(\theta - \frac{\pi}{2} e_i)\rangle}{2}$ evaluated in $2d$ circuit queries.
    - SPSA: 2-query simultaneous stochastic perturbation gradient $\hat{g}_k = \frac{\langle H(\theta + c_k \Delta) \rangle - \langle H(\theta - c_k \Delta) \rangle}{2 c_k \Delta}$.
    - Quantum Natural Gradient (QNG): Preconditioned update $\Delta \theta = - G(\theta)^{-1} \nabla \langle H \rangle$ where $G(\theta)$ is the Riemannian Fubini-Study / Quantum Fisher Information metric tensor.
- **Key Empirical Findings**:
  - **QAOA vs. Classical Exact Optimum**: Classical branch-and-bound / exact ground-state solver from Track B identified maximum cut $101.0$ (Ising energy $-101.0$) in $22.1$ ms. QAOA ($p=1$) achieved a cut of $93.0$ (approximation ratio $0.921$) in $1295$ ms. Increasing depth to $p=2$ achieved final energy $-77.17$ in $2307$ ms.
  - **VQE Exact Ground State**: VQE converged to exact ground energy $-6.0000$ ($0.0000$ absolute error) matching full exact matrix diagonalization.
  - **Gradient Strategies Comparison**: Parameter-shift required 12 circuit evaluations ($27.1$ ms) with gradient norm $0.4888$. SPSA required only 2 evaluations ($5.2$ ms) with gradient norm $0.0846$. QNG required 18 evaluations ($13.4$ ms) with natural gradient norm $5.2219$.
  - **Finite Shots and Hardware Depolarizing Noise**: Under zero noise, approximation ratio reached $0.891$ with 128/512 shots. Under $5\%$ depolarizing noise, approximation ratio degraded to $0.762$–$0.832$; under $15\%$ noise, quality dropped to $0.772$–$0.802$.
  - **Barren Plateau Phenomenon**: Random parameterized quantum circuit gradient variance decayed exponentially from $0.1658$ at $N=2$ qubits down to $0.0391$ at $N=10$ qubits ($\log_{10} \text{Var}$ decreased from $-0.78$ to $-1.41$), directly confirming McClean et al.'s theoretical vanishing gradient scaling.
- **Artifacts Generated**:
  - Tables: `qaoa_vs_classical_benchmark.csv`, `vqe_ground_state_results.csv`, `quantum_gradient_strategies.csv`, `noise_and_shots_benchmark.csv`, `barren_plateau_scaling.csv`.
  - Figures: `qaoa_vs_classical.png`, `noise_and_shots_scaling.png`, `barren_plateau_variance.png`.

### 2.4 Track D
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

### 2.5 Track E (Smart University Course Timetable Optimization)
- Problem definition & formulation (Faculty, rooms, timeslots, cohorts, hard & soft constraints)
- Algorithmic approaches: Greedy heuristic vs. Integer Linear Programming (ILP)
- Feasibility, hard violations, soft penalty score, room utilization, and runtime

### 2.6 Track F
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

### 2.7 Track G
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

### 2.8 Track H
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

### 2.9 Track I
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

### 2.10 Track J
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

---

## 3. Comparative Analysis & Benchmark Results
*Benchmark tables, convergence plots, and Pareto frontiers across tracks.*

---

## 4. Limitations & Challenges

---

## 5. Conclusions & Future Work

