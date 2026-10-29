"""Quantum Optimization Algorithms:
1. QAOA (Quantum Approximate Optimization Algorithm)
2. VQE (Variational Quantum Eigensolver)
3. Parameter-Shift Rule for Exact Analytical Quantum Gradients
4. SPSA (Simultaneous Perturbation Stochastic Approximation)
5. QNG (Quantum Natural Gradient via Fubini-Study / Quantum Fisher Information Metric)
6. Realistic noise and finite measurement shot simulation
"""
import time
from typing import Tuple, Dict, Any, List, Optional, Callable
import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from circuits.ansatz import build_qaoa_circuit, build_vqe_ansatz, build_maxcut_hamiltonian


class QuantumOptimizerEngine:
    """Core simulation engine for evaluating parameterized quantum circuits.
    
    Supports:
    - Exact statevector simulation (infinite shots / noise-free)
    - Finite-shot measurement sampling
    - Simulated depolarizing / readout noise
    """

    def __init__(self, shots: Optional[int] = None, noise_rate: float = 0.0, seed: int = 42):
        self.shots = shots
        self.noise_rate = float(noise_rate)
        self.rng = np.random.RandomState(seed)

    def evaluate_expectation(self, circuit: QuantumCircuit, params: np.ndarray, hamiltonian: SparsePauliOp) -> float:
        """Evaluate expected value <psi(theta)| H |psi(theta)>."""
        # Bind numerical parameters
        param_dict = {p: val for p, val in zip(circuit.parameters, params)}
        bound_qc = circuit.assign_parameters(param_dict)

        # Exact statevector
        sv = Statevector.from_instruction(bound_qc)

        if self.shots is None and self.noise_rate == 0.0:
            # Pure analytic expectation
            val = float(np.real(sv.expectation_value(hamiltonian)))
            return val

        # Finite-shot simulation with optional depolarizing noise
        probs = sv.probabilities()
        n_qubits = circuit.num_qubits
        dim = 2 ** n_qubits

        # Depolarizing channel: with probability p_noise, state becomes completely mixed state
        if self.noise_rate > 0.0:
            probs = (1.0 - self.noise_rate) * probs + self.noise_rate * (np.ones(dim) / dim)

        shots = self.shots if self.shots is not None else 1024
        # Sample measurement counts from multinomial distribution
        counts = self.rng.multinomial(shots, probs)
        empirical_probs = counts / shots

        # Compute expectation over basis states from diagonal of Hamiltonian in computational basis
        # For diagonal Pauli Z operators (Ising models):
        H_diag = np.real(np.diag(hamiltonian.to_matrix()))
        noisy_expectation = float(np.dot(empirical_probs, H_diag))
        return noisy_expectation

    def sample_bitstrings(self, circuit: QuantumCircuit, params: np.ndarray, shots: int = 1024) -> Dict[str, int]:
        """Sample computational basis bitstrings for optimal parameter assignment."""
        param_dict = {p: val for p, val in zip(circuit.parameters, params)}
        bound_qc = circuit.assign_parameters(param_dict)
        sv = Statevector.from_instruction(bound_qc)
        probs = sv.probabilities()
        counts = self.rng.multinomial(shots, probs)
        n_qubits = circuit.num_qubits

        res = {}
        for idx, count in enumerate(counts):
            if count > 0:
                bitstring = format(idx, f'0{n_qubits}b')
                res[bitstring] = int(count)
        return res


def parameter_shift_gradient(
    circuit: QuantumCircuit,
    params: np.ndarray,
    hamiltonian: SparsePauliOp,
    engine: QuantumOptimizerEngine,
    shift: float = np.pi / 2.0
) -> np.ndarray:
    """Compute exact quantum gradient using the Parameter-Shift Rule:
        d <H> / d theta_i = (<H>(theta + s * e_i) - <H>(theta - s * e_i)) / (2 * sin(s))
    For standard Pauli rotation generators with eigenvalues +- 1/2, s = pi / 2.
    """
    grad = np.zeros_like(params, dtype=float)
    for i in range(len(params)):
        p_plus = params.copy()
        p_minus = params.copy()
        p_plus[i] += shift
        p_minus[i] -= shift

        e_plus = engine.evaluate_expectation(circuit, p_plus, hamiltonian)
        e_minus = engine.evaluate_expectation(circuit, p_minus, hamiltonian)
        grad[i] = (e_plus - e_minus) / (2.0 * np.sin(shift))
    return grad


def spsa_gradient(
    circuit: QuantumCircuit,
    params: np.ndarray,
    hamiltonian: SparsePauliOp,
    engine: QuantumOptimizerEngine,
    c_k: float = 0.05
) -> np.ndarray:
    """Simultaneous Perturbation Stochastic Approximation (SPSA) gradient:
    Evaluates objective at only TWO points perturbed by a random Rademacher vector delta in {-1, +1}^d.
    """
    d = len(params)
    delta = engine.rng.choice([-1.0, 1.0], size=d)

    p_plus = params + c_k * delta
    p_minus = params - c_k * delta

    e_plus = engine.evaluate_expectation(circuit, p_plus, hamiltonian)
    e_minus = engine.evaluate_expectation(circuit, p_minus, hamiltonian)

    grad = (e_plus - e_minus) / (2.0 * c_k * delta)
    return grad


