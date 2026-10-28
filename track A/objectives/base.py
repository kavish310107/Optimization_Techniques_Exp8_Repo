"""Base objective function class."""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np


class ObjectiveFunction(ABC):
    """Abstract base class for scalar objective functions."""

    def __init__(self, name: str, dim: int, optimum: Optional[np.ndarray] = None, opt_val: Optional[float] = None):
        self.name = name
        self.dim = dim
        self.optimum = optimum
        self.opt_val = opt_val

    @abstractmethod
    def evaluate(self, x: np.ndarray) -> float:
        """Compute scalar objective value f(x)."""
        pass

    @abstractmethod
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Compute analytic gradient nabla f(x)."""
        pass

    def hessian(self, x: np.ndarray) -> np.ndarray:
        """Compute analytic Hessian matrix nabla^2 f(x) if available."""
        raise NotImplementedError(f"Hessian not implemented for {self.name}")

    def distance_to_optimum(self, x: np.ndarray) -> Optional[float]:
        """Compute Euclidean distance ||x - x*|| if optimum is known."""
        if self.optimum is not None:
            return float(np.linalg.norm(x - self.optimum))
        return None

