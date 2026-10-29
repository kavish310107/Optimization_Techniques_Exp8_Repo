"""Multi-Task Optimization Module:
- Problem: Simultaneous optimization of two conflicting task losses:
    min_{theta} [ L_1(theta), L_2(theta) ]
- Algorithms:
    1. Equal Task Weighting (Baseline): L_total = 0.5 * L_1 + 0.5 * L_2
    2. MGDA (Multiple Gradient Descent Algorithm - Desideri 2012 / Sener & Koltun 2018):
       Finds Pareto-stationary direction by solving the min-norm point in the convex hull of task gradients:
       min_{alpha_1 + alpha_2 = 1, alpha_i >= 0} || alpha_1 g_1 + alpha_2 g_2 ||^2
    3. GradNorm (Chen et al. 2018):
       Dynamically balances gradient magnitudes based on relative inverse training rates.
"""
from typing import Dict, Any, List, Tuple
import numpy as np


class TwoTaskModel:
    """Multi-task learning setup on shared parameters theta with two synthetic conflicting tasks.
    
    Task 1: Minimize L_1(theta) = 0.5 * ||A_1 theta - y_1||^2  (Regression Task 1)
    Task 2: Minimize L_2(theta) = 0.5 * ||A_2 theta - y_2||^2  (Regression Task 2)
    where Task 1 and Task 2 have conflicting optimal parameter vectors theta_1^* != theta_2^*.
    """

    def __init__(self, dim: int = 15, num_samples: int = 200, seed: int = 42):
        rng = np.random.RandomState(seed)
        self.dim = dim
        self.A1 = rng.randn(num_samples, dim)
        self.A2 = rng.randn(num_samples, dim)

        # Conflicting target parameter directions
        theta1_true = np.ones(dim)
        theta2_true = -np.ones(dim)

        self.y1 = np.dot(self.A1, theta1_true) + rng.normal(0, 0.1, size=num_samples)
        self.y2 = np.dot(self.A2, theta2_true) + rng.normal(0, 0.1, size=num_samples)

    def evaluate_losses_and_gradients(self, theta: np.ndarray) -> Tuple[float, float, np.ndarray, np.ndarray]:
        """Compute task losses and analytical gradients."""
        r1 = np.dot(self.A1, theta) - self.y1
        L1 = 0.5 * float(np.mean(r1 ** 2))
        g1 = np.dot(self.A1.T, r1) / len(r1)

        r2 = np.dot(self.A2, theta) - self.y2
        L2 = 0.5 * float(np.mean(r2 ** 2))
        g2 = np.dot(self.A2.T, r2) / len(r2)

        return L1, L2, g1, g2


def solve_mgda_2task(g1: np.ndarray, g2: np.ndarray) -> Tuple[float, float, np.ndarray]:
    """Analytical solution for MGDA minimum-norm gradient in 2-task setting:
        min_{alpha in [0, 1]} || alpha g1 + (1 - alpha) g2 ||^2
    
    Derivation:
        f(alpha) = alpha^2 ||g1||^2 + (1-alpha)^2 ||g2||^2 + 2 alpha (1-alpha) g1^T g2
        df/dalpha = 2 alpha ||g1||^2 - 2 (1-alpha) ||g2||^2 + 2 (1 - 2 alpha) g1^T g2 = 0
        alpha* = (||g2||^2 - g1^T g2) / (||g1 - g2||^2)
    Clipped to [0, 1].
    """
    diff = g1 - g2
    denom = np.dot(diff, diff)

    if denom < 1e-12:
        alpha = 0.5
    else:
        num = np.dot(g2, g2) - np.dot(g1, g2)
        alpha = float(num / denom)
        alpha = max(0.0, min(1.0, alpha))

    combined_grad = alpha * g1 + (1.0 - alpha) * g2
    return alpha, 1.0 - alpha, combined_grad


