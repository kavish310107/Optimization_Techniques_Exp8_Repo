"""First-order gradient-based optimizers:
- Gradient Descent (GD)
- Stochastic / Mini-batch Gradient Descent
- Momentum
- Nesterov Accelerated Gradient (NAG)
- AdaGrad
- RMSProp
- Adam
"""
import numpy as np
from .base import Optimizer


class GradientDescent(Optimizer):
    """Standard Gradient Descent (full-batch / deterministic).
    
    Update rule:
        theta_{t+1} = theta_t - lr * grad
    """
    def __init__(self, lr: float = 0.01):
        super().__init__(lr=lr, name="GD")

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        return params - self.lr * grad


class Momentum(Optimizer):
    """Polyak Classical Momentum.
    
    Update rule:
        v_{t+1} = beta * v_t + lr * grad
        theta_{t+1} = theta_t - v_{t+1}
    """
    def __init__(self, lr: float = 0.01, beta: float = 0.9):
        super().__init__(lr=lr, name="Momentum")
        if not (0.0 <= beta < 1.0):
            raise ValueError(f"beta must be in [0, 1), got {beta}")
        self.beta = beta
        self.v = None

    def reset(self):
        super().reset()
        self.v = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        if self.v is None:
            self.v = np.zeros_like(params)
        self.v = self.beta * self.v + self.lr * grad
        return params - self.v


class NesterovAcceleratedGradient(Optimizer):
    """Nesterov Accelerated Gradient (NAG).
    
    Standard equivalent form:
        v_{t+1} = beta * v_t + lr * grad
        theta_{t+1} = theta_t - (beta * v_{t+1} + lr * grad)
    or commonly implemented via momentum buffer update:
        theta_{t+1} = theta_t - (beta * v_t + lr * grad)
    """
    def __init__(self, lr: float = 0.01, beta: float = 0.9):
        super().__init__(lr=lr, name="NAG")
        if not (0.0 <= beta < 1.0):
            raise ValueError(f"beta must be in [0, 1), got {beta}")
        self.beta = beta
        self.v = None

    def reset(self):
        super().reset()
        self.v = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        if self.v is None:
            self.v = np.zeros_like(params)
        # Nesterov momentum step (Sutskever et al. 2013 formulation)
        self.v = self.beta * self.v + self.lr * grad
        return params - (self.beta * self.v + self.lr * grad)


class AdaGrad(Optimizer):
    """Adaptive Gradient Algorithm (AdaGrad).
    
    Accumulates squared gradients per dimension:
        G_{t+1} = G_t + grad^2
        theta_{t+1} = theta_t - lr / (sqrt(G_{t+1}) + eps) * grad
    """
    def __init__(self, lr: float = 0.1, eps: float = 1e-8):
        super().__init__(lr=lr, name="AdaGrad")
        self.eps = eps
        self.G = None

    def reset(self):
        super().reset()
        self.G = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        if self.G is None:
            self.G = np.zeros_like(params)
        self.G += grad ** 2
        adjusted_grad = grad / (np.sqrt(self.G) + self.eps)
        return params - self.lr * adjusted_grad


class RMSProp(Optimizer):
    """Root Mean Square Propagation (RMSProp).
    
    Exponentially decaying average of squared gradients:
        v_{t+1} = gamma * v_t + (1 - gamma) * grad^2
        theta_{t+1} = theta_t - lr / (sqrt(v_{t+1}) + eps) * grad
    """
    def __init__(self, lr: float = 0.01, gamma: float = 0.9, eps: float = 1e-8):
        super().__init__(lr=lr, name="RMSProp")
        if not (0.0 <= gamma < 1.0):
            raise ValueError(f"gamma must be in [0, 1), got {gamma}")
        self.gamma = gamma
        self.eps = eps
        self.v = None

    def reset(self):
        super().reset()
        self.v = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        if self.v is None:
            self.v = np.zeros_like(params)
        self.v = self.gamma * self.v + (1.0 - self.gamma) * (grad ** 2)
        adjusted_grad = grad / (np.sqrt(self.v) + self.eps)
        return params - self.lr * adjusted_grad


class Adam(Optimizer):
    """Adaptive Moment Estimation (Adam).
    
    First and second moment tracking with bias correction:
        m_t = beta1 * m_{t-1} + (1 - beta1) * grad
        v_t = beta2 * v_{t-1} + (1 - beta2) * grad^2
        m_hat = m_t / (1 - beta1^t)
        v_hat = v_t / (1 - beta2^t)
        theta_{t+1} = theta_t - lr / (sqrt(v_hat) + eps) * m_hat
    """
    def __init__(self, lr: float = 0.01, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        super().__init__(lr=lr, name="Adam")
        if not (0.0 <= beta1 < 1.0):
            raise ValueError(f"beta1 must be in [0, 1), got {beta1}")
        if not (0.0 <= beta2 < 1.0):
            raise ValueError(f"beta2 must be in [0, 1), got {beta2}")
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = None
        self.v = None

    def reset(self):
        super().reset()
        self.m = None
        self.v = None

    def step(self, params: np.ndarray, grad: np.ndarray, **kwargs) -> np.ndarray:
        self.t += 1
        if self.m is None:
            self.m = np.zeros_like(params)
            self.v = np.zeros_like(params)

        self.m = self.beta1 * self.m + (1.0 - self.beta1) * grad
        self.v = self.beta2 * self.v + (1.0 - self.beta2) * (grad ** 2)

        # Bias corrections
        m_hat = self.m / (1.0 - (self.beta1 ** self.t))
        v_hat = self.v / (1.0 - (self.beta2 ** self.t))

        return params - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
