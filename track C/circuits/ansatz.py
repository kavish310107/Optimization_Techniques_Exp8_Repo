"""Quantum circuit builders and ansatz definitions:
- QAOA circuit (cost unitary e^{-i gamma H_C} and transverse-field mixer e^{-i beta H_M})
- Hardware-Efficient VQE Ansatz (RealAmplitudes / RY-CX layers)
- Hamiltonian representations (Pauli Z_i Z_j for Ising / Max-Cut)
"""
from typing import List, Tuple, Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp


def build_maxcut_hamiltonian(W: np.ndarray) -> Tuple[SparsePauliOp, float]:
    """Convert weighted adjacency matrix W to Ising Pauli Z Hamiltonian.
    
    Max-Cut Hamiltonian:
        H_C = sum_{i < j} (W_ij / 2) Z_i Z_j
    Offset = -0.5 * sum_{i < j} W_ij
    
    Ground state minimizes <H_C>, corresponding to maximum cut.
    """
    n = W.shape[0]
    pauli_list = []
    total_w = 0.0

    for i in range(n):
        for j in range(i + 1, n):
            w = W[i, j]
            if abs(w) > 1e-9:
                # Build Pauli string with Z at i and j, I elsewhere
                # Qiskit qubit 0 is rightmost in string: string[n - 1 - k]
                chars = ['I'] * n
                chars[n - 1 - i] = 'Z'
                chars[n - 1 - j] = 'Z'
                p_str = "".join(chars)
                pauli_list.append((p_str, 0.5 * float(w)))
                total_w += float(w)

    if not pauli_list:
        # Trivial graph
        pauli_list = [('I' * n, 0.0)]

    H_C = SparsePauliOp.from_list(pauli_list)
    offset = -0.5 * total_w
    return H_C, offset


def build_qaoa_circuit(W: np.ndarray, p: int) -> QuantumCircuit:
    """Build parameterized QAOA circuit of depth p for graph W.
    
    Circuit Structure:
    1. Initial state: |+>^n via Hadamard gates on all qubits.
    2. For step l = 1 ... p:
       a. Cost unitary: U(C, gamma_l) = prod_{i<j} e^{-i gamma_l w_ij Z_i Z_j / 2}
          Implemented via CNOT(i, j) -> RZ(gamma_l * w_ij) -> CNOT(i, j)
       b. Mixer unitary: U(B, beta_l) = prod_i e^{-i beta_l X_i}
          Implemented via RX(2 * beta_l) on all qubits.
    """
    n = W.shape[0]
    qc = QuantumCircuit(n)

    gammas = ParameterVector('gamma', p)
    betas = ParameterVector('beta', p)

    # 1. Uniform superposition
    qc.h(range(n))

    # 2. Alternating layers
    for l in range(p):
        # Cost Hamiltonian layer
        for i in range(n):
            for j in range(i + 1, n):
                w = W[i, j]
                if abs(w) > 1e-9:
                    qc.cx(i, j)
                    qc.rz(gammas[l] * float(w), j)
                    qc.cx(i, j)

        # Mixer layer
        for i in range(n):
            qc.rx(2.0 * betas[l], i)

    return qc


def build_vqe_ansatz(num_qubits: int, reps: int = 2) -> QuantumCircuit:
    """Build a hardware-efficient parameterized quantum circuit (RealAmplitudes RY-CX ansatz).
    
    Each layer consists of:
    - Single-qubit RY(theta) rotations on all qubits
    - Linear entanglement ladder via CNOT(i, i+1) gates
    """
    qc = QuantumCircuit(num_qubits)
    num_params = num_qubits * (reps + 1)
    thetas = ParameterVector('theta', num_params)

    param_idx = 0
    for r in range(reps):
        for q in range(num_qubits):
            qc.ry(thetas[param_idx], q)
            param_idx += 1
        for q in range(num_qubits - 1):
            qc.cx(q, q + 1)

    # Final rotation layer
    for q in range(num_qubits):
        qc.ry(thetas[param_idx], q)
        param_idx += 1

    return qc

