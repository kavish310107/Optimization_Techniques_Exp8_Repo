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

### 2.3 Track C
- Problem definition & formulation
- Algorithmic approaches
- Empirical setup & evaluation metrics

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

