# Track F: Compiler Optimization

This directory contains the complete modular implementation, optimization pipeline, benchmarks, and validation tests for **Track F: Compiler Optimization**, in accordance with Assignment 8 requirements (Chapter 6 methods: MiniLang compiler, 4 compulsory optimizations, and a compiler decision formulated as an optimization problem solved via ILP / Greedy graph coloring).

---

## Architecture & Module Structure

```text
track F/
├── README.md                 # Track documentation, architecture, and execution instructions
├── frontend/                 # Lexical analysis and AST parsing
│   ├── ast_nodes.py          # Token definitions, Regex tokenizer, and AST dataclasses
│   ├── parser.py             # Recursive descent parser supporting arithmetic, conditionals, loops
│   └── __init__.py
├── ir/                       # Intermediate representation
│   ├── tac.py                # Linear 3-Address Code (TAC), temporaries, labels, IR generator
│   └── __init__.py
├── passes/                   # Compiler optimization passes
│   ├── optimizations.py      # Constant Folding & Propagation, Dead-Code Elimination, CSE, Strength Reduction
│   ├── register_alloc.py     # Graph Coloring Register Allocation (ILP via HiGHS vs Greedy Welsh-Powell)
│   └── __init__.py
├── codegen/                  # Code execution engine
│   ├── vm.py                 # Virtual Machine / interpreter executing TAC with register mapping
│   └── __init__.py
├── experiments/              # Benchmark runners & evaluation
│   └── runner.py             # 5 benchmark programs measuring static IR size, dynamic cycles, runtime, output equivalence
└── tests/                    # Unit testing suite
    └── test_track_f.py       # 8 unit tests (parsing, syntax error rejection, optimizations, register allocation, VM)
```

---

## Compulsory Coverage & Optimization Transformations

### 1. The Four Compulsory Optimizations (Full Credit Requirement)
1. **Constant Folding & Constant Propagation**:
   - Simplifies compile-time literal expressions ($2 \times 3 + 4 \to 10$) and propagates known variable values.
   - Clears propagation tables at basic block boundaries (labels and jumps) to ensure conservative sound semantics.
2. **Common Subexpression Elimination (CSE)**:
   - Identifies identical computations within basic blocks and reuses prior results (e.g. $a \times b$ computed once and reused across subsequent statements).
   - Accounts for commutativity on symmetric operators ($+, *, ==, !=$).
3. **Dead-Code Elimination (DCE)**:
   - Identifies and strips unused variable and temporary assignments whose destination values never affect any program output or observable behavior.
4. **Strength Reduction**:
   - Replaces computationally heavy operations with cheaper equivalents:
     - $x \times 2 \to x + x$
     - $x \times 1 \to x$
     - $x \times 0 \to 0$
     - $x + 0 \to x$
     - $x / 1 \to x$

### 2. Compiler Decision Posed as Chapter 6 Optimization
- **Register Allocation via Graph Coloring**:
  - Live ranges for variables are computed from definition to last use, extending across loop boundaries for backward branches.
  - Interference graph $G = (V, E)$ has edges between variables whose live ranges overlap.
  - Solved using:
    1. **Greedy Welsh-Powell Heuristic**: Highest degree nodes colored first.
    2. **Integer Linear Programming (ILP)**: Canonical graph coloring binary optimization solved with SciPy HiGHS backend, minimizing total registers used subject to $\sum_c x_{v, c} = 1$ and $x_{u, c} + x_{v, c} \le 1$ for all $(u, v) \in E$.

### 3. Execution & Correctness Verification
- A custom 3-Address Code Virtual Machine (`TACVirtualMachine`) executes both unoptimized and optimized code with register mappings.
- Output equivalence is checked across all benchmark programs ($100\%$ semantic preservation verified).

---

## Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track F/tests/test_track_f.py" -v
```

### Run Experimental Benchmarks & Generate Plots
```bash
python "track F/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, and comparison bar charts are saved to `results/track_f/`.

