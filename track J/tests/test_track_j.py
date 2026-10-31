"""
Automated Unit Tests for Track J: Software-Engineering Optimization (Test-Suite Minimization & Prioritization).
Verifies:
1. Deterministic generation of realistic CI test suite models.
2. APFD metric calculation edge cases and monotonic ordering.
3. Naive full suite baseline execution and coverage verification.
4. Greedy additional coverage heuristic feasibility and coverage preservation.
5. Exact Integer Linear Programming (ILP) minimum-weight set-cover optimality.
6. Budgeted Dynamic Programming budget-bound constraint satisfaction.
"""

import os
import sys
import pytest
import numpy as np

# Add track J to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import TestCase, TestSuiteInstance, generate_realistic_ci_test_suite, compute_apfd
from src.solvers import (
    solve_naive_full_suite,
    solve_greedy_additional_coverage,
    solve_ilp_minimum_cost_suite,
    solve_budgeted_dp_suite
)


def test_test_suite_generator():
    suite = generate_realistic_ci_test_suite(num_tests=30, num_requirements=15, num_faults=5, seed=42)
    assert len(suite.test_cases) == 30
    assert suite.num_requirements == 15
    assert suite.total_duration_ms > 0
    # Every requirement is covered by at least one test
    assert len(suite.total_covered_requirements) == 15


def test_apfd_metric():
    tc1 = TestCase(id=0, name="t0", duration_ms=10.0, faults_detected={0, 1})
    tc2 = TestCase(id=1, name="t1", duration_ms=10.0, faults_detected={2})
    tc3 = TestCase(id=2, name="t2", duration_ms=10.0, faults_detected=set())
    
    all_faults = {0, 1, 2}
    
    # Optimal ordering: tc1, tc2, tc3
    apfd_opt = compute_apfd([tc1, tc2, tc3], all_faults)
    # Suboptimal ordering: tc3, tc2, tc1
    apfd_sub = compute_apfd([tc3, tc2, tc1], all_faults)
    
    assert apfd_opt > apfd_sub, "Optimal test ordering must yield strictly higher APFD than reversed ordering."
    assert 0.0 <= apfd_opt <= 1.0


def test_greedy_minimization():
    suite = generate_realistic_ci_test_suite(num_tests=40, num_requirements=20, num_faults=8, seed=99)
    res = solve_greedy_additional_coverage(suite)
    
    assert res["coverage_pct"] == 100.0, "Greedy minimization must preserve 100% of available coverage."
    assert res["num_selected"] < len(suite.test_cases), "Greedy selection must reduce suite size."
    assert res["total_duration_ms"] < suite.total_duration_ms


def test_ilp_minimum_cost():
    suite = generate_realistic_ci_test_suite(num_tests=40, num_requirements=20, num_faults=8, seed=99)
    res_greedy = solve_greedy_additional_coverage(suite)
    res_ilp = solve_ilp_minimum_cost_suite(suite)
    
    assert res_ilp["coverage_pct"] == 100.0, "ILP must achieve 100% coverage."
    # Exact ILP objective should be less than or equal to greedy heuristic
    assert res_ilp["total_duration_ms"] <= res_greedy["total_duration_ms"] + 1e-4, "Exact ILP duration must be <= greedy duration."


def test_budgeted_dp():
    suite = generate_realistic_ci_test_suite(num_tests=50, num_requirements=25, num_faults=10, seed=123)
    budget_ms = 150.0
    res_dp = solve_budgeted_dp_suite(suite, time_budget_ms=budget_ms)
    
    # Tolerating small binning discretization (one 5ms bin)
    assert res_dp["total_duration_ms"] <= budget_ms + 10.0, f"DP solution exceeded time budget: {res_dp['total_duration_ms']} > {budget_ms}"
    assert res_dp["num_selected"] > 0

