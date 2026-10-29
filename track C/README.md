# Track C: Quantum Optimization

This directory contains the complete modular implementation, mathematical formulations, benchmarks, and validation tests for **Track C: Quantum Optimization**, in accordance with Assignment 8 requirements (Chapter 6 quantum optimization methods: QAOA, VQE, parameter-shift rule, SPSA, quantum natural gradient, and comparison against Track B classical baselines).

---

## Architecture & Module Structure

```text
track C/
├── README.md                 # Track documentation, formulations, and execution instructions
├── circuits/                 # Quantum circuits & parameterized ansatzes
│   ├── ansatz.py             # Max-Cut Ising Hamiltonian builder, QAOA circuit, VQE RY-CX ansatz
│   └── __init__.py
├── algorithms/               # Quantum optimization algorithms & gradient engines
│   ├── quantum_solvers.py    # QAOASolver, VQESolver, parameter_shift_gradient, SPSA, Fubini-Study QNG
│   └── __init__.py
├── experiments/              # Benchmark runners & empirical evaluation
│   └── runner.py             # QAOA vs Track B baseline, VQE, gradient comparisons, noise & barren plateaus
└── tests/                    # Unit testing suite
    └── test_track_c.py       # Unit tests (circuits, parameter-shift check, metric tensor, solvers)
```

---

## Compulsory Coverage & Mathematical Formulations

### 1. Quantum Approximate Optimization Algorithm (QAOA)
- **Problem Mapping**:
  Given graph $W$ from Track B, the Max-Cut cost Hamiltonian is:
  $$H_C = \sum_{i < j} \frac{w_{ij}}{2} Z_i Z_j, \quad \text{Offset} = -\frac{1}{2} \sum_{i < j} w_{ij}$$
- **Ansatz Construction**:
  $$|\psi(\gamma, \beta)\rangle = \prod_{l=1}^p e^{-i \beta_l H_M} e^{-i \gamma_l H_C} |+\rangle^{\otimes n}$$
  where $H_M = \sum_{i=1}^n X_i$ is the transverse-field mixer.
- **Hybrid Optimization Loop**:
  Parameters $(\gamma, \beta)$ are evaluated on the quantum circuit (Statevector / Shot Simulator) and updated via classical optimizer (COBYLA/BFGS).

### 2. Variational Quantum Eigensolver (VQE)
- Hardware-efficient parameterized ansatz using alternating layers of $R_y(\theta)$ single-qubit rotations and entangling $CNOT$ ladders (`build_vqe_ansatz`).
- Finds the minimum eigenvalue (ground state energy) $\min_\theta \langle\psi(\theta)| H |\psi(\theta)\rangle$.
- Matched exact diagonalization on spin chain benchmark with $0.0000$ energy error.

### 3. Quantum Gradient Strategies
- **Parameter-Shift Rule**:
  $$\frac{\partial \langle H \rangle}{\partial \theta_i} = \frac{\langle H(\theta + \frac{\pi}{2} e_i)\rangle - \langle H(\theta - \frac{\pi}{2} e_i)\rangle}{2}$$
  Exact analytical quantum gradient evaluated in $2d$ circuit queries.
- **SPSA (Simultaneous Perturbation Stochastic Approximation)**:
  Estimates gradient in only $2$ function evaluations using random Rademacher perturbations $\pm \Delta$.
- **Quantum Natural Gradient (QNG)**:
  Uses the Fubini-Study / Quantum Fisher Information metric tensor $g_{ij}(\theta) = \text{Re}\left(\langle \partial_i \psi | \partial_j \psi \rangle - \langle \partial_i \psi | \psi \rangle \langle \psi | \partial_j \psi \rangle\right)$ to perform Riemannian gradient descent $\Delta \theta = - g(\theta)^{-1} \nabla \langle H \rangle$.

### 4. Hardware Noise, Finite Shots & Barren Plateaus
- **Finite Shots**: Evaluated over 128, 512, 1024, and $\infty$ measurement shots.
- **Depolarizing Noise**: Simulated hardware depolarizing noise rates ($p \in [0.0, 0.15]$).
- **Barren Plateau Study**: Demonstrated exponential decay of gradient variance $\text{Var}[\partial_k E] \propto 2^{-n}$ across $n \in [2, 10]$ qubits.

---

## Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track C/tests/test_track_c.py" -v
```

### Run Experimental Benchmarks & Generate Plots
```bash
python "track C/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, and plots are saved to `results/track_c/`.

