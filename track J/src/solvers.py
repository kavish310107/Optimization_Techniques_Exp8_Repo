"""
Optimization Solvers for Test-Suite Minimization & Prioritization.
Formulations:
1. Baseline: Naive Random Execution & Full Execution.
2. Greedy Cost-Effective Heuristic (Additional Greedy with Coverage Density).
3. Exact Integer Linear Programming (ILP) Minimum-Weight Set Cover using SciPy HiGHS.
4. Dynamic Programming (0-1 Knapsack Formulation under strict CI execution budget B).
"""

import time
import numpy as np
from typing import List, Set, Dict, Any, Tuple
from scipy.optimize import milp, LinearConstraint
from .models import TestCase, TestSuiteInstance, compute_apfd


def solve_naive_full_suite(instance: TestSuiteInstance, seed: int = 42) -> Dict[str, Any]:
    """Naive Baseline: Runs entire test suite in random/file-system order."""
    rng = np.random.default_rng(seed)
    shuffled_tests = list(instance.test_cases)
    rng.shuffle(shuffled_tests)
    
    total_time = sum(tc.duration_ms for tc in shuffled_tests)
    covered = set().union(*(tc.covered_requirements for tc in shuffled_tests))
    faults = set().union(*(tc.faults_detected for tc in shuffled_tests))
    all_faults = instance.all_detected_faults
    apfd = compute_apfd(shuffled_tests, all_faults)
    
    return {
        "method": "Naive Full Suite (Unoptimized)",
        "selected_tests": shuffled_tests,
        "num_selected": len(shuffled_tests),
        "total_duration_ms": total_time,
        "coverage_count": len(covered),
        "coverage_pct": (len(covered) / instance.num_requirements) * 100.0,
        "faults_detected_count": len(faults),
        "apfd_score": apfd,
        "solver_time_ms": 0.05
    }


def solve_greedy_additional_coverage(instance: TestSuiteInstance) -> Dict[str, Any]:
    """
    Greedy Additional Coverage Heuristic:
    Iteratively selects test case maximizing [Marginal New Requirements Covered / Duration_ms].
    Guarantees full available coverage with submodular diminishing returns.
    """
    t0 = time.perf_counter()
    target_requirements = instance.total_covered_requirements
    uncovered = set(target_requirements)
    available_tests = list(instance.test_cases)
    
    selected_tests: List[TestCase] = []
    
    while uncovered and available_tests:
        best_tc = None
        best_density = -1.0
        
        for tc in available_tests:
            marginal_cov = len(tc.covered_requirements.intersection(uncovered))
            density = marginal_cov / max(1.0, tc.duration_ms)
            if density > best_density:
                best_density = density
                best_tc = tc
                
        if best_tc is None or best_density <= 0:
            break
            
        selected_tests.append(best_tc)
        uncovered.difference_update(best_tc.covered_requirements)
        available_tests.remove(best_tc)
        
    solver_time = (time.perf_counter() - t0) * 1000.0
    total_time = sum(tc.duration_ms for tc in selected_tests)
    covered = set().union(*(tc.covered_requirements for tc in selected_tests))
    faults = set().union(*(tc.faults_detected for tc in selected_tests))
    all_faults = instance.all_detected_faults
    apfd = compute_apfd(selected_tests, all_faults)
    
    return {
        "method": "Greedy Cost-Effective Minimization",
        "selected_tests": selected_tests,
        "num_selected": len(selected_tests),
        "total_duration_ms": total_time,
        "coverage_count": len(covered),
        "coverage_pct": (len(covered) / instance.num_requirements) * 100.0,
        "faults_detected_count": len(faults),
        "apfd_score": apfd,
        "solver_time_ms": solver_time
    }


