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

---

### Entry 006: Top-Level Package Relative Import Failure in Track E Modules
- **Timestamp / Phase**: Track E Implementation (Unit Test Discovery)
- **Symptom / Error Encountered**:
  `pytest "track E/tests/test_track_e.py"` failed with:
  `ImportError: attempted relative import beyond top-level package` in `validator/timetable_validator.py`.
- **Root Cause Analysis**:
  When pytest is run specifying `track E/tests/test_track_e.py`, `track E` is appended to `sys.path`. Using two-dot relative imports (`from ..models...`) inside `validator/` attempted to navigate above `track E`, which was treated as the root namespace by Python's import system.
- **Resolution / Fix Applied**:
  Standardized intra-track package imports to single-dot package references relative to `track E` root (`from models.problem_models import ...`).
- **Lesson Learned**:
  Follow standard track-root-relative package naming across all modules to preserve compatibility between standalone execution and pytest discovery.

---

### Entry 007: Register Interference Across Loops in Graph Coloring
- **Timestamp / Phase**: Track F Implementation (Register Allocation Live Range Analysis)
- **Symptom / Error Encountered**:
  Executing an optimized while-loop program in the Virtual Machine with ILP register allocation caused an infinite loop (100,000 cycles timeout) while the unoptimized code finished in 42 cycles.
- **Root Cause Analysis**:
  Simple linear-scan interval analysis `[first_seen, last_seen]` recorded `n = 5` as last seen at its definition and comparison instructions. Because `n` was not modified inside the loop body, the linear scan failed to mark `n` as interfering with temporary variables defined later in the loop body (`_t2`, `_t3`). The ILP solver assigned both `n` and `_t2` to register `R0`, causing `_t2 = fact * i` to overwrite `n = 5` with `1`, corrupting the termination condition.
- **Resolution / Fix Applied**:
  Implemented loop-aware backward branch analysis: any variable whose live range spans across a backward `JUMP` instruction has its live interval extended across the entire loop span `[loop_start, loop_end]`.
- **Lesson Learned**:
  In CFG analysis, straight-line intervals are insufficient for programs with backward branches; loop spans must expand live ranges of all loop-invariant and loop-carried variables to prevent register clobbering.


---

### Entry 008: Starvation Test Assertion Failure and Preemption Handling in xv6 Simulator
- **Timestamp / Phase**: Track G Implementation (Scheduler Dynamic Aging Unit Testing)
- **Symptom / Error Encountered**:
  `pytest "track G/tests/test_track_g.py"` failed with:
  `AssertionError: assert 40 < 40` on `p_low_aging.start_time < 40`, and `assert 50 < 50` on `p_low_aging.finish_time < p_low_no_aging.finish_time`.
- **Root Cause Analysis**:
  In the discrete-event simulator, once a process with higher static priority was dispatched, it remained running because the dispatch logic only checked runnable processes when the CPU was idle. Although the waiting low-priority process dynamically aged up towards priority 0, it could not preempt the currently executing high-priority process. Furthermore, for test processes with static priority 5 vs 25 with aging threshold 8, the low-priority process required $20 \times 8 = 160$ ticks of waiting to surpass priority 5, exceeding the total workload length of 40 ticks. Once preemption was added, the aged low-priority task ran first, but because both processes executed completely before tick 50, the completion tick of the second process remained 50.
- **Resolution / Fix Applied**:
  1. Added explicit preemption check in the simulator at timer interrupt ticks: if an aged runnable process achieves a strictly better dynamic priority than the currently running process, the CPU preempts the current process and returns it to `RUNNABLE`.
  2. Adjusted test case priorities (priority 10 vs 13, aging threshold 6) so that priority promotion occurs at tick 24, allowing the starved process to preempt and execute before tick 40.
  3. Validated response time improvement (`p_low_aging.response_time < p_low_no_aging.response_time`) rather than overall batch completion tick.
- **Lesson Learned**:
  Dynamic aging requires both priority promotion in waiting queues and preemptive rescheduling upon timer interrupt; without preemption, priority improvements remain latent until the currently executing thread voluntarily relinquishes the CPU.

### Entry 009: DBMS Indexing Trade‑off Analysis (Track H)
- **Timestamp / Phase**: Benchmark & Analysis Phase (Track H)\n- **Symptom / Observation**: Adding seven secondary indexes increased database size by 133 % and insert latency by ~16 %, but yielded query speed‑ups up to 3.6× (point‑lookup) and overall average reduction of ~25 %.\n- **Root Cause Analysis**: Indexes improve read‑heavy query performance by enabling B‑Tree lookups and covering scans, while incurring additional B‑Tree pages and write‑ahead‑log updates on INSERT/UPDATE.\n- **Resolution / Insight**: For read‑dominant workloads, the storage and write overhead is acceptable; for write‑intensive scenarios, selective indexing or partial indexes should be considered.\n- **Lesson Learned**: Empirical measurement of both read and write metrics is essential when evaluating indexing strategies, as low‑selectivity range indexes may degrade performance.

### Entry 009: DBMS Indexing Trade‑off Analysis (Track H)
- **Timestamp / Phase**: Benchmark & Analysis Phase (Track H)\n- **Symptom / Observation**: Adding seven secondary indexes increased database size by 133 % and insert latency by ~16 %, but yielded query speed‑ups up to 3.6× (point‑lookup) and overall average reduction of ~25 %.\n- **Root Cause Analysis**: Indexes improve read‑heavy query performance by enabling B‑Tree lookups and covering scans, while incurring additional B‑Tree pages and write‑ahead‑log updates on INSERT/UPDATE.\n- **Resolution / Insight**: For read‑dominant workloads, the storage and write overhead is acceptable; for write‑intensive scenarios, selective indexing or partial indexes should be considered.\n- **Lesson Learned**: Empirical measurement of both read and write metrics is essential when evaluating indexing strategies, as low‑selectivity range indexes may degrade performance.