def run_equal_weighting_optimization(model: TwoTaskModel, steps: int = 100, lr: float = 0.05) -> Dict[str, Any]:
    """Baseline: equal fixed weights (alpha_1 = 0.5, alpha_2 = 0.5)."""
    theta = np.zeros(model.dim, dtype=float)
    hist_L1, hist_L2 = [], []

    for _ in range(steps):
        L1, L2, g1, g2 = model.evaluate_losses_and_gradients(theta)
        hist_L1.append(L1)
        hist_L2.append(L2)
        combined_grad = 0.5 * g1 + 0.5 * g2
        theta -= lr * combined_grad

    final_L1, final_L2, _, _ = model.evaluate_losses_and_gradients(theta)
    return {
        "final_L1": final_L1,
        "final_L2": final_L2,
        "hist_L1": hist_L1,
        "hist_L2": hist_L2,
        "theta": theta,
    }


def run_mgda_optimization(model: TwoTaskModel, steps: int = 100, lr: float = 0.05) -> Dict[str, Any]:
    """MGDA optimization dynamically balancing Pareto gradients."""
    theta = np.zeros(model.dim, dtype=float)
    hist_L1, hist_L2, hist_alphas = [], [], []

    for _ in range(steps):
        L1, L2, g1, g2 = model.evaluate_losses_and_gradients(theta)
        hist_L1.append(L1)
        hist_L2.append(L2)
        a1, a2, mgda_grad = solve_mgda_2task(g1, g2)
        hist_alphas.append((a1, a2))
        theta -= lr * mgda_grad

    final_L1, final_L2, _, _ = model.evaluate_losses_and_gradients(theta)
    return {
        "final_L1": final_L1,
        "final_L2": final_L2,
        "hist_L1": hist_L1,
        "hist_L2": hist_L2,
        "hist_alphas": hist_alphas,
        "theta": theta,
    }


def run_gradnorm_optimization(model: TwoTaskModel, steps: int = 100, lr: float = 0.05, alpha_param: float = 0.15) -> Dict[str, Any]:
    """GradNorm balancing task gradient norms according to training loss ratios."""
    theta = np.zeros(model.dim, dtype=float)
    weights = np.array([1.0, 1.0], dtype=float)
    hist_L1, hist_L2 = [], []

    # Initial losses L(0)
    L1_init, L2_init, _, _ = model.evaluate_losses_and_gradients(theta)

    for step in range(steps):
        L1, L2, g1, g2 = model.evaluate_losses_and_gradients(theta)
        hist_L1.append(L1)
        hist_L2.append(L2)

        # Gradient norms
        G1_norm = np.linalg.norm(weights[0] * g1)
        G2_norm = np.linalg.norm(weights[1] * g2)
        G_avg = 0.5 * (G1_norm + G2_norm)

        # Relative inverse training rate r_i(t) = (L_i(t) / L_i(0)) / mean_j(L_j(t) / L_j(0))
        loss_ratio1 = L1 / max(L1_init, 1e-9)
        loss_ratio2 = L2 / max(L2_init, 1e-9)
        mean_ratio = 0.5 * (loss_ratio1 + loss_ratio2)

        r1 = loss_ratio1 / max(mean_ratio, 1e-9)
        r2 = loss_ratio2 / max(mean_ratio, 1e-9)

        # Target norms: G_avg * [r_i]^alpha
        target1 = G_avg * (r1 ** alpha_param)
        target2 = G_avg * (r2 ** alpha_param)

        # Update weights proportionally
        grad_w1 = abs(G1_norm - target1)
        grad_w2 = abs(G2_norm - target2)

        weights[0] -= 0.02 * (G1_norm - target1)
        weights[1] -= 0.02 * (G2_norm - target2)
        # Renormalize weights sum to 2
        weights = np.maximum(0.1, weights)
        weights = 2.0 * weights / np.sum(weights)

        combined_grad = 0.5 * (weights[0] * g1 + weights[1] * g2)
        theta -= lr * combined_grad

    final_L1, final_L2, _, _ = model.evaluate_losses_and_gradients(theta)
    return {
        "final_L1": final_L1,
        "final_L2": final_L2,
        "hist_L1": hist_L1,
        "hist_L2": hist_L2,
        "theta": theta,
    }

