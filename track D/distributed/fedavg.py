"""Distributed and Federated Optimization:
- Implementation of Federated Averaging (FedAvg, McMahan et al. 2017)
- Compares:
    - Centralized Optimization (Single-server standard gradient descent)
    - FedAvg with varying local steps E and communication rounds R
    - Non-IID vs IID data partitioning across clients
"""
import time
from typing import List, Dict, Any, Tuple
import numpy as np


class FederatedDataset:
    """Partitions synthetic data across K clients in IID or Non-IID distribution."""

    def __init__(self, num_clients: int = 5, samples_per_client: int = 200, dim: int = 10, non_iid: bool = False, seed: int = 42):
        rng = np.random.RandomState(seed)
        self.num_clients = num_clients
        self.dim = dim
        self.clients_X = []
        self.clients_y = []

        true_theta = rng.randn(dim)

        for k in range(num_clients):
            if non_iid:
                # Client-specific feature bias and shift
                client_mean = rng.uniform(-1.5, 1.5, size=dim)
                X_k = rng.randn(samples_per_client, dim) + client_mean
            else:
                X_k = rng.randn(samples_per_client, dim)

            z = np.dot(X_k, true_theta)
            prob = 1.0 / (1.0 + np.exp(-np.clip(z, -25.0, 25.0)))
            y_k = (rng.rand(samples_per_client) < prob).astype(float)

            self.clients_X.append(X_k)
            self.clients_y.append(y_k)

        # Full concatenated dataset for centralized baseline
        self.all_X = np.vstack(self.clients_X)
        self.all_y = np.concatenate(self.clients_y)


def compute_logistic_loss_and_grad(X: np.ndarray, y: np.ndarray, theta: np.ndarray) -> Tuple[float, np.ndarray]:
    """Analytical binary cross-entropy loss and gradient."""
    N = len(y)
    z = np.dot(X, theta)
    p = 1.0 / (1.0 + np.exp(-np.clip(z, -25.0, 25.0)))
    eps = 1e-12
    p_safe = np.clip(p, eps, 1.0 - eps)
    loss = -np.mean(y * np.log(p_safe) + (1.0 - y) * np.log(1.0 - p_safe))
    grad = np.dot(X.T, (p - y)) / N
    return float(loss), grad


def run_centralized_training(data: FederatedDataset, total_steps: int = 100, lr: float = 0.1) -> Dict[str, Any]:
    """Centralized baseline optimizer updating on pooled dataset."""
    t0 = time.perf_counter()
    dim = data.dim
    theta = np.zeros(dim, dtype=float)
    losses = []

    for step in range(total_steps):
        loss, grad = compute_logistic_loss_and_grad(data.all_X, data.all_y, theta)
        losses.append(loss)
        theta -= lr * grad

    final_loss, _ = compute_logistic_loss_and_grad(data.all_X, data.all_y, theta)
    runtime_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "final_loss": final_loss,
        "loss_history": losses,
        "runtime_ms": runtime_ms,
        "theta": theta,
        "communication_rounds": 0,
    }


def run_fedavg(
    data: FederatedDataset,
    rounds: int = 20,
    local_steps: int = 5,
    local_lr: float = 0.1,
    client_fraction: float = 1.0,
    seed: int = 42
) -> Dict[str, Any]:
    """Federated Averaging (FedAvg):
    For round r = 1 ... R:
        1. Select subset of clients S_t.
        2. Distribute global model theta_t to clients in S_t.
        3. Each client performs E local gradient steps: theta_k^{t, e+1} = theta_k^{t, e} - lr * grad_k.
        4. Central server aggregates updates via weighted average:
           theta_{t+1} = sum_{k in S_t} (n_k / n) theta_k^{t, E}.
    """
    t0 = time.perf_counter()
    rng = np.random.RandomState(seed)
    dim = data.dim
    K = data.num_clients
    total_samples = len(data.all_y)

    global_theta = np.zeros(dim, dtype=float)
    global_losses = []

    for r in range(rounds):
        # Record global loss before round update
        cur_loss, _ = compute_logistic_loss_and_grad(data.all_X, data.all_y, global_theta)
        global_losses.append(cur_loss)

        # Client sampling
        m = max(1, int(client_fraction * K))
        sampled_clients = rng.choice(K, size=m, replace=False)

        client_weights = []
        client_thetas = []

        for k in sampled_clients:
            X_k = data.clients_X[k]
            y_k = data.clients_y[k]
            n_k = len(y_k)

            # Local model initialized with global parameters
            local_theta = global_theta.copy()
            for _ in range(local_steps):
                _, grad = compute_logistic_loss_and_grad(X_k, y_k, local_theta)
                local_theta -= local_lr * grad

            client_thetas.append(local_theta)
            client_weights.append(n_k)

        # Server aggregation (weighted average)
        weights_arr = np.array(client_weights, dtype=float)
        weights_norm = weights_arr / np.sum(weights_arr)

        aggregated_theta = np.zeros(dim, dtype=float)
        for w, th in zip(weights_norm, client_thetas):
            aggregated_theta += w * th

        global_theta = aggregated_theta

    final_loss, _ = compute_logistic_loss_and_grad(data.all_X, data.all_y, global_theta)
    global_losses.append(final_loss)
    runtime_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "final_loss": final_loss,
        "loss_history": global_losses,
        "runtime_ms": runtime_ms,
        "theta": global_theta,
        "communication_rounds": rounds,
        "local_steps": local_steps,
    }

