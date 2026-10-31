"""
Explicit quantum circuit implementations for foundational quantum algorithms.
Built using native Qiskit 2.x primitives (QuantumCircuit, gates).
Hand-crafted circuits without relying on black-box library wrappers.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def build_deutsch_jozsa_circuit(n_qubits: int, oracle_type: str = "balanced") -> QuantumCircuit:
    """
    Constructs Deutsch-Jozsa circuit.
    Determines whether a boolean function f: {0,1}^n -> {0,1} is constant or balanced.
    Requires exactly 1 query to the quantum oracle vs 2^(n-1) + 1 classical queries.
    """
    if n_qubits < 1:
        raise ValueError("Deutsch-Jozsa requires at least 1 input qubit.")
    
    # n input qubits + 1 ancilla qubit
    qc = QuantumCircuit(n_qubits + 1, n_qubits)
    
    # Prepare ancilla in |-> = (|0> - |1>)/sqrt(2)
    qc.x(n_qubits)
    qc.h(n_qubits)
    
    # Put input qubits into equal superposition
    for i in range(n_qubits):
        qc.h(i)
        
    qc.barrier()
    
    # Oracle implementation
    if oracle_type == "constant_0":
        pass  # Identity: f(x) = 0
    elif oracle_type == "constant_1":
        qc.x(n_qubits)  # Invert ancilla: f(x) = 1
    elif oracle_type == "balanced":
        # Balanced: f(x) = x_0 (or parity)
        for i in range(n_qubits):
            qc.cx(i, n_qubits)
    else:
        raise ValueError(f"Unknown oracle_type: {oracle_type}")
        
    qc.barrier()
    
    # Interfere input qubits
    for i in range(n_qubits):
        qc.h(i)
        
    # Measure input qubits
    for i in range(n_qubits):
        qc.measure(i, i)
        
    return qc


def build_bernstein_vazirani_circuit(secret_string: str) -> QuantumCircuit:
    """
    Constructs Bernstein-Vazirani circuit to learn hidden bitstring s in {0,1}^n.
    f(x) = s . x (mod 2).
    Requires exactly 1 quantum query vs n classical queries.
    """
    n_qubits = len(secret_string)
    if n_qubits < 1:
        raise ValueError("Secret string cannot be empty.")
    
    qc = QuantumCircuit(n_qubits + 1, n_qubits)
    
    # Ancilla in |->
    qc.x(n_qubits)
    qc.h(n_qubits)
    
    # Superposition
    for i in range(n_qubits):
        qc.h(i)
        
    qc.barrier()
    
    # Oracle for s: apply CNOT from i to ancilla if s[i] == '1'
    # Reverse string indexing to match Qiskit qubit ordering (q0 = LSB)
    rev_s = secret_string[::-1]
    for i in range(n_qubits):
        if rev_s[i] == '1':
            qc.cx(i, n_qubits)
            
    qc.barrier()
    
    # Hadamard transform
    for i in range(n_qubits):
        qc.h(i)
        
    # Measure
    for i in range(n_qubits):
        qc.measure(i, i)
        
    return qc


def build_grover_circuit(n_qubits: int, target_state: str, num_iterations: int = 1) -> QuantumCircuit:
    """
    Constructs Grover's Search circuit for a target bitstring in 2^n unstructured items.
    Provides quadratic speedup: O(sqrt(N)) quantum oracle queries vs O(N) classical queries.
    """
    if len(target_state) != n_qubits:
        raise ValueError("Target state length must equal n_qubits.")
        
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # Initialize uniform superposition
    for i in range(n_qubits):
        qc.h(i)
        
    # Grover iterations
    for _ in range(num_iterations):
        qc.barrier()
        # --- Phase Oracle for target_state ---
        # Map target state to |11...1>
        rev_target = target_state[::-1]
        for i, b in enumerate(rev_target):
            if b == '0':
                qc.x(i)
                
        # Apply multi-controlled Z
        if n_qubits == 2:
            qc.cz(0, 1)
        elif n_qubits == 3:
            qc.h(2)
            qc.ccx(0, 1, 2)
            qc.h(2)
        else:
            qc.h(n_qubits - 1)
            qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            qc.h(n_qubits - 1)
            
        for i, b in enumerate(rev_target):
            if b == '0':
                qc.x(i)
                
        qc.barrier()
        # --- Diffusion Operator (Inversion about the mean: 2|s><s| - I) ---
        for i in range(n_qubits):
            qc.h(i)
            qc.x(i)
            
        if n_qubits == 2:
            qc.cz(0, 1)
        elif n_qubits == 3:
            qc.h(2)
            qc.ccx(0, 1, 2)
            qc.h(2)
        else:
            qc.h(n_qubits - 1)
            qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            qc.h(n_qubits - 1)
            
        for i in range(n_qubits):
            qc.x(i)
            qc.h(i)
            
    qc.barrier()
    for i in range(n_qubits):
        qc.measure(i, i)
        
    return qc


def build_qft_circuit(n_qubits: int, inverse: bool = False) -> QuantumCircuit:
    """
    Constructs hand-crafted Quantum Fourier Transform circuit.
    Maps discrete computational states to frequency domain in O(n^2) gates vs O(n 2^n) classical FFT.
    """
    qc = QuantumCircuit(n_qubits)
    
    if not inverse:
        for j in range(n_qubits - 1, -1, -1):
            qc.h(j)
            for k in range(j - 1, -1, -1):
                angle = np.pi / (2 ** (j - k))
                qc.cp(angle, k, j)
        # Swap qubits
        for i in range(n_qubits // 2):
            qc.swap(i, n_qubits - 1 - i)
    else:
        # Inverse QFT
        for i in range(n_qubits // 2):
            qc.swap(i, n_qubits - 1 - i)
        for j in range(n_qubits):
            for k in range(j):
                angle = -np.pi / (2 ** (j - k))
                qc.cp(angle, k, j)
            qc.h(j)
            
    return qc


def build_qpe_circuit(n_counting_qubits: int, unitary_phase: float) -> QuantumCircuit:
    """
    Quantum Phase Estimation (QPE) circuit.
    Estimates phase theta in U|psi> = exp(2*pi*i*theta)|psi|.
    Uses eigenstate |1> with phase gate P(2*pi*theta).
    """
    # counting qubits + 1 state qubit
    n_total = n_counting_qubits + 1
    qc = QuantumCircuit(n_total, n_counting_qubits)
    
    # Prepare eigenstate |1> on ancilla qubit (index n_counting_qubits)
    qc.x(n_counting_qubits)
    
    # Superposition on counting qubits
    for i in range(n_counting_qubits):
        qc.h(i)
        
    qc.barrier()
    
    # Controlled-U^(2^j) operations
    for j in range(n_counting_qubits):
        repetitions = 2 ** j
        phase_angle = 2 * np.pi * unitary_phase * repetitions
        qc.cp(phase_angle, j, n_counting_qubits)
        
    qc.barrier()
    
    # Apply Inverse QFT on counting register
    inv_qft = build_qft_circuit(n_counting_qubits, inverse=True)
    qc.compose(inv_qft, qubits=list(range(n_counting_qubits)), inplace=True)
    
    qc.barrier()
    for i in range(n_counting_qubits):
        qc.measure(i, i)
        
    return qc


def shor_period_finding_sim(a: int, N: int) -> Tuple[int, Dict[str, Any]]:
    """
    Simulates Shor's quantum period-finding routine for modular exponentiation f(x) = a^x mod N.
    Finds period r such that a^r = 1 (mod N).
    """
    if np.gcd(a, N) != 1:
        return np.gcd(a, N), {"status": "trivial_factor"}
        
    # Evaluate sequence classically to find true order r
    # (used to verify quantum phase estimation mapping)
    r = 1
    val = a % N
    sequence = [val]
    while val != 1 and r < N:
        val = (val * a) % N
        sequence.append(val)
        r += 1
        
    return r, {
        "a": a,
        "N": N,
        "period_r": r,
        "sequence": sequence
    }
