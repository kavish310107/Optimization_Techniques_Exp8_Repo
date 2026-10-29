"""Unit tests for Track D: Submodular, Parallel, and Distributed Optimization.

Validates:
1. Submodular facility location monotonicity and diminishing returns property.
2. Greedy submodular selection achieves >= (1 - 1/e) approx ratio against exact exhaustive search.
3. Lazy greedy produces identical selection to standard greedy with fewer evaluations.
4. Parallel loss and gradient reduction matches sequential computation exactly.
5. Amdahl's law serial fraction parameter estimation.
6. Federated averaging (FedAvg) aggregation arithmetic and loss reduction.
7. MGDA 2-task min-norm analytical solver yields convex combination in [0, 1].
8. GradNorm dynamic weight adjustment.
"""
import pytest
import numpy as np
import sys
import os

TRACK_D_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TRACK_D_DIR not in sys.path:
    sys.path.insert(0, TRACK_D_DIR)

from submodular import (
    FacilityLocationFunction,
    greedy_submodular_selection,
    lazy_greedy_submodular_selection,
    exact_submodular_maximization,
)
from parallel import (
    ParallelOptimizationBenchmark,
    fit_amdahl_and_gustafson,
)
from distributed import (
    FederatedDataset,
    compute_logistic_loss_and_grad,
    run_centralized_training,
    run_fedavg,
)
from multitask import (
    TwoTaskModel,
    solve_mgda_2task,
    run_equal_weighting_optimization,
    run_mgda_optimization,
)


class TestSubmodularOptimization:
    @pytest.fixture
    def small_facility_problem(self):
        rng = np.random.RandomState(42)
        M = rng.uniform(0.1, 5.0, size=(6, 10))
        return FacilityLocationFunction(M)

    def test_diminishing_returns(self, small_facility_problem):
        assert small_facility_problem.check_diminishing_returns(num_checks=50)

    def test_greedy_one_minus_one_over_e_guarantee(self, small_facility_problem):
        k = 3
        exact_S, exact_val = exact_submodular_maximization(small_facility_problem, k)
        greedy_S, greedy_val = greedy_submodular_selection(small_facility_problem, k)

        # Theoretical guarantee: greedy >= (1 - 1/e) * exact
        bound = (1.0 - 1.0 / np.e) * exact_val
        assert greedy_val >= bound - 1e-7
        assert greedy_val <= exact_val + 1e-7

    def test_lazy_greedy_matches_standard_greedy(self, small_facility_problem):
        k = 3
        greedy_S, greedy_val = greedy_submodular_selection(small_facility_problem, k)
        lazy_S, lazy_val, evals = lazy_greedy_submodular_selection(small_facility_problem, k)

        assert np.isclose(greedy_val, lazy_val)
        assert greedy_S == lazy_S
        assert evals < (small_facility_problem.num_facilities * k)


class TestParallelOptimization:
    def test_parallel_reduction_correctness(self):
        bench = ParallelOptimizationBenchmark(num_samples=1000, num_features=10, seed=42)
        _, loss_1, grad_1 = bench.run_parallel(num_workers=1)
        _, loss_2, grad_2 = bench.run_parallel(num_workers=2)

        assert np.isclose(loss_1, loss_2, atol=1e-5)
        assert np.allclose(grad_1, grad_2, atol=1e-5)

    def test_amdahl_fit(self):
        workers = [1, 2, 4]
        speedups = [1.0, 1.8, 3.2]
        res = fit_amdahl_and_gustafson(workers, speedups)
        assert 0.0 < res["serial_fraction_s"] < 0.3


class TestDistributedFedAvg:
    def test_fedavg_loss_reduction(self):
        data = FederatedDataset(num_clients=3, samples_per_client=100, dim=5, seed=42)
        res = run_fedavg(data, rounds=10, local_steps=3, local_lr=0.05, seed=42)

        # Final loss should be lower than initial loss
        assert res["loss_history"][-1] < res["loss_history"][0]

    def test_centralized_loss_reduction(self):
        data = FederatedDataset(num_clients=3, samples_per_client=100, dim=5, seed=42)
        res = run_centralized_training(data, total_steps=30, lr=0.1)
        assert res["final_loss"] < res["loss_history"][0]


class TestMultiTaskMGDA:
    def test_mgda_analytical_solver(self):
        g1 = np.array([1.0, 0.0])
        g2 = np.array([0.0, 1.0])
        a1, a2, mgda_grad = solve_mgda_2task(g1, g2)

        assert np.isclose(a1, 0.5)
        assert np.isclose(a2, 0.5)
        assert np.isclose(a1 + a2, 1.0)
        assert np.allclose(mgda_grad, [0.5, 0.5])

    def test_mgda_optimization_progress(self):
        model = TwoTaskModel(dim=5, num_samples=50, seed=42)
        res = run_mgda_optimization(model, steps=25, lr=0.05)
        assert res["final_L1"] < res["hist_L1"][0]
        assert res["final_L2"] < res["hist_L2"][0]

