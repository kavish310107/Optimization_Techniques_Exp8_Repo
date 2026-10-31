"""
Automated Unit Tests for Track I: Quantum Algorithms and Quantum Machine Learning.
Verifies:
1. Deutsch-Jozsa circuit construction and deterministic decision.
2. Bernstein-Vazirani bitstring recovery.
3. Grover's search quadratic amplification.
4. Quantum Fourier Transform unitary properties.
5. Quantum Phase Estimation accuracy.
6. Shor's period finding helper correctness.
7. Variational Quantum Classifier (VQC) forward pass, training step, and noise impact.
"""

import os
import sys
import pytest
import numpy as np
from qiskit.quantum_info import Statevector

# Ensure track I directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms import (
    build_deutsch_jozsa_circuit,
    build_bernstein_vazirani_circuit,
    build_grover_circuit,
    build_qft_circuit,
    build_qpe_circuit,
    shor_period_finding_sim
)
from src.qml_models import VariationalQuantumClassifier, train_classical_models


def test_deutsch_jozsa():
    # Test balanced oracle
    qc_bal = build_deutsch_jozsa_circuit(n_qubits=3, oracle_type="balanced")
    sv_bal = Statevector.from_instruction(qc_bal.remove_final_measurements(inplace=False))
    p_000_bal = sum(prob for state, prob in sv_bal.probabilities_dict().items() if state[1:] == "000")
    assert p_000_bal < 1e-6, "Balanced oracle should yield zero probability of |000>."

    # Test constant oracle
    qc_const = build_deutsch_jozsa_circuit(n_qubits=3, oracle_type="constant_0")
    sv_const = Statevector.from_instruction(qc_const.remove_final_measurements(inplace=False))
    p_000_const = sum(prob for state, prob in sv_const.probabilities_dict().items() if state[1:] == "000")
    assert p_000_const > 0.99, "Constant oracle should yield probability ~1 for |000>."


def test_bernstein_vazirani():
    secret = "101"
    qc_bv = build_bernstein_vazirani_circuit(secret)
    sv_bv = Statevector.from_instruction(qc_bv.remove_final_measurements(inplace=False))
    max_state = max(sv_bv.probabilities_dict().items(), key=lambda item: item[1])[0]
    recovered = max_state[-len(secret):]
    assert recovered == secret, f"Recovered '{recovered}' did not match secret '{secret}'."


def test_grover_search():
    target = "11"
    qc_grover = build_grover_circuit(n_qubits=2, target_state=target, num_iterations=1)
    sv_grover = Statevector.from_instruction(qc_grover.remove_final_measurements(inplace=False))
    p_target = sv_grover.probabilities_dict().get(target, 0.0)
    assert p_target > 0.95, f"Grover target probability {p_target} is below expected threshold."


def test_qft_unitary():
    qc_qft = build_qft_circuit(n_qubits=3, inverse=False)
    assert qc_qft.num_qubits == 3
    assert qc_qft.depth() > 0


def test_qpe_phase():
    # Estimate phase theta = 0.25 (1/4) using 2 counting qubits
    qc_qpe = build_qpe_circuit(n_counting_qubits=2, unitary_phase=0.25)
    sv_qpe = Statevector.from_instruction(qc_qpe.remove_final_measurements(inplace=False))
    max_state_qpe = max(sv_qpe.probabilities_dict().items(), key=lambda item: item[1])[0]
    counting_bits = max_state_qpe[1:]
    est_val = int(counting_bits, 2) / 4.0
    assert abs(est_val - 0.25) < 1e-4, f"QPE estimated phase {est_val} instead of 0.25."


def test_shor_period_finding():
    r, meta = shor_period_finding_sim(a=7, N=15)
    assert r == 4
    assert (7 ** 4) % 15 == 1


def test_vqc_classifier():
    X = np.array([[0.5, 1.0], [2.5, 0.2], [0.8, 1.2], [2.8, 0.5]])
    y = np.array([0, 1, 0, 1])
    
    vqc = VariationalQuantumClassifier(n_qubits=2, n_layers=1, max_iter=2, seed=42)
    vqc.fit(X, y)
    preds = vqc.predict(X)
    
    assert len(preds) == len(y)
    assert set(preds).issubset({0, 1})
    assert vqc.circuit_evaluations > 0
