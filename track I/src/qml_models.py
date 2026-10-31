"""
Quantum Machine Learning (QML) vs Classical Classifier implementations.
- Variational Quantum Classifier (VQC) with parameterized Angle Feature Map and RealAmplitudes ansatz.
- Classical Multilayer Perceptron (MLP) and Classical Logistic Regression for rigorous head-to-head benchmarking.
- Noise model simulation for noisy NISQ resilience comparison.
"""

import time
import numpy as np
from typing import Dict, Any, Tuple, List
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit.circuit.library import RealAmplitudes
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class VariationalQuantumClassifier:
    """
    Variational Quantum Classifier (VQC).
    Feature Map: Angle encoding (Ry rotations with scaled features).
    Ansatz: Parameterized Entangling Circuit (Ry + CZ / CX ladder).
    Measurement: Expectation value of Pauli Z on qubit 0, mapped to binary class probability via sigmoid.
    """
    def __init__(self, n_qubits: int = 2, n_layers: int = 2, learning_rate: float = 0.1, max_iter: int = 50, seed: int = 42):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.lr = learning_rate
        self.max_iter = max_iter
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        
        # Total parameters = n_qubits * (n_layers + 1)
        self.n_params = self.n_qubits * (self.n_layers + 1)
        self.params = self.rng.uniform(-0.5, 0.5, size=self.n_params)
        
        # Observable: Z on qubit 0
        pauli_str = "I" * (self.n_qubits - 1) + "Z"
        self.observable = SparsePauliOp.from_list([(pauli_str, 1.0)])
        
        self.training_loss_history: List[float] = []
        self.circuit_evaluations: int = 0
        self.training_time_s: float = 0.0

    def _build_circuit(self, x: np.ndarray, theta: np.ndarray) -> QuantumCircuit:
        """Constructs state preparation (encoding) + parameterized ansatz."""
        qc = QuantumCircuit(self.n_qubits)
        
        # 1. Feature Encoding (Angle Encoding: Ry(x_i))
        for i in range(self.n_qubits):
            val = x[i % len(x)]
            qc.ry(val, i)
            
        # 2. Parameterized Variational Ansatz
        idx = 0
        for l in range(self.n_layers):
            # Rotation layer
            for q in range(self.n_qubits):
                qc.ry(theta[idx], q)
                idx += 1
            # Entanglement layer (linear ladder)
            for q in range(self.n_qubits - 1):
                qc.cx(q, q + 1)
                
        # Final rotation layer
        for q in range(self.n_qubits):
            qc.ry(theta[idx], q)
            idx += 1
            
        return qc

    def _evaluate_expectation(self, x: np.ndarray, theta: np.ndarray, noise_depolarizing: float = 0.0) -> float:
        """Evaluates <psi(x, theta)| Z_0 |psi(x, theta)> using Statevector."""
        self.circuit_evaluations += 1
        qc = self._build_circuit(x, theta)
        sv = Statevector.from_instruction(qc)
        exp_val = sv.expectation_value(self.observable).real
        
        # Apply phenomenological depolarizing noise channel if requested: <O>_noisy = (1 - p)*<O>
        if noise_depolarizing > 0.0:
            exp_val = (1.0 - noise_depolarizing) * exp_val
            
        return float(exp_val)

    def _predict_prob(self, X: np.ndarray, theta: np.ndarray, noise: float = 0.0) -> np.ndarray:
        """Outputs predicted probability P(y=1) = (1 + <Z>) / 2 (or sigmoid)."""
        probs = []
        for x in X:
            exp_val = self._evaluate_expectation(x, theta, noise_depolarizing=noise)
            # Clip between -1 and 1
            exp_val = np.clip(exp_val, -1.0, 1.0)
            p1 = 0.5 * (1.0 + exp_val)
            probs.append(p1)
        return np.array(probs)

    def fit(self, X: np.ndarray, y: np.ndarray, noise_depolarizing: float = 0.0) -> "VariationalQuantumClassifier":
        """Trains the VQC parameters using SPSA / Parameter-Shift gradient descent."""
        t0 = time.perf_counter()
        theta = self.params.copy()
        n_samples = len(X)
        shift = np.pi / 2.0
        
        for iteration in range(self.max_iter):
            # Compute loss
            probs = self._predict_prob(X, theta, noise=noise_depolarizing)
            # Binary cross entropy with numerical stability epsilon
            eps = 1e-9
            probs_clipped = np.clip(probs, eps, 1.0 - eps)
            loss = -np.mean(y * np.log(probs_clipped) + (1.0 - y) * np.log(1.0 - probs_clipped))
            self.training_loss_history.append(float(loss))
            
            # Subsample mini-batch for gradient to ensure fast training
            batch_indices = self.rng.choice(n_samples, size=min(16, n_samples), replace=False)
            grad = np.zeros_like(theta)
            
            # Analytic Parameter-Shift Rule for each variational parameter:
            # d<Z>/d theta_k = (<Z(theta_k + pi/2)> - <Z(theta_k - pi/2)>) / 2
            for k in range(self.n_params):
                theta_plus = theta.copy()
                theta_plus[k] += shift
                theta_minus = theta.copy()
                theta_minus[k] -= shift
                
                grad_k = 0.0
                for idx in batch_indices:
                    x_i = X[idx]
                    y_i = y[idx]
                    
                    e_plus = self._evaluate_expectation(x_i, theta_plus, noise_depolarizing)
                    e_minus = self._evaluate_expectation(x_i, theta_minus, noise_depolarizing)
                    dexp_dtheta = 0.5 * (e_plus - e_minus)
                    
                    p_i = 0.5 * (1.0 + self._evaluate_expectation(x_i, theta, noise_depolarizing))
                    p_i = np.clip(p_i, eps, 1.0 - eps)
                    
                    # Chain rule dLoss/dtheta_k
                    dloss_dp = (p_i - y_i) / (p_i * (1.0 - p_i))
                    dp_dtheta = 0.5 * dexp_dtheta
                    grad_k += dloss_dp * dp_dtheta
                    
                grad[k] = grad_k / len(batch_indices)
                
            # Gradient descent step
            theta = theta - self.lr * np.clip(grad, -1.0, 1.0)
            
        self.params = theta
        self.training_time_s = time.perf_counter() - t0
        return self

    def predict(self, X: np.ndarray, noise: float = 0.0) -> np.ndarray:
        probs = self._predict_prob(X, self.params, noise=noise)
        return (probs >= 0.5).astype(int)


