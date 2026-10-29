"""Submodular Optimization Module:
- Objective: Facility Location / Set Coverage Maximization
- Properties: Monotonicity and Diminishing Returns check
- Algorithms:
    - Standard Greedy Selection (Nemhauser et al. 1978: (1 - 1/e) approx guarantee)
    - Lazy Greedy (Accelerated with max-heap priority queue)
    - Exact Brute-Force baseline (for verifying approximation ratio)
"""
from typing import Set, List, Tuple, Dict, Any, Optional
import heapq
import numpy as np


class FacilityLocationFunction:
    """Submodular Facility Location objective function:
        F(S) = sum_{j in V} max_{i in S} M_{ij}
    where S is the chosen set of facilities and M_{ij} is the utility/similarity of facility i for client j.
    
    Mathematical Properties:
    - Non-negative: F(empty) = 0 (with proper baseline)
    - Monotone increasing: S subseteq T implies F(S) <= F(T)
    - Submodular (diminishing returns): For S subseteq T and e not in T,
      F(S cup {e}) - F(S) >= F(T cup {e}) - F(T).
    """

    def __init__(self, utility_matrix: np.ndarray):
        M = np.asarray(utility_matrix, dtype=float)
        if M.ndim != 2:
            raise ValueError(f"Utility matrix must be 2D, got shape {M.shape}")
        if np.any(M < 0):
            raise ValueError("Utilities must be non-negative for monotonicity.")
        self.M = M
        self.num_facilities, self.num_clients = M.shape

    def evaluate(self, S: Set[int]) -> float:
        """Evaluate F(S). If S is empty, utility is 0."""
        if not S:
            return 0.0
        # For each client j, find max utility among facilities in S
        indices = list(S)
        sub_M = self.M[indices, :]
        max_utilities = np.max(sub_M, axis=0)
        return float(np.sum(max_utilities))

    def marginal_gain(self, S: Set[int], item: int) -> float:
        """Compute Delta(item | S) = F(S cup {item}) - F(S)."""
        if item in S:
            return 0.0
        if not S:
            return float(np.sum(self.M[item, :]))
        # Gain is sum_j max(0, M[item, j] - max_{i in S} M[i, j])
        cur_max = np.max(self.M[list(S), :], axis=0)
        new_utils = np.maximum(cur_max, self.M[item, :])
        return float(np.sum(new_utils - cur_max))

    def check_diminishing_returns(self, num_checks: int = 50, seed: int = 42) -> bool:
        """Empirically test whether the diminishing returns property holds across random subsets.
        
        S subseteq T and e not in T -> Delta(e | S) >= Delta(e | T) - eps
        """
        rng = np.random.RandomState(seed)
        all_items = list(range(self.num_facilities))
        if len(all_items) < 3:
            return True

        for _ in range(num_checks):
            # Sample sizes |S| < |T|
            k_T = rng.randint(2, self.num_facilities)
            k_S = rng.randint(1, k_T)

            # Sample T, then sample S as subset of T
            T_list = rng.choice(all_items, size=k_T, replace=False).tolist()
            S_list = rng.choice(T_list, size=k_S, replace=False).tolist()

            S = set(S_list)
            T = set(T_list)

            # Pick element e not in T
            available = [x for x in all_items if x not in T]
            if not available:
                continue
            e = rng.choice(available)

            gain_S = self.marginal_gain(S, e)
            gain_T = self.marginal_gain(T, e)

            # Diminishing returns: gain_S must be >= gain_T
            if gain_S < gain_T - 1e-9:
                return False

        return True


def greedy_submodular_selection(func: FacilityLocationFunction, k: int) -> Tuple[List[int], float]:
    """Standard Greedy Algorithm for Cardinality Constrained Submodular Maximization:
        max_{|S| <= k} F(S)
    
    Theoretical Guarantee (Nemhauser, Wolsey, Fisher 1978):
        F(S_greedy) >= (1 - 1/e) * F(S_opt) approx 0.6321 * F(S_opt)
    """
    S: Set[int] = set()
    n = func.num_facilities
    k = min(k, n)

    for _ in range(k):
        best_item = -1
        best_gain = -1.0
        for item in range(n):
            if item not in S:
                gain = func.marginal_gain(S, item)
                if gain > best_gain:
                    best_gain = gain
                    best_item = item
        if best_item != -1:
            S.add(best_item)

    val = func.evaluate(S)
    return sorted(list(S)), val


def lazy_greedy_submodular_selection(func: FacilityLocationFunction, k: int) -> Tuple[List[int], float, int]:
    """Lazy Greedy Algorithm (Minoux 1978) using a Max-Heap with upper-bound caching.
    
    Exploits submodularity: marginal gains can only decrease over iterations.
    Significantly reduces the number of function evaluations from O(n * k) to O(n + k log n).
    """
    n = func.num_facilities
    k = min(k, n)
    S: Set[int] = set()

    # Max-heap stores (-upper_bound, item, iteration_stale_stamp)
    heap = []
    eval_count = 0
    for item in range(n):
        gain = func.marginal_gain(S, item)
        eval_count += 1
        heapq.heappush(heap, (-gain, item, 0))

    current_iter = 0
    while len(S) < k and heap:
        neg_gain, item, stamp = heapq.heappop(heap)
        if stamp == current_iter:
            # The bound is fresh for the current set S, so it must be the true maximum
            S.add(item)
            current_iter += 1
        else:
            # Recompute fresh marginal gain
            fresh_gain = func.marginal_gain(S, item)
            eval_count += 1
            heapq.heappush(heap, (-fresh_gain, item, current_iter))

    val = func.evaluate(S)
    return sorted(list(S)), val, eval_count


def exact_submodular_maximization(func: FacilityLocationFunction, k: int) -> Tuple[List[int], float]:
    """Exhaustive search over all subsets of size k (for verifying (1 - 1/e) guarantee)."""
    from itertools import combinations
    n = func.num_facilities
    best_val = -1.0
    best_S = []

    for subset in combinations(range(n), k):
        val = func.evaluate(set(subset))
        if val > best_val:
            best_val = val
            best_S = list(subset)

    return sorted(best_S), best_val

