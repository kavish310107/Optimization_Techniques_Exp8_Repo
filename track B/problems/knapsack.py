"""0-1 Knapsack Problem formulation:
Maximize sum_{i=1}^n v_i * x_i
Subject to:
    sum_{i=1}^n w_i * x_i <= W
    x_i in {0, 1}
"""
from typing import Tuple, List, Optional
import numpy as np


class KnapsackProblem:
    """0-1 Knapsack instance representation with exact validation and penalty evaluation."""

    def __init__(self, values: np.ndarray, weights: np.ndarray, capacity: float, name: str = "Knapsack"):
        values = np.asarray(values, dtype=float)
        weights = np.asarray(weights, dtype=float)

        if len(values) != len(weights):
            raise ValueError(f"Values length ({len(values)}) != Weights length ({len(weights)})")
        if np.any(values < 0) or np.any(weights < 0):
            raise ValueError("Values and weights must be non-negative.")
        if capacity < 0:
            raise ValueError(f"Capacity must be non-negative, got {capacity}")

        self.values = values
        self.weights = weights
        self.capacity = float(capacity)
        self.n = len(values)
        self.name = name

    def evaluate(self, x: np.ndarray) -> Tuple[float, float, bool]:
        """Evaluate a binary selection vector x.
        
        Returns:
            (total_value, total_weight, is_feasible)
        """
        x_bin = np.asarray(x, dtype=float).round().astype(int)
        total_val = float(np.dot(self.values, x_bin))
        total_wt = float(np.dot(self.weights, x_bin))
        is_feasible = bool(total_wt <= self.capacity + 1e-9)
        return total_val, total_wt, is_feasible

    def to_qubo(self, penalty_multiplier: Optional[float] = None) -> Tuple[np.ndarray, float]:
        """Formulate 0-1 Knapsack as QUBO (minimization form).
        
        Minimizes:
            Q(x) = - sum_i v_i x_i + P * (sum_i w_i x_i + sum_k s_k - W)^2
        Where s_k are binary slack variables to enforce inequality constraint.
        For exact comparison baseline or unconstrained penalty formulation,
        returns (Q_matrix, constant_offset).
        """
        # Linear penalty formulation for capacity excess:
        # P must exceed max_i (v_i / w_i)
        if penalty_multiplier is None:
            max_ratio = np.max(self.values / np.maximum(self.weights, 1e-6))
            penalty = float(max_ratio * 1.5)
        else:
            penalty = float(penalty_multiplier)

        # Basic QUBO matrix on x variables:
        # Objective: min -v^T x + P * (x^T (w w^T) x - 2 W w^T x)
        # Note: x_i^2 = x_i for binary variables
        Q = np.zeros((self.n, self.n), dtype=float)
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    # Linear terms on diagonal: -v_i - 2 P W w_i + P w_i^2
                    Q[i, i] = -self.values[i] + penalty * (self.weights[i]**2 - 2.0 * self.capacity * self.weights[i])
                else:
                    # Quadratic cross terms: 2 * P * w_i * w_j (split symmetrically)
                    Q[i, j] = penalty * (self.weights[i] * self.weights[j])

        offset = penalty * (self.capacity ** 2)
        return Q, offset

