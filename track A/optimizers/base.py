"""Base optimizer interface and trajectory logger."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np


class Optimizer(ABC):
    """Abstract base class for all first-order and second-order continuous optimizers."""

    def __init__(self, lr: float = 0.01, name: str = "Optimizer"):
        if lr <= 0:
            raise ValueError(f"Learning rate must be positive, got {lr}")
        self.lr = float(lr)
        self.name = name
        self.t = 0  # iteration step counter

    def reset(self):
        """Reset internal optimizer state/buffers."""
        self.t = 0

    @abstractmethod
    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        """Perform a single parameter update step.

        Args:
            params: Current parameter vector (1D or 2D ndarray).
            grad: Current gradient vector of objective w.r.t params.
            kwargs: Optional additional curvature info (Hessian, Jacobian, etc.)

        Returns:
            Updated parameter vector.
        """
        pass

