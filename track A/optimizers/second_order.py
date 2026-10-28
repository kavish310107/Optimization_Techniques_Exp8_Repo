"""Second-order and curvature-based optimization methods:
- Damped Newton's Method
- Gauss-Newton Method (for non-linear least squares)
- Curvature Approximations:
    - Diagonal Fisher / Low-rank approximation
    - Hessian-Vector Product (Pearlmutter / finite-difference formulation)
"""
from typing import Optional, Callable
import numpy as np
from .base import Optimizer


class NewtonsMethod(Optimizer):
    """Classical Newton-Raphson optimization with Levenberg-Marquardt damping.
    
    Update step:
        delta = - (H + damping * I)^{-1} * grad
        theta_{t+1} = theta_t + lr * delta
    """
    def __init__(self, lr: float = 1.0, damping: float = 1e-4):
        super().__init__(lr=lr, name="Newton")
        self.damping = float(damping)

    def step(self, params: np.ndarray, grad: np.ndarray, hessian: Optional[np.ndarray] = None, **kwargs) -> np.ndarray:
        self.t += 1
        if hessian is None:
            raise ValueError("Newton's Method requires 'hessian' in step() kwargs.")

        d = len(params)
        # Regularized Hessian to guarantee positive definiteness / invertibility
        H_reg = hessian + self.damping * np.eye(d)

        try:
            # Solve (H_reg) * delta = -grad
            delta = np.linalg.solve(H_reg, -grad)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse if singular
            delta = -np.linalg.pinv(H_reg) @ grad

        return params + self.lr * delta


class GaussNewton(Optimizer):
    """Gauss-Newton method for Non-Linear Least Squares.
    
    Minimizes:
        f(theta) = 0.5 * sum_i r_i(theta)^2 = 0.5 * ||r(theta)||^2
    
    Approximates Hessian as:
        H_GN = J^T J
    
    Update:
        delta = - (J^T J + damping * I)^{-1} J^T r
        theta_{t+1} = theta_t + lr * delta
    """
    def __init__(self, lr: float = 1.0, damping: float = 1e-4):
        super().__init__(lr=lr, name="GaussNewton")
        self.damping = float(damping)

    def step(self, params: np.ndarray, grad: Optional[np.ndarray] = None,
             residuals: Optional[np.ndarray] = None,
             jacobian: Optional[np.ndarray] = None, **kwargs) -> np.ndarray:
        self.t += 1
        if residuals is None or jacobian is None:
            raise ValueError("GaussNewton requires 'residuals' and 'jacobian' in step() kwargs.")

        # J is (m, n), residuals is (m,)
        J = jacobian
        r = residuals
        n_params = len(params)

        JT_J = J.T @ J
        JT_r = J.T @ r

        H_reg = JT_J + self.damping * np.eye(n_params)
        try:
            delta = np.linalg.solve(H_reg, -JT_r)
        except np.linalg.LinAlgError:
            delta = -np.linalg.pinv(H_reg) @ JT_r

        return params + self.lr * delta


class DiagonalFisherOptimizer(Optimizer):
    """Natural gradient / curvature descent using a running diagonal empirical Fisher approximation.
    
    F_diag = E[ (grad_i)^2 ]
    theta_{t+1} = theta_t - lr * (F_diag + damping)^{-1} * grad
    """
    def __init__(self, lr: float = 0.01, beta: float = 0.95, damping: float = 1e-3):
        super().__init__(lr=lr, name="DiagFisher")
        self.beta = beta
        self.damping = damping
        self.F_diag = None

    def reset(self):
        super().reset()
        self.F_diag = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        # Empirical Fisher diagonal is estimated from squared gradient
        fisher_sample = grad ** 2
        if self.F_diag is None:
            self.F_diag = fisher_sample
        else:
            self.F_diag = self.beta * self.F_diag + (1.0 - self.beta) * fisher_sample

        preconditioned_grad = grad / (self.F_diag + self.damping)
        return params - self.lr * preconditioned_grad


def hessian_vector_product(grad_func: Callable[[np.ndarray], np.ndarray],
                           x: np.ndarray, v: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Compute Hessian-Vector Product (HVP) H(x) * v using finite differences without forming the full Hessian matrix.
    
    Pearlmutter forward-difference approximation:
        H(x) v approx (grad(x + eps * v) - grad(x - eps * v)) / (2 * eps)
    """
    v_norm = np.linalg.norm(v)
    if v_norm == 0:
        return np.zeros_like(x)
    step_v = eps * (v / v_norm)
    g_plus = grad_func(x + step_v)
    g_minus = grad_func(x - step_v)
    return (g_plus - g_minus) / (2.0 * eps) * v_norm

