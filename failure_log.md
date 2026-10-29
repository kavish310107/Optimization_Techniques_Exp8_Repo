# Failure Log & Debugging Records

This document records meaningful AI-generated coding errors, bugs, failed approaches, debugging steps, fixes, and lessons learned throughout the lifecycle of this project.

Entries must follow the format:
- **Timestamp / Phase**
- **Symptom / Error Encountered**
- **Root Cause Analysis**
- **Resolution / Fix Applied**
- **Lesson Learned**

---

### Entry 001: PowerShell Foreach Variable Interpolation Syntax Error
- **Timestamp / Phase**: Setup Phase (Directory Initialization)
- **Symptom / Error Encountered**:
  PowerShell script execution failed with:
  `Missing variable name after foreach.`
  `Unexpected token ')' in expression or statement.`
- **Root Cause Analysis**:
  A multi-line PowerShell string passed directly to the shell without single quotes caused variable interpolation expansion issues during subshell invocation, stripping `$d` to empty text before PowerShell parsed the loop.
- **Resolution / Fix Applied**:
  Replaced the interpolated script block with a direct single-line command using native comma-separated paths:
  `New-Item -ItemType Directory -Force -Path ...`
- **Lesson Learned**:
  When driving Windows PowerShell via CLI tools, pass clean command arrays or single-quoted script blocks to avoid shell variable stripping.

---

### Entry 002: Over-aggressive Step Size Divergence in Accelerated Gradient (NAG)
- **Timestamp / Phase**: Track A Implementation (Benchmark 1 - Strongly Convex Quadratic)
- **Symptom / Error Encountered**:
  During benchmark execution on a quadratic function with Lipschitz constant $L = \lambda_{max}(Q) = 20.0$, Nesterov Accelerated Gradient (NAG) exploded with objective loss $2.76 \times 10^{32}$ at $\text{lr}=0.08$.
- **Root Cause Analysis**:
  For standard GD, stability requires $\eta < 2/L = 0.10$. However, accelerated momentum methods (NAG) have tighter stability bounds $\eta \le \frac{2(1-\beta)}{L(1+\beta)}$ to avoid resonance oscillations along high-curvature eigenspaces. At $\eta=0.08, \beta=0.8$, the amplification factor exceeded unity along the dominant eigenvector.
- **Resolution / Fix Applied**:
  Adjusted step size $\eta$ to $0.04$ ($< 1/L$), respecting acceleration stability limits, and refined NAG formulation to Sutskever's standard lookahead velocity representation. NAG then converged cleanly in 89 iterations to within $4.95 \times 10^{-7}$ of the optimum.
- **Lesson Learned**:
  Accelerated first-order methods require strictly smaller step sizes than unaccelerated GD when ill-conditioned curvature exists, emphasizing the necessity of step-size tuning.

---

### Entry 003: Relative Import Failure Beyond Top-Level Package in Test Execution
- **Timestamp / Phase**: Track B Implementation (Unit Test Setup)
- **Symptom / Error Encountered**:
  Running `pytest "track B/tests/test_track_b.py"` failed during test discovery with:
  `ImportError: attempted relative import beyond top-level package` at `from ..problems.base import DiscreteSolution`.
- **Root Cause Analysis**:
  `track B/algorithms/solvers.py` utilized a two-dot relative import (`from ..problems...`), but when pytest executed the test file directly, `track B` was added to `sys.path` as a root folder rather than a subpackage of a parent package, making a parent-level traversal invalid.
- **Resolution / Fix Applied**:
  Updated the import in `track B/algorithms/solvers.py` to `from problems.base import DiscreteSolution`, maintaining clean modular resolution compatible with both pytest runs and direct module execution.
- **Lesson Learned**:
  Inside individual track directories designed as standalone modules, keep intra-track imports relative to the track root or absolute within the track namespace.

---

### Entry 004: Missing Type Annotation and Class Import in Quantum Runner
- **Timestamp / Phase**: Track C Implementation (Experiment Runner Execution)
- **Symptom / Error Encountered**:
  Runner failed with `NameError: name 'Tuple_W_Q' is not defined` and subsequently `NameError: name 'SparsePauliOp' is not defined` in `experiment_barren_plateaus`.
- **Root Cause Analysis**:
  A typing placeholder `Tuple_W_Q` was inadvertently left in the return signature of `load_track_b_maxcut_instance`, and `SparsePauliOp` was invoked inside the barren plateau function without being imported at the top of `runner.py`.
- **Resolution / Fix Applied**:
  Corrected return type annotation to `np.ndarray` and imported `SparsePauliOp` from `qiskit.quantum_info` in `track C/experiments/runner.py`.
- **Lesson Learned**:
  Always ensure all qiskit quantum information structures are explicitly imported at module level when writing standalone experiment scripts.

---

### Entry 005: Lazy Greedy Stale Bound Key Tracking in Max-Heap Priority Queue
- **Timestamp / Phase**: Track D Implementation (Submodular Optimization)
- **Symptom / Error Encountered**:
  During early testing of Minoux's lazy greedy algorithm, item reinsertion into Python's `heapq` without updating the iteration stamp caused premature convergence and suboptimal subset selection.
- **Root Cause Analysis**:
  In submodular maximization, marginal gains $\Delta(e | S)$ can only decrease as the set $S$ expands. If a re-evaluated marginal gain is pushed back onto the priority queue without storing the current round index $t = |S|$, the algorithm cannot distinguish between an upper bound computed under the current set $S$ versus an earlier ancestor set $S' \subset S$.
- **Resolution / Fix Applied**:
  Implemented 3-tuple heap entries `(-upper_bound, item, iteration_stamp)`. An item popped from the heap is accepted only if `iteration_stamp == current_set_size`; otherwise, its marginal gain is freshly evaluated and re-pushed with `iteration_stamp = current_set_size`.
- **Lesson Learned**:
  Stale bound caching in priority queues requires explicit state-version timestamps to ensure strict mathematical equivalence to standard greedy selection.

