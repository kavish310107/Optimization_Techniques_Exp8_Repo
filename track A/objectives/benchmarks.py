"""Standard benchmark objectives covering:
- Strongly convex quadratic function
- Non-convex Rosenbrock valley
- Non-convex Saddle-Point function (escape dynamics)
- Non-linear least squares problem (for Gauss-Newton)
"""
from typing import Tuple, Optional
import numpy as np
from .base import ObjectiveFunction


class ConvexQuadratic(ObjectiveFunction):
    """Convex Quadratic Objective:
        f(x) = 0.5 * x^T Q x - b^T x + c
        
    Gradient:
        nabla f(x) = Q x - b
        
    Hessian:
        nabla^2 f(x) = Q
        
    Analytic Global Minimum:
        x* = Q^{-1} b
        f(x*) = -0.5 * b^T Q^{-1} b + c
    """
    def __init__(self, Q: Optional[np.ndarray] = None, b: Optional[np.ndarray] = None, c: float = 0.0):
        if Q is None:
            # Default well-conditioned 2D ellipse with condition number 10
            Q = np.array([[10.0, 0.0], [0.0, 1.0]], dtype=float)
        if b is None:
            b = np.array([2.0, -1.0], dtype=float)
        
        dim = len(b)
        # Verify symmetry and positive definiteness
        if not np.allclose(Q, Q.T):
            Q = 0.5 * (Q + Q.T)
        eigvals = np.linalg.eigvalsh(Q)
        if np.any(eigvals <= 0):
            raise ValueError(f"Matrix Q must be strictly positive definite; min eigenvalue: {eigvals.min()}")

        self.Q = Q
        self.b = b
        self.c = float(c)
        x_star = np.linalg.solve(Q, b)
        f_star = float(0.5 * x_star.T @ Q @ x_star - b.T @ x_star + c)
        super().__init__(name="ConvexQuadratic", dim=dim, optimum=x_star, opt_val=f_star)

    def evaluate(self, x: np.ndarray) -> float:
        return float(0.5 * x.T @ self.Q @ x - self.b.T @ x + self.c)

    def gradient(self, x: np.ndarray) -> np.ndarray:
        return self.Q @ x - self.b

    def hessian(self, x: np.ndarray) -> np.ndarray:
        return self.Q.copy()


class Rosenbrock(ObjectiveFunction):
    """Rosenbrock Valley Function (Non-Convex):
        f(x, y) = (a - x)^2 + b * (y - x^2)^2
        Default: a = 1.0, b = 100.0
        
    Global Minimum:
        (x*, y*) = (1, 1), f(x*, y*) = 0.0
        
    Characteristics:
        Has a narrow parabolic banana valley; first-order methods oscillate heavily across valley walls.
    """
    def __init__(self, a: float = 1.0, b: float = 100.0):
        self.a = float(a)
        self.b = float(b)
        super().__init__(name="Rosenbrock", dim=2, optimum=np.array([a, a**2], dtype=float), opt_val=0.0)

    def evaluate(self, x: np.ndarray) -> float:
        x1, x2 = x[0], x[1]
        return float((self.a - x1)**2 + self.b * (x2 - x1**2)**2)

    def gradient(self, x: np.ndarray) -> np.ndarray:
        x1, x2 = x[0], x[1]
        df_dx1 = -2.0 * (self.a - x1) - 4.0 * self.b * x1 * (x2 - x1**2)
        df_dx2 = 2.0 * self.b * (x2 - x1**2)
        return np.array([df_dx1, df_dx2], dtype=float)

    def hessian(self, x: np.ndarray) -> np.ndarray:
        x1, x2 = x[0], x[1]
        d2f_dx12 = 2.0 - 4.0 * self.b * x2 + 12.0 * self.b * (x1**2)
        d2f_dx1dx2 = -4.0 * self.b * x1
        d2f_dx22 = 2.0 * self.b
        return np.array([[d2f_dx12, d2f_dx1dx2], [d2f_dx1dx2, d2f_dx22]], dtype=float)


class SaddleFunction(ObjectiveFunction):
    """Non-convex landscape with a strict saddle point at origin:
        f(x, y) = 0.5 * x^2 - 0.5 * y^2 + 0.1 * y^4
        
    At (0, 0):
        nabla f(0, 0) = [0, 0]
        Hessian = diag([1, -1]) -> indefinite eigenvalues (+1, -1) -> strict saddle point!
        
    Minima:
        Global minima at (0, +-sqrt(5/2)) approx (0, +-1.5811), where f* = -0.625
    """
    def __init__(self):
        # Two symmetric global minima: (0, 1.58113883) and (0, -1.58113883)
        y_min = np.sqrt(0.5 / 0.2)
        super().__init__(name="SaddleLandscape", dim=2, optimum=np.array([0.0, y_min]), opt_val=-0.625)

    def evaluate(self, x: np.ndarray) -> float:
        x1, x2 = x[0], x[1]
        return float(0.5 * x1**2 - 0.5 * x2**2 + 0.1 * x2**4)

    def gradient(self, x: np.ndarray) -> np.ndarray:
        x1, x2 = x[0], x[1]
        df_dx1 = x1
        df_dx2 = -x2 + 0.4 * (x2**3)
        return np.array([df_dx1, df_dx2], dtype=float)

    def hessian(self, x: np.ndarray) -> np.ndarray:
        x1, x2 = x[0], x[1]
        return np.array([[1.0, 0.0], [0.0, -1.0 + 1.2 * (x2**2)]], dtype=float)


class NonLinearLeastSquares(ObjectiveFunction):
    """Non-linear least squares fit to exponential decay curve:
        Model: y_hat(t; theta) = theta_0 * exp(-theta_1 * t)
        Residuals: r_i(theta) = y_hat(t_i; theta) - y_i
        Objective: f(theta) = 0.5 * sum_i r_i(theta)^2
    """
    def __init__(self, t_data: Optional[np.ndarray] = None, y_data: Optional[np.ndarray] = None):
        if t_data is None or y_data is None:
            # Synthetic ground truth: theta* = [2.5, 1.2]
            rng = np.random.RandomState(42)
            t_data = np.linspace(0.1, 2.5, 30)
            y_data = 2.5 * np.exp(-1.2 * t_data) + rng.normal(0, 0.02, size=len(t_data))

        self.t_data = t_data
        self.y_data = y_data
        super().__init__(name="NonLinearLeastSquares", dim=2, optimum=np.array([2.5, 1.2]))

    def residuals(self, theta: np.ndarray) -> np.ndarray:
        """Vector of residuals r(theta)."""
        theta_0, theta_1 = theta[0], theta[1]
        pred = theta_0 * np.exp(-theta_1 * self.t_data)
        return pred - self.y_data

    def jacobian(self, theta: np.ndarray) -> np.ndarray:
        """Jacobian matrix J_ij = partial r_i / partial theta_j."""
        theta_0, theta_1 = theta[0], theta[1]
        exp_term = np.exp(-theta_1 * self.t_data)
        dr_dtheta0 = exp_term
        dr_dtheta1 = -theta_0 * self.t_data * exp_term
        return np.column_stack([dr_dtheta0, dr_dtheta1])

    def evaluate(self, theta: np.ndarray) -> float:
        r = self.residuals(theta)
        return float(0.5 * np.sum(r**2))

    def gradient(self, theta: np.ndarray) -> np.ndarray:
        r = self.residuals(theta)
        J = self.jacobian(theta)
        return J.T @ r

    def hessian(self, theta: np.ndarray) -> np.ndarray:
        # Gauss-Newton approximation of Hessian: J^T J
        J = self.jacobian(theta)
        return J.T @ J