def compute_fubini_study_metric(
    circuit: QuantumCircuit,
    params: np.ndarray,
    eps: float = 1e-3
) -> np.ndarray:
    """Compute Quantum Fisher Information / Fubini-Study metric tensor g_ij(theta):
        g_ij = Re( <partial_i psi | partial_j psi> - <partial_i psi|psi><psi|partial_j psi> )
    Provides the Riemannian curvature metric for Quantum Natural Gradient (QNG).
    """
    d = len(params)
    param_dict = {p: val for p, val in zip(circuit.parameters, params)}
    bound_qc = circuit.assign_parameters(param_dict)
    psi = Statevector.from_instruction(bound_qc).data

    # Finite difference approximation of state tangents |partial_i psi>
    tangents = []
    for i in range(d):
        p_shift = params.copy()
        p_shift[i] += eps
        d_dict = {p: val for p, val in zip(circuit.parameters, p_shift)}
        psi_shift = Statevector.from_instruction(circuit.assign_parameters(d_dict)).data
        d_psi = (psi_shift - psi) / eps
        tangents.append(d_psi)

    G = np.zeros((d, d), dtype=float)
    for i in range(d):
        for j in range(d):
            inner_ij = np.vdot(tangents[i], tangents[j])
            inner_i0 = np.vdot(tangents[i], psi)
            inner_0j = np.vdot(psi, tangents[j])
            g_val = np.real(inner_ij - inner_i0 * inner_0j)
            G[i, j] = g_val

    # Ensure symmetric positive semi-definite
    G = 0.5 * (G + G.T)
    return G


class QAOASolver:
    """Hybrid Quantum-Classical QAOA Solver."""

    def __init__(self, p: int = 1, shots: Optional[int] = None, noise_rate: float = 0.0, max_iters: int = 50, seed: int = 42):
        self.p = p
        self.engine = QuantumOptimizerEngine(shots=shots, noise_rate=noise_rate, seed=seed)
        self.max_iters = max_iters
        self.seed = seed

    def solve(self, W: np.ndarray, method: str = "COBYLA") -> Dict[str, Any]:
        t0 = time.perf_counter()
        H_C, offset = build_maxcut_hamiltonian(W)
        circuit = build_qaoa_circuit(W, self.p)

        rng = np.random.RandomState(self.seed)
        # 2*p parameters: [gamma_1..p, beta_1..p]
        init_params = rng.uniform(0.0, np.pi, size=2 * self.p)

        loss_history = []

        def cost_fn(theta):
            val = self.engine.evaluate_expectation(circuit, theta, H_C)
            loss_history.append(float(val + offset))
            return val

        # Hybrid classical optimization loop
        res = minimize(
            cost_fn,
            init_params,
            method=method,
            options={"maxiter": self.max_iters}
        )

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        opt_params = res.x
        final_energy = float(self.engine.evaluate_expectation(circuit, opt_params, H_C) + offset)

        # Sample bitstrings to extract best cut partition
        samples = self.engine.sample_bitstrings(circuit, opt_params, shots=2048)
        best_bitstring = max(samples.items(), key=lambda kv: kv[1])[0]

        # Convert bitstring to binary assignment vector x
        # Qiskit bitstring order is qubit n-1 ... qubit 0
        best_x = np.array([int(best_bitstring[len(best_bitstring) - 1 - i]) for i in range(W.shape[0])])

        # Evaluate cut weight
        cut_weight = 0.0
        n = W.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                if best_x[i] != best_x[j]:
                    cut_weight += W[i, j]

        return {
            "p": self.p,
            "optimal_params": opt_params.tolist(),
            "final_energy": final_energy,
            "best_cut": cut_weight,
            "best_bitstring": best_bitstring,
            "best_assignment": best_x.tolist(),
            "samples": samples,
            "iterations": len(loss_history),
            "loss_history": loss_history,
            "runtime_ms": runtime_ms,
        }


class VQESolver:
    """Variational Quantum Eigensolver (VQE) for ground state energy finding."""

    def __init__(self, reps: int = 2, shots: Optional[int] = None, noise_rate: float = 0.0, max_iters: int = 60, seed: int = 42):
        self.reps = reps
        self.engine = QuantumOptimizerEngine(shots=shots, noise_rate=noise_rate, seed=seed)
        self.max_iters = max_iters
        self.seed = seed

    def solve(self, hamiltonian: SparsePauliOp, num_qubits: int, offset: float = 0.0) -> Dict[str, Any]:
        t0 = time.perf_counter()
        circuit = build_vqe_ansatz(num_qubits, reps=self.reps)
        num_params = len(circuit.parameters)

        rng = np.random.RandomState(self.seed)
        init_params = rng.uniform(-np.pi, np.pi, size=num_params)

        energy_history = []

        def cost_fn(theta):
            e = self.engine.evaluate_expectation(circuit, theta, hamiltonian) + offset
            energy_history.append(float(e))
            return e

        res = minimize(
            cost_fn,
            init_params,
            method="BFGS",
            options={"maxiter": self.max_iters}
        )

        runtime_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "optimal_energy": float(res.fun),
            "optimal_params": res.x.tolist(),
            "iterations": len(energy_history),
            "energy_history": energy_history,
            "runtime_ms": runtime_ms,
        }
