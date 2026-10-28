# Track A: Continuous Optimization

This directory contains the complete modular implementation, mathematical formulations, benchmarks, and validation tests for **Track A: Continuous Optimization**, in accordance with Assignment 8 requirements (Chapter 6 continuous optimization methods).

---

## Architecture & Module Structure

```text
track A/
├── README.md                 # Track documentation and execution instructions
├── optimizers/               # First- and second-order optimization algorithms
│   ├── base.py               # Abstract Optimizer base class with unified interface
│   ├── first_order.py        # GD, Momentum, NAG, AdaGrad, RMSProp, Adam
│   ├── second_order.py       # Newton's Method, Gauss-Newton, Diag-Fisher, HVP
│   └── __init__.py
├── objectives/               # Benchmark objective landscapes & formulations
│   ├── base.py               # ObjectiveFunction base class
│   ├── benchmarks.py         # Convex Quadratic, Rosenbrock, Saddle, Least-Squares
│   └── __init__.py
├── models/                   # Machine learning architectures
│   ├── mlp.py                # TwoLayerMLP with analytical backpropagation
│   └── __init__.py
├── experiments/              # Controlled experimental benchmarks & runners
│   └── runner.py             # Reproducible experiment runner generating results & plots
└── tests/                    # Verification suite
    └── test_track_a.py       # Unit tests (gradients, Hessians, convergence, edge cases)
```

---

## Compulsory Coverage & Mathematical Formulations

### 1. First-Order Gradient Methods
- **Gradient Descent (GD)**: $\theta_{t+1} = \theta_t - \eta \nabla f(\theta_t)$
- **Momentum (Polyak)**: $v_{t+1} = \beta v_t + \eta \nabla f(\theta_t); \quad \theta_{t+1} = \theta_t - v_{t+1}$
- **Nesterov Accelerated Gradient (NAG)**: Lookahead velocity formulation $\theta_{t+1} = \theta_t - (\beta v_{t+1} + \eta \nabla f(\theta_t))$
- **AdaGrad**: $G_{t+1} = G_t + g_t^2; \quad \theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{G_{t+1}} + \epsilon} \odot g_t$
- **RMSProp**: $v_{t+1} = \gamma v_t + (1 - \gamma) g_t^2; \quad \theta_{t+1} = \theta_t - \frac{\eta}{\sqrt{v_{t+1}} + \epsilon} \odot g_t$
- **Adam**: Bias-corrected first ($m_t$) and second ($v_t$) moment tracking.

### 2. Second-Order & Curvature Methods
- **Newton's Method**: $\theta_{t+1} = \theta_t - (\nabla^2 f(\theta_t) + \lambda I)^{-1} \nabla f(\theta_t)$ with Levenberg-Marquardt damping $\lambda$.
- **Gauss-Newton**: Non-linear least squares solver with Hessian approximated as $H_{GN} \approx J^T J$.
- **Empirical Diagonal Fisher**: Natural gradient descent preconditioned by diagonal expected squared score vector $(F_{diag} + \lambda I)^{-1}$.
- **Hessian-Vector Products (HVP)**: Pearlmutter finite-difference formulation $H(x)v \approx \frac{\nabla f(x + \epsilon v) - \nabla f(x - \epsilon v)}{2\epsilon}$ without storing or computing $n \times n$ matrices.

### 3. Backpropagation vs. Optimization
- `TwoLayerMLP` implements analytical matrix calculus chain rule backpropagation for a multi-layer perceptron. The gradient computation (backpropagation) is cleanly separated from parameter updating (delegated to any optimizer).

### 4. Objective Landscapes
- **Convex Quadratic**: $f(x) = \frac{1}{2} x^T Q x - b^T x$ with condition number $\kappa = 10$.
- **Non-Convex Rosenbrock Valley**: $f(x_1, x_2) = (1 - x_1)^2 + 100(x_2 - x_1^2)^2$.
- **Non-Convex Saddle Point**: $f(x_1, x_2) = \frac{1}{2} x_1^2 - \frac{1}{2} x_2^2 + 0.1 x_2^4$ with strict indefinite Hessian $\nabla^2 f(0, 0) = \text{diag}(1, -1)$.

---

## Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track A/tests/test_track_a.py" -v
```

### Run Experiments & Generate Plots
```bash
python "track A/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, and visualization curves are exported to `results/track_a/`.

