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

