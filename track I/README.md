# Track I: Quantum Algorithms and Quantum Machine Learning (QML)

## 1. Overview & Scope
Track I evaluates what quantum algorithms and quantum machine learning offer compared with classical computing, and rigorously analyzes their practical limitations on contemporary Noisy Intermediate-Scale Quantum (NISQ) systems and classical simulators.

As specified by **Assignment 8**:
1. **Quantum Algorithms Suite**: Hand-crafted implementations of foundational quantum algorithms using native Qiskit primitives:
   - **Deutsch-Jozsa**: Exact determination of whether a boolean function $f: \{0,1\}^n \to \{0,1\}$ is constant or balanced in a single quantum query vs. $2^{n-1}+1$ classical queries.
   - **Bernstein-Vazirani**: Determination of a hidden bitstring $s \in \{0,1\}^n$ where $f(x) = s \cdot x \pmod 2$ in 1 quantum query vs. $n$ classical queries.
   - **Grover's Search**: Quadratic amplitude amplification finding marked items in an unstructured $N = 2^n$ database using $O(\sqrt{N})$ queries vs. $O(N)$ classical linear search.
   - **Quantum Fourier Transform (QFT)**: Quantum mapping of computational states to frequency domain with gate complexity $O(n^2)$ vs. classical FFT $O(n 2^n)$.
   - **Quantum Phase Estimation (QPE)**: Eigenvalue phase estimation $\theta$ in $U |\psi\rangle = e^{2\pi i \theta} |\psi\rangle$.
   - **Shor's Period Finding**: Modular order finding $a^r \equiv 1 \pmod N$ converting integer factorization into period estimation.
2. **QML vs. Classical Comparison**:
   - Variational Quantum Classifier (VQC) with angle feature map ($\text{Ry}$ rotations) and entangling $\text{CX}$ ladders trained using analytic parameter-shift gradients.
   - Classical Baselines: Logistic Regression (linear boundary) and Multi-Layer Perceptron (MLP).
3. **Noisy Hardware Simulation & Algorithmic Limits**:
   - Depolarizing noise impact on VQC generalization.
   - Analysis of simulation wall-clock overhead, data loading bottlenecks, and barren plateaus contrasted with Track D parallel speedups.

---

## 2. Directory Structure
```
track I/
├── README.md               # Documentation and execution guide
├── src/
│   ├── algorithms.py       # Hand-crafted quantum algorithm circuits
│   └── qml_models.py       # VQC & classical ML models
├── experiments/
│   └── runner.py           # Comprehensive experiment runner & visualizer
└── tests/
    └── test_track_i.py     # Pytest automated test suite (7 tests)
```

---

## 3. Execution Instructions

### Prerequisites
Install the required packages (Python 3.10+):
```bash
pip install -r requirements.txt
```
*(Dependencies: `qiskit`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `pytest`)*

### Run Experiments & Generate Benchmarks
Execute the unified experiment runner:
```bash
python "track I/experiments/runner.py"
```
Generated artifacts will be written directly to `results/track_i/`:
- `results/track_i/quantum_algorithms_suite_results.csv`
- `results/track_i/grover_vs_classical_scaling.csv`
- `results/track_i/qml_vs_classical_results.csv`
- `results/track_i/quantum_vs_classical_qml_analysis.png`

### Run Automated Tests
```bash
pytest "track I/tests/test_track_i.py" -q
```

---

## 4. Key Empirical Findings

### A. Algorithmic Advantage vs. Simulation Reality
- **Query Complexity**: Grover's search provides quadratic query reduction: for $N=32$, Grover requires 4 oracle evaluations while classical average requires 11 queries ($2.75\times$ query speedup).
- **Wall-Clock Paradox on Simulators**: While Grover demonstrates asymptotic query superiority, executing quantum circuits on classical hardware incurs exponential statevector simulation overhead: for $N=32$, the quantum simulator takes $120.10$ ms vs. $0.02$ ms for classical search ($5,586\times$ wall-clock slowdown). True computational advantage requires physical fault-tolerant quantum hardware.

### B. QML Variational Classification
- On the non-linear two-moons classification benchmark:
  - **Classical Logistic Regression**: 86.7% accuracy ($0.009$ s training).
  - **Variational Quantum Classifier (VQC)**: 80.0% accuracy ($28.53$ s training, 10,830 circuit queries).
  - **Noise Vulnerability**: Under simulated hardware depolarizing noise, expectation amplitudes attenuate, degrading confidence margins.
- **The Data Encoding Bottleneck**: Preparing classical data into quantum states requires deep encoding circuits, offsetting computational gains unless the data itself originates from a quantum process.

