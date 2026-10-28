"""Small ML Model demonstrating Backpropagation (distinct from the optimizer).

Implements a 2-layer Multi-Layer Perceptron (MLP) for binary classification:
    Input x (d_in) -> Linear -> ReLU -> Linear -> Sigmoid -> Binary Cross-Entropy Loss

Explicitly separates:
    1. Forward propagation (activations, predictions, loss)
    2. Backward propagation (chain-rule analytical gradients w.r.t weights and biases)
    3. Parameter update (delegated to any Track A Optimizer)
"""
from typing import Tuple, Dict
import numpy as np


class TwoLayerMLP:
    """Two-layer fully-connected neural network for binary classification."""

    def __init__(self, input_dim: int, hidden_dim: int, seed: int = 42):
        rng = np.random.RandomState(seed)
        # He initialization for ReLU hidden layer
        self.W1 = rng.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros((1, hidden_dim))
        # Xavier initialization for Sigmoid output layer
        self.W2 = rng.randn(hidden_dim, 1) * np.sqrt(1.0 / hidden_dim)
        self.b2 = np.zeros((1, 1))

        # Cached intermediate activations for backprop
        self.cache: Dict[str, np.ndarray] = {}

    @property
    def params_flat(self) -> np.ndarray:
        """Flatten all parameters into a single 1D vector."""
        return np.concatenate([
            self.W1.ravel(),
            self.b1.ravel(),
            self.W2.ravel(),
            self.b2.ravel(),
        ])

    def set_params_flat(self, theta: np.ndarray):
        """Unpack flattened 1D parameter vector back into layer weights and biases."""
        idx = 0
        w1_size = self.W1.size
        self.W1 = theta[idx:idx + w1_size].reshape(self.W1.shape)
        idx += w1_size

        b1_size = self.b1.size
        self.b1 = theta[idx:idx + b1_size].reshape(self.b1.shape)
        idx += b1_size

        w2_size = self.W2.size
        self.W2 = theta[idx:idx + w2_size].reshape(self.W2.shape)
        idx += w2_size

        b2_size = self.b2.size
        self.b2 = theta[idx:idx + b2_size].reshape(self.b2.shape)

    @staticmethod
    def relu(z: np.ndarray) -> np.ndarray:
        return np.maximum(0.0, z)

    @staticmethod
    def sigmoid(z: np.ndarray) -> np.ndarray:
        # Numerically stable sigmoid
        z_clipped = np.clip(z, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(-z_clipped))

    def forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass.
        
        Args:
            X: Input matrix of shape (N, input_dim)
        Returns:
            y_pred: Predicted probabilities of shape (N, 1)
        """
        Z1 = X @ self.W1 + self.b1
        A1 = self.relu(Z1)
        Z2 = A1 @ self.W2 + self.b2
        A2 = self.sigmoid(Z2)

        self.cache = {
            "X": X,
            "Z1": Z1,
            "A1": A1,
            "Z2": Z2,
            "A2": A2,
        }
        return A2

    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray, eps: float = 1e-12) -> float:
        """Binary cross-entropy loss:
            L = - (1/N) * sum [ y * log(p) + (1-y) * log(1-p) ]
        """
        N = len(y_true)
        p = np.clip(y_pred, eps, 1.0 - eps)
        loss = -np.mean(y_true * np.log(p) + (1.0 - y_true) * np.log(1.0 - p))
        return float(loss)

    def backpropagation(self, y_true: np.ndarray) -> np.ndarray:
        """Backpropagation step: analytical gradients via chain rule.
        
        Computes:
            dL / dZ2 = A2 - y
            dL / dW2 = A1^T (dL / dZ2) / N
            dL / db2 = mean(dL / dZ2, axis=0)
            dL / dA1 = (dL / dZ2) W2^T
            dL / dZ1 = dL / dA1 * (Z1 > 0)
            dL / dW1 = X^T (dL / dZ1) / N
            dL / db1 = mean(dL / dZ1, axis=0)

        Returns:
            Flattened gradient vector matching `params_flat`.
        """
        X = self.cache["X"]
        A1 = self.cache["A1"]
        Z1 = self.cache["Z1"]
        A2 = self.cache["A2"]
        N = len(y_true)

        # Gradient of BCE loss w.r.t logits Z2
        dZ2 = (A2 - y_true) / N
        dW2 = A1.T @ dZ2
        db2 = np.sum(dZ2, axis=0, keepdims=True)

        # Backprop through ReLU
        dA1 = dZ2 @ self.W2.T
        dZ1 = dA1 * (Z1 > 0.0)

        dW1 = X.T @ dZ1
        db1 = np.sum(dZ1, axis=0, keepdims=True)

        grads_flat = np.concatenate([
            dW1.ravel(),
            db1.ravel(),
            dW2.ravel(),
            db2.ravel(),
        ])
        return grads_flat