def train_classical_models(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, seed: int = 42) -> Dict[str, Any]:
    """Trains classical baselines (Logistic Regression and Multi-Layer Perceptron)."""
    # 1. Classical Logistic Regression
    t0_lr = time.perf_counter()
    lr = LogisticRegression(random_state=seed, max_iter=200)
    lr.fit(X_train, y_train)
    t_lr = time.perf_counter() - t0_lr
    y_pred_lr = lr.predict(X_test)
    
    # 2. Classical MLP Classifier (equivalent small capacity: 4 hidden units)
    t0_mlp = time.perf_counter()
    mlp = MLPClassifier(hidden_layer_sizes=(4,), activation='relu', solver='adam', max_iter=200, random_state=seed)
    mlp.fit(X_train, y_train)
    t_mlp = time.perf_counter() - t0_mlp
    y_pred_mlp = mlp.predict(X_test)
    
    return {
        "LogisticRegression": {
            "model": lr,
            "training_time_s": t_lr,
            "accuracy": float(accuracy_score(y_test, y_pred_lr)),
            "f1": float(f1_score(y_test, y_pred_lr, zero_division=0)),
            "params_count": int(X_train.shape[1] + 1)
        },
        "Classical_MLP": {
            "model": mlp,
            "training_time_s": t_mlp,
            "accuracy": float(accuracy_score(y_test, y_pred_mlp)),
            "f1": float(f1_score(y_test, y_pred_mlp, zero_division=0)),
            "params_count": int(X_train.shape[1] * 4 + 4 + 4 * 1 + 1)  # W1 + b1 + W2 + b2
        }
    }

