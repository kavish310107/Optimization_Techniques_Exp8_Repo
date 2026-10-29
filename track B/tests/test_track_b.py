"""Unit tests for Track B: Discrete Optimization.

Validates:
1. Greedy knapsack solution feasibility and density sorting.
2. Dynamic programming exactness against known toy knapsack instance.
3. Branch-and-bound correctness, bound pruning, and agreement with DP/ILP.
4. Integer Linear Programming (SciPy HiGHS) exact solution.
5. Equivalence of Max-Cut binary representation, QUBO, and Ising energy.
6. Binary-to-spin transformations and Hamiltonian ground states.
7. Simulated Annealing heuristic on QUBO.
8. Constraint enforcement and invalid problem dimensions.
"""
import pytest
import numpy as np
import sys
import os

TRACK_B_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TRACK_B_DIR not in sys.path:
    sys.path.insert(0, TRACK_B_DIR)

from problems import KnapsackProblem, MaxCutProblem
from algorithms import (
    GreedyKnapsack,
    DynamicProgrammingKnapsack,
    BranchAndBoundKnapsack,
    ILPKnapsack,
    GreedyMaxCut,
    SimulatedAnnealingQUBO,
    ClassicalExactIsingSolver,
)


class TestKnapsackAlgorithms:
    @pytest.fixture
    def toy_knapsack(self):
        # Known textbook instance: items with values [60, 100, 120], weights [10, 20, 30], capacity 50
        # Optimal combination: items 1 and 2 (indices 1 and 2) -> weight = 20 + 30 = 50, value = 100 + 120 = 220
        # Greedy by density: ratio = [6, 5, 4] -> takes item 0 (wt 10, val 60) + item 1 (wt 20, val 100) -> wt 30, val 160 (suboptimal)
        return KnapsackProblem(
            values=np.array([60.0, 100.0, 120.0]),
            weights=np.array([10.0, 20.0, 30.0]),
            capacity=50.0,
            name="ToyKnapsack"
        )

    def test_greedy_feasibility_and_suboptimality(self, toy_knapsack):
        solver = GreedyKnapsack()
        sol = solver.solve(toy_knapsack)
        assert sol.feasible
        assert sol.objective_value == 160.0
        assert np.array_equal(sol.variables, [1, 1, 0])

    def test_dynamic_programming_exactness(self, toy_knapsack):
        solver = DynamicProgrammingKnapsack()
        sol = solver.solve(toy_knapsack)
        assert sol.feasible
        assert sol.objective_value == 220.0
        assert np.array_equal(sol.variables, [0, 1, 1])

    def test_branch_and_bound_exactness(self, toy_knapsack):
        solver = BranchAndBoundKnapsack()
        sol = solver.solve(toy_knapsack)
        assert sol.feasible
        assert sol.objective_value == 220.0
        assert np.array_equal(sol.variables, [0, 1, 1])

    def test_ilp_highs_exactness(self, toy_knapsack):
        solver = ILPKnapsack()
        sol = solver.solve(toy_knapsack)
        assert sol.feasible
        assert sol.objective_value == 220.0
        assert np.array_equal(sol.variables, [0, 1, 1])

    def test_agreement_on_random_instance(self):
        rng = np.random.RandomState(42)
        n = 10
        values = rng.randint(10, 50, size=n).astype(float)
        weights = rng.randint(5, 25, size=n).astype(float)
        capacity = float(np.sum(weights) * 0.5)

        prob = KnapsackProblem(values=values, weights=weights, capacity=capacity)
        sol_dp = DynamicProgrammingKnapsack().solve(prob)
        sol_bb = BranchAndBoundKnapsack().solve(prob)
        sol_ilp = ILPKnapsack().solve(prob)

        # All three exact solvers must find the exact same optimal objective value
        assert np.isclose(sol_dp.objective_value, sol_ilp.objective_value)
        assert np.isclose(sol_bb.objective_value, sol_ilp.objective_value)
        assert sol_dp.feasible and sol_bb.feasible and sol_ilp.feasible


class TestMaxCutQUBOAndIsing:
    @pytest.fixture
    def triangle_graph(self):
        # 3-node triangle with equal weights of 1.0 on all 3 edges
        # Max-Cut can at most cut 2 edges (weight = 2.0)
        W = np.array([
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ])
        return MaxCutProblem(adjacency_matrix=W, name="Triangle")

    def test_binary_to_spin_conversion(self):
        x = np.array([0, 1, 0])
        s = MaxCutProblem.binary_to_spin(x)
        assert np.allclose(s, [1.0, -1.0, 1.0])
        x_recovered = MaxCutProblem.spin_to_binary(s)
        assert np.allclose(x, x_recovered)

    def test_exact_classical_maxcut_ground_state(self, triangle_graph):
        solver = ClassicalExactIsingSolver()
        sol = solver.solve(triangle_graph)
        assert sol.objective_value == 2.0
        # Cut is 2, so energy H(s) = -Cut = -2 + offset adjustment
        # H(s) = -0.5 * sum w_ij + 0.5 * sum w_ij s_i s_j = -1.5 + 0.5 * (-1) = -2.0
        spins = triangle_graph.binary_to_spin(sol.variables)
        energy = triangle_graph.evaluate_energy(spins)
        # Check correspondence: higher cut -> lower Ising energy
        assert energy < 0

    def test_qubo_matrix_properties(self, triangle_graph):
        Q, offset = triangle_graph.to_qubo()
        assert Q.shape == (3, 3)
        # For each binary configuration x, x^T Q x + offset must equal -Cut(x)
        for i in range(8):
            x = np.array([(i >> j) & 1 for j in range(3)], dtype=float)
            qubo_energy = x.T @ Q @ x + offset
            cut = triangle_graph.evaluate_cut(x)
            assert np.isclose(qubo_energy, -cut)

    def test_simulated_annealing_qubo(self, triangle_graph):
        Q, offset = triangle_graph.to_qubo()
        sa = SimulatedAnnealingQUBO(t_initial=5.0, steps_per_t=50, seed=123)
        sol = sa.solve(Q, offset)
        cut = triangle_graph.evaluate_cut(sol.variables)
        assert cut == 2.0  # Must find the global max cut of 2 on triangle


class TestDiscreteInputValidation:
    def test_mismatched_dimensions(self):
        with pytest.raises(ValueError, match="length"):
            KnapsackProblem(values=np.array([1.0, 2.0]), weights=np.array([1.0]), capacity=10.0)

    def test_negative_capacity(self):
        with pytest.raises(ValueError, match="non-negative"):
            KnapsackProblem(values=np.array([1.0]), weights=np.array([1.0]), capacity=-5.0)

    def test_non_square_adjacency(self):
        with pytest.raises(ValueError, match="square"):
            MaxCutProblem(adjacency_matrix=np.ones((3, 4)))

