# Track A Prompt Record: Continuous Optimization

- **Track**: Track A (Continuous Optimization)
- **Date**: 2026-10-28
- **AI Tool**: Gemini (Antigravity Assistant)
- **Kind of Work**: Requirements extraction, algorithm implementation, test suite generation, benchmarking, visualization, and documentation.

## User Prompt Excerpt:
> Implement **Track A: Continuous Optimization** in the existing `track A/` folder of my Optimization Techniques assignment.
> 1. Inspect before coding: Read the assignment PDF and existing `CHECKLIST.md`. Identify compulsory Track A algorithms, mathematical requirements, experiments, and deliverables.
> 2. Implement the optimization algorithms: Gradient Descent, SGD, Mini-batch SGD, Momentum, Nesterov Accelerated Gradient (NAG), AdaGrad, RMSProp, Adam, and second-order methods (Newton's Method, Gauss-Newton, curvature approximations). Also backpropagation on a small ML model.
> 3. Objective functions: Convex (Quadratic), Non-convex (Rosenbrock / Saddle point / Local minima).
> 4. Controlled experiments: Compare convergence, final loss, distance to optimum, runtime, sensitivity to learning rate.
> 5. Results & Visualizations: Save outputs/plots under `results/track_a/`.
> 6. Code structure & tests: Algorithms, objectives, runner, pytest suite, track README.
> 7. Updates: CHECKLIST.md, README.md, requirements.txt, failure_log.md.

## Execution Plan & Verification Notes:
- Formulate continuous test landscapes:
  1. Strongly Convex Quadratic: $f(x) = \frac{1}{2} x^T Q x - b^T x$.
  2. Non-Convex Rosenbrock Valley: $f(x_1, x_2) = (1 - x_1)^2 + 100(x_2 - x_1^2)^2$.
  3. Non-Convex Saddle Point function: $f(x_1, x_2) = x_1^2 - x_2^2 + 0.1 x_2^4$ (demonstrating escape dynamics).
  4. Small ML Model (Multi-layer Perceptron / Logistic Regression) with Backpropagation distinct from optimizer.
- Implement shared optimizer interface: `Optimizer.step(params, grads, ...)` and full iterative trajectory logging.
- Second-order and curvature methods:
  - Exact Newton's Method (Hessian inversion with damping/regularization).
  - Gauss-Newton for non-linear least squares.
  - Curvature approximations: Diagonal Fisher / low-rank approximation and Hessian-Vector Products (HVP).
- Run benchmarks, generate plots and CSV tables in `results/track_a/`.
- Validate with full pytest suite.

