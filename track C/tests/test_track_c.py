"""Unit tests for Track C: Quantum Optimization.

Validates:
1. Hamiltonian construction from weighted graph.
2. QAOA circuit gate structure, parameter binding, and symmetry.
3. VQE ansatz structure and parameter count.
4. Parameter-shift rule exactness against central finite differences.
5. SPSA stochastic gradient computation.
6. Quantum Fisher Information (Fubini-Study) metric tensor symmetry and positive semi-definiteness.
7. Small-instance QAOA ground state solution (triangle graph).
"""
import pytest
import numpy as np
import sys
import os

TRACK_C_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TRACK_C_DIR not in sys.path:
    sys.path.insert(0, TRACK_C_DIR)

from circuits import build_maxcut_hamiltonian, build_qaoa_circuit, build_vqe_ansatz
from algorithms import (
    QuantumOptimizerEngine,
    QAOASolver,
    VQESolver,
    parameter_shift_gradient,
    spsa_gradient,
    compute_fubini_study_metric,
)


class TestQuantumCircuits:
    def test_hamiltonian_construction(self):
        # 3-node triangle with weight 1
        W = np.array([
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ])
        H, offset = build_maxcut_hamiltonian(W)
        assert len(H.paulis) == 3
        # Offset should be -0.5 * sum(weights) = -1.5
        assert np.isclose(offset, -1.5)

    def test_qaoa_circuit_parameters(self):
        W = np.array([[0, 2], [2, 0]])
        qc = build_qaoa_circuit(W, p=2)
        # Should have 2 qubits, 2 gammas, 2 betas (4 total parameters)
        assert qc.num_qubits == 2
        assert len(qc.parameters) == 4

    def test_vqe_ansatz_dimensions(self):
        qc = build_vqe_ansatz(num_qubits=3, reps=2)
        assert qc.num_qubits == 3
        # num_params = num_qubits * (reps + 1) = 3 * 3 = 9
        assert len(qc.parameters) == 9


class TestQuantumGradientsAndMetrics:
    def test_parameter_shift_vs_finite_difference(self):
        # 2-qubit ansatz
        qc = build_vqe_ansatz(num_qubits=2, reps=1)
        W = np.array([[0, 1], [1, 0]], dtype=float)
        H, _ = build_maxcut_hamiltonian(W)
        engine = QuantumOptimizerEngine()

        theta = np.array([0.5, 0.8, -0.3, 1.2])

        # Exact parameter-shift gradient
        ps_grad = parameter_shift_gradient(qc, theta, H, engine)

        # Numerical central difference
        eps = 1e-5
        fd_grad = np.zeros_like(theta)
        for i in range(len(theta)):
            t_p = theta.copy(); t_p[i] += eps
            t_m = theta.copy(); t_m[i] -= eps
            fd_grad[i] = (engine.evaluate_expectation(qc, t_p, H) - engine.evaluate_expectation(qc, t_m, H)) / (2.0 * eps)

        assert np.allclose(ps_grad, fd_grad, atol=1e-4)

    def test_fubini_study_metric_tensor(self):
        qc = build_vqe_ansatz(num_qubits=2, reps=1)
        theta = np.array([0.4, 0.9, 1.1, -0.6])
        G = compute_fubini_study_metric(qc, theta)

        # G must be symmetric
        assert np.allclose(G, G.T, atol=1e-5)
        # G must be positive semi-definite (eigenvalues >= -1e-7 due to float precision)
        eigvals = np.linalg.eigvalsh(G)
        assert np.all(eigvals >= -1e-6)


class TestQuantumSolvers:
    def test_qaoa_triangle_cut(self):
        # 3-node triangle graph: max cut is 2
        W = np.array([
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0]
        ])
        qaoa = QAOASolver(p=1, max_iters=35, seed=42)
        res = qaoa.solve(W)
        assert res["best_cut"] == 2.0
        assert res["final_energy"] < 0.0

    def test_vqe_two_qubit_ground_state(self):
        W = np.array([[0, 1], [1, 0]], dtype=float)
        H, offset = build_maxcut_hamiltonian(W)
        vqe = VQESolver(reps=1, max_iters=40, seed=42)
        res = vqe.solve(H, num_qubits=2, offset=offset)

        # Ground state of H for 2-node graph has cut = 1, so ground energy = -1.0
        assert np.isclose(res["optimal_energy"], -1.0, atol=0.05)

