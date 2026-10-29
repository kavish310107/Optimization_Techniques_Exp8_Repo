"""Classical discrete algorithms:
- Greedy Heuristics (Knapsack value-to-weight ratio greedy, Max-Cut greedy degree partition)
- Dynamic Programming (0-1 Knapsack table algorithm)
- Branch and Bound (Depth-First Search with fractional relaxation upper bounding)
- Integer Linear Programming (ILP using SciPy's HiGHS branch-and-cut solver)
- QUBO / Ising Classical Solvers:
    - Simulated Annealing
    - Exact Classical Brute-Force (exhaustive ground-state verification for Track C baseline)
"""
import time
from typing import Tuple, Optional, List, Dict, Any
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

from problems.base import DiscreteSolution
from problems.knapsack import KnapsackProblem
from problems.maxcut import MaxCutProblem


class GreedyKnapsack:
    """Greedy heuristic for 0-1 Knapsack using value-to-weight density ratio."""

    def solve(self, problem: KnapsackProblem) -> DiscreteSolution:
        t0 = time.perf_counter()
        ratios = problem.values / np.maximum(problem.weights, 1e-9)
        # Sort items in descending order of value-to-weight ratio
        sorted_indices = np.argsort(-ratios)

        x = np.zeros(problem.n, dtype=int)
        current_weight = 0.0
        current_value = 0.0

        for idx in sorted_indices:
            w = problem.weights[idx]
            if current_weight + w <= problem.capacity:
                x[idx] = 1
                current_weight += w
                current_value += problem.values[idx]

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return DiscreteSolution(
            variables=x,
            objective_value=current_value,
            feasible=True,
            runtime_ms=runtime_ms,
            method_name="Greedy (Density Ratio)",
            extra={"total_weight": current_weight}
        )


class DynamicProgrammingKnapsack:
    """Exact Dynamic Programming for 0-1 Knapsack (Integer capacity pseudo-polynomial O(n*W))."""

    def solve(self, problem: KnapsackProblem, capacity_scale: int = 1) -> DiscreteSolution:
        t0 = time.perf_counter()
        # Scale weights and capacity to integers if needed
        W = int(round(problem.capacity * capacity_scale))
        weights_int = np.round(problem.weights * capacity_scale).astype(int)
        n = problem.n
        values = problem.values

        # dp[i][w] = max value using subset of first i items with weight limit w
        dp = np.zeros((n + 1, W + 1), dtype=float)

        for i in range(1, n + 1):
            w_i = weights_int[i - 1]
            v_i = values[i - 1]
            dp[i, :] = dp[i - 1, :]
            if w_i <= W:
                dp[i, w_i:] = np.maximum(dp[i - 1, w_i:], dp[i - 1, :W + 1 - w_i] + v_i)

        # Backtrack to find chosen items
        x = np.zeros(n, dtype=int)
        cur_w = W
        for i in range(n, 0, -1):
            if dp[i, cur_w] != dp[i - 1, cur_w]:
                x[i - 1] = 1
                cur_w -= weights_int[i - 1]

        val, wt, feas = problem.evaluate(x)
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        return DiscreteSolution(
            variables=x,
            objective_value=val,
            feasible=feas,
            runtime_ms=runtime_ms,
            method_name="Dynamic Programming",
            extra={"table_size": (n + 1, W + 1)}
        )


class BranchAndBoundKnapsack:
    """Exact Branch and Bound for 0-1 Knapsack using Fractional Relaxation Upper Bounding."""

    def solve(self, problem: KnapsackProblem) -> DiscreteSolution:
        t0 = time.perf_counter()
        n = problem.n
        # Sort items by value/weight ratio descending for tight LP bounds
        ratios = problem.values / np.maximum(problem.weights, 1e-9)
        order = np.argsort(-ratios)
        v_sorted = problem.values[order]
        w_sorted = problem.weights[order]
        W = problem.capacity

        best_val = 0.0
        best_x_sorted = np.zeros(n, dtype=int)
        nodes_explored = 0

        def fractional_bound(level: int, current_w: float, current_v: float) -> float:
            """Compute continuous relaxation (greedy fractional knapsack) upper bound."""
            if current_w > W:
                return 0.0
            bound = current_v
            rem_capacity = W - current_w
            for j in range(level, n):
                if w_sorted[j] <= rem_capacity:
                    rem_capacity -= w_sorted[j]
                    bound += v_sorted[j]
                else:
                    bound += v_sorted[j] * (rem_capacity / w_sorted[j])
                    break
            return bound

        # DFS stack: (level, current_w, current_v, current_x_list)
        stack = [(0, 0.0, 0.0, [])]

        while stack:
            level, cur_w, cur_v, cur_x = stack.pop()
            nodes_explored += 1

            if level == n:
                if cur_v > best_val and cur_w <= W:
                    best_val = cur_v
                    best_x_sorted = np.array(cur_x, dtype=int)
                continue

            # Pruning condition: upper bound <= current best known integer solution
            bound = fractional_bound(level, cur_w, cur_v)
            if bound <= best_val:
                continue

            # Branch 1: Exclude item level
            stack.append((level + 1, cur_w, cur_v, cur_x + [0]))

            # Branch 2: Include item level (if weight capacity allows)
            if cur_w + w_sorted[level] <= W:
                stack.append((level + 1, cur_w + w_sorted[level], cur_v + v_sorted[level], cur_x + [1]))

        # Map solution back to original item indices
        best_x = np.zeros(n, dtype=int)
        best_x[order] = best_x_sorted

        val, wt, feas = problem.evaluate(best_x)
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        return DiscreteSolution(
            variables=best_x,
            objective_value=val,
            feasible=feas,
            runtime_ms=runtime_ms,
            method_name="Branch and Bound",
            extra={"nodes_explored": nodes_explored}
        )


