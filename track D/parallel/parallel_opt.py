"""Parallel Program Optimization Module:
- Multi-core data parallelism on continuous optimization workload (Batch Gradient / Loss computation)
- Measures:
    - Speedup: S_p = T_1 / T_p
    - Parallel Efficiency: E_p = S_p / p
    - Communication / Synchronization overhead
- Theoretical modeling:
    - Amdahl's Law: S_p = 1 / (s + (1 - s) / p)
    - Gustafson's Law: S_p = s + p * (1 - s)
"""
import time
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np


def chunked_loss_and_gradient(chunk_args: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> Tuple[float, np.ndarray]:
    """Worker function for computing loss and gradient on a chunk of data.
    
    Logistic regression model:
        z = X theta
        p = 1 / (1 + exp(-z))
        loss = - sum (y log p + (1-y) log(1-p))
        grad = X^T (p - y)
    """
    X_chunk, y_chunk, theta = chunk_args
    z = np.dot(X_chunk, theta)
    z_clipped = np.clip(z, -30.0, 30.0)
    p = 1.0 / (1.0 + np.exp(-z_clipped))
    
    eps = 1e-12
    p_safe = np.clip(p, eps, 1.0 - eps)
    chunk_loss = -np.sum(y_chunk * np.log(p_safe) + (1.0 - y_chunk) * np.log(1.0 - p_safe))
    chunk_grad = np.dot(X_chunk.T, (p - y_chunk))
    
    return float(chunk_loss), chunk_grad


class ParallelOptimizationBenchmark:
    """Benchmark harness evaluating speedup and parallel efficiency across worker counts."""

    def __init__(self, num_samples: int = 150000, num_features: int = 60, seed: int = 42):
        rng = np.random.RandomState(seed)
        self.X = rng.randn(num_samples, num_features)
        true_theta = rng.randn(num_features)
        z = np.dot(self.X, true_theta)
        prob = 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))
        self.y = (rng.rand(num_samples) < prob).astype(float)
        self.theta = rng.randn(num_features)
        self.N = num_samples

    def run_sequential(self, num_trials: int = 3) -> float:
        """Run purely sequential computation."""
        times = []
        for _ in range(num_trials):
            t0 = time.perf_counter()
            loss, grad = chunked_loss_and_gradient((self.X, self.y, self.theta))
            times.append((time.perf_counter() - t0) * 1000.0)
        return float(np.median(times))

    def run_parallel(self, num_workers: int, num_trials: int = 3) -> Tuple[float, float, np.ndarray]:
        """Run parallel computation with num_workers partitions using ThreadPoolExecutor."""
        # Split dataset into num_workers contiguous chunks
        chunk_size = int(np.ceil(self.N / num_workers))
        chunks = []
        for w in range(num_workers):
            start = w * chunk_size
            end = min((w + 1) * chunk_size, self.N)
            if start < self.N:
                chunks.append((self.X[start:end], self.y[start:end], self.theta))

        times = []
        final_loss = 0.0
        final_grad = np.zeros_like(self.theta)

        for _ in range(num_trials):
            t0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                results = list(executor.map(chunked_loss_and_gradient, chunks))

            # Reduction step (aggregation)
            total_loss = sum(r[0] for r in results) / self.N
            total_grad = sum(r[1] for r in results) / self.N
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            times.append(elapsed_ms)
            final_loss = total_loss
            final_grad = total_grad

        return float(np.median(times)), final_loss, final_grad


def fit_amdahl_and_gustafson(p_workers: List[int], measured_speedups: List[float]) -> Dict[str, float]:
    """Estimate serial fraction 's' under Amdahl's Law from empirical measurements."""
    # S_p = 1 / (s + (1-s)/p) => 1 / S_p = s + (1-s)/p = s*(1 - 1/p) + 1/p
    # Let y = 1/S_p - 1/p, x = 1 - 1/p => y = s * x
    P = np.array(p_workers, dtype=float)
    S = np.array(measured_speedups, dtype=float)

    # Filter out single-worker (p=1) where denominator is zero
    mask = (P > 1)
    if not np.any(mask):
        return {"serial_fraction_s": 0.05, "parallel_fraction": 0.95}

    x = 1.0 - (1.0 / P[mask])
    y = (1.0 / S[mask]) - (1.0 / P[mask])
    
    # Linear least squares fit for s (constrained to [0, 1])
    s_est = float(np.sum(x * y) / np.maximum(np.sum(x ** 2), 1e-9))
    s_est = max(0.01, min(0.99, s_est))

    return {
        "serial_fraction_s": round(s_est, 4),
        "parallel_fraction": round(1.0 - s_est, 4),
    }