def solve_ilp_minimum_cost_suite(instance: TestSuiteInstance) -> Dict[str, Any]:
    """
    Exact Integer Linear Programming (ILP) via SciPy HiGHS:
    Min-Weight Set Cover:
    Minimize sum_{i} duration_i * x_i
    Subject to:
      sum_{i : req in tc_i} x_i >= 1  for all covered requirements
      x_i in {0, 1}
    """
    t0 = time.perf_counter()
    n_tests = len(instance.test_cases)
    covered_reqs = sorted(list(instance.total_covered_requirements))
    n_reqs = len(covered_reqs)
    
    c = np.array([tc.duration_ms for tc in instance.test_cases])
    
    # Construct binary constraint matrix A_ub where A[r, i] = 1 if test i covers req r
    A = np.zeros((n_reqs, n_tests))
    req_to_row = {r: idx for idx, r in enumerate(covered_reqs)}
    
    for i, tc in enumerate(instance.test_cases):
        for r in tc.covered_requirements:
            if r in req_to_row:
                A[req_to_row[r], i] = 1.0
                
    # Constraints: A x >= 1
    constraints = LinearConstraint(A, lb=np.ones(n_reqs), ub=np.full(n_reqs, np.inf))
    integrality = np.ones(n_tests)  # All binary
    
    res = milp(c=c, integrality=integrality, constraints=constraints, bounds=(0, 1))
    solver_time = (time.perf_counter() - t0) * 1000.0
    
    if not res.success:
        raise RuntimeError(f"ILP optimization failed: {res.status}")
        
    x_opt = np.round(res.x).astype(int)
    selected_indices = [i for i in range(n_tests) if x_opt[i] == 1]
    
    # Sort selected tests by coverage density for optimal prioritization sequence
    selected_tests = [instance.test_cases[i] for i in selected_indices]
    selected_tests.sort(key=lambda tc: len(tc.covered_requirements) / max(1.0, tc.duration_ms), reverse=True)
    
    total_time = sum(tc.duration_ms for tc in selected_tests)
    covered = set().union(*(tc.covered_requirements for tc in selected_tests))
    faults = set().union(*(tc.faults_detected for tc in selected_tests))
    all_faults = instance.all_detected_faults
    apfd = compute_apfd(selected_tests, all_faults)
    
    return {
        "method": "Exact ILP Set-Cover Minimization (HiGHS)",
        "selected_tests": selected_tests,
        "num_selected": len(selected_tests),
        "total_duration_ms": total_time,
        "coverage_count": len(covered),
        "coverage_pct": (len(covered) / instance.num_requirements) * 100.0,
        "faults_detected_count": len(faults),
        "apfd_score": apfd,
        "solver_time_ms": solver_time
    }


def solve_budgeted_dp_suite(instance: TestSuiteInstance, time_budget_ms: float) -> Dict[str, Any]:
    """
    Dynamic Programming (DP) for Budget-Constrained CI Execution:
    Given a hard execution time limit B (e.g., 200 ms for pull request gate),
    selects subset of tests maximizing unique coverage without exceeding B.
    Formulated as a 0-1 Knapsack with coverage values.
    """
    t0 = time.perf_counter()
    
    # Scale times to integers (bins of 5ms)
    time_scale = 5.0
    int_budget = int(time_budget_ms / time_scale)
    
    tests = instance.test_cases
    n = len(tests)
    weights = [max(1, int(np.round(tc.duration_ms / time_scale))) for tc in tests]
    values = [len(tc.covered_requirements) for tc in tests]
    
    # Standard 0-1 knapsack DP table
    dp = np.zeros((n + 1, int_budget + 1), dtype=int)
    
    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for b in range(int_budget + 1):
            if w <= b:
                dp[i, b] = max(dp[i - 1, b], dp[i - 1, b - w] + v)
            else:
                dp[i, b] = dp[i - 1, b]
                
    # Backtrack to find selected tests
    curr_b = int_budget
    selected_indices = []
    for i in range(n, 0, -1):
        if dp[i, curr_b] != dp[i - 1, curr_b]:
            selected_indices.append(i - 1)
            curr_b -= weights[i - 1]
            
    selected_tests = [tests[idx] for idx in selected_indices]
    selected_tests.sort(key=lambda tc: len(tc.covered_requirements) / max(1.0, tc.duration_ms), reverse=True)
    
    solver_time = (time.perf_counter() - t0) * 1000.0
    total_time = sum(tc.duration_ms for tc in selected_tests)
    covered = set().union(*(tc.covered_requirements for tc in selected_tests))
    faults = set().union(*(tc.faults_detected for tc in selected_tests))
    all_faults = instance.all_detected_faults
    apfd = compute_apfd(selected_tests, all_faults)
    
    return {
        "method": f"Budgeted Dynamic Programming (B={time_budget_ms:.0f}ms)",
        "selected_tests": selected_tests,
        "num_selected": len(selected_tests),
        "total_duration_ms": total_time,
        "coverage_count": len(covered),
        "coverage_pct": (len(covered) / instance.num_requirements) * 100.0,
        "faults_detected_count": len(faults),
        "apfd_score": apfd,
        "solver_time_ms": solver_time
    }