class ILPKnapsack:
    """Exact Integer Linear Programming (ILP) using SciPy HiGHS Branch-and-Cut solver."""

    def solve(self, problem: KnapsackProblem) -> DiscreteSolution:
        t0 = time.perf_counter()
        n = problem.n
        # SciPy milp minimizes c^T x, so c = -values
        c = -problem.values.astype(float)
        integrality = np.ones(n, dtype=int)  # 1 indicates binary integer constraint
        constraints = LinearConstraint(A=problem.weights.reshape(1, -1), lb=0.0, ub=problem.capacity)
        bounds = Bounds(lb=np.zeros(n), ub=np.ones(n))

        res = milp(c=c, integrality=integrality, constraints=constraints, bounds=bounds)

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        if not res.success:
            raise RuntimeError(f"MILP solver failed: {res.status_message}")

        x = np.round(res.x).astype(int)
        val, wt, feas = problem.evaluate(x)

        return DiscreteSolution(
            variables=x,
            objective_value=val,
            feasible=feas,
            runtime_ms=runtime_ms,
            method_name="ILP (SciPy HiGHS)",
            extra={"solver_status": res.status}
        )


class GreedyMaxCut:
    """Greedy local partition heuristic for Max-Cut (Sahni-Gonzales 0.5-approximation)."""

    def solve(self, problem: MaxCutProblem) -> DiscreteSolution:
        t0 = time.perf_counter()
        n = problem.n
        x = np.zeros(n, dtype=int)

        # Incrementally assign each node to the partition that maximizes cut to already assigned nodes
        for i in range(n):
            # If x[i] = 0, cut gain from assigned neighbors with x[j]=1
            gain_0 = sum(problem.W[i, j] for j in range(i) if x[j] == 1)
            # If x[i] = 1, cut gain from assigned neighbors with x[j]=0
            gain_1 = sum(problem.W[i, j] for j in range(i) if x[j] == 0)
            x[i] = 1 if gain_1 >= gain_0 else 0

        # Local search single-flip improvement
        improved = True
        while improved:
            improved = False
            for i in range(n):
                current_cut = problem.evaluate_cut(x)
                x[i] = 1 - x[i]
                new_cut = problem.evaluate_cut(x)
                if new_cut > current_cut:
                    improved = True
                else:
                    x[i] = 1 - x[i]  # Revert

        cut = problem.evaluate_cut(x)
        runtime_ms = (time.perf_counter() - t0) * 1000.0

        return DiscreteSolution(
            variables=x,
            objective_value=cut,
            feasible=True,
            runtime_ms=runtime_ms,
            method_name="Greedy Local Search (Max-Cut)"
        )


class SimulatedAnnealingQUBO:
    """Simulated Annealing heuristic for general QUBO / Ising minimization."""

    def __init__(self, t_initial: float = 10.0, t_final: float = 1e-3, alpha: float = 0.98, steps_per_t: int = 50, seed: int = 42):
        self.t_initial = t_initial
        self.t_final = t_final
        self.alpha = alpha
        self.steps_per_t = steps_per_t
        self.seed = seed

    def solve(self, Q: np.ndarray, offset: float = 0.0) -> DiscreteSolution:
        t0 = time.perf_counter()
        rng = np.random.RandomState(self.seed)
        n = Q.shape[0]

        # Initial random binary configuration
        x = rng.choice([0, 1], size=n)
        current_energy = float(x.T @ Q @ x + offset)
        best_x = x.copy()
        best_energy = current_energy

        T = self.t_initial
        while T > self.t_final:
            for _ in range(self.steps_per_t):
                idx = rng.randint(0, n)
                x_new = x.copy()
                x_new[idx] = 1 - x_new[idx]

                new_energy = float(x_new.T @ Q @ x_new + offset)
                delta_E = new_energy - current_energy

                if delta_E < 0 or rng.rand() < np.exp(-delta_E / max(T, 1e-12)):
                    x = x_new
                    current_energy = new_energy
                    if current_energy < best_energy:
                        best_energy = current_energy
                        best_x = x.copy()

            T *= self.alpha

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return DiscreteSolution(
            variables=best_x,
            objective_value=best_energy,
            feasible=True,
            runtime_ms=runtime_ms,
            method_name="Simulated Annealing (QUBO)",
            extra={"best_qubo_energy": best_energy}
        )


class ClassicalExactIsingSolver:
    """Exact classical solver (exhaustive search) for small QUBO / Ising systems.
    
    Serves as ground-truth classical baseline for Track C quantum comparisons.
    """

    def solve(self, problem: MaxCutProblem) -> DiscreteSolution:
        t0 = time.perf_counter()
        n = problem.n
        if n > 22:
            raise ValueError(f"Exhaustive search on n={n} requires 2^{n} states; use heuristic for n > 22.")

        best_cut = -1.0
        best_x = None

        # Iterate all 2^n configurations
        for i in range(1 << n):
            x = np.array([(i >> j) & 1 for j in range(n)], dtype=int)
            cut = problem.evaluate_cut(x)
            if cut > best_cut:
                best_cut = cut
                best_x = x.copy()

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        spins = problem.binary_to_spin(best_x)
        ground_energy = problem.evaluate_energy(spins)

        return DiscreteSolution(
            variables=best_x,
            objective_value=best_cut,
            feasible=True,
            runtime_ms=runtime_ms,
            method_name="Exact Classical Ground State",
            extra={"ground_state_energy": ground_energy, "spins": spins.tolist()}
        )
