# Track E: Smart University Course Timetable Optimization

This directory contains the complete modular implementation, mathematical formulations, benchmarks, and independent validation tests for **Track E: Main Real-Process Case Study (University Timetabling)**, in accordance with Assignment 8 requirements (Section 4 Problem-Solving Workflow, Section 5 Chapter 6 methods comparison, and Section 6 Track E specification).

---

## 1. Case Study Verification & Strategy-Selection Table

As established in Section 3 and Section 6 of the assignment, students are free to select an open-domain problem (e.g. Transport, Infrastructure, Scheduling, Education). University Course Timetabling represents a classic combinatorial scheduling challenge.

### Strategy-Selection Table
| Dimension | Specification for University Timetable Optimization |
|:---|:---|
| **Variable Type** | Discrete / Binary decision variables $x_{i, r, t} \in \{0, 1\}$ |
| **Problem Size** | Combinatorial: Up to 32 sessions, 4 rooms, 20 slots ($2,560$ decision variables; $500+$ linear constraints) |
| **Approaches Compared** | **Heuristic (Greedy Difficulty-First)** vs. **Exact (Integer Linear Programming via SciPy HiGHS)** |
| **Hardware / Target** | Standard CPU (Single process execution) |
| **Evaluation Metrics** | Feasibility (0 hard violations), Unscheduled sessions, Soft penalty, Room utilization (%), Runtime (ms) |

---

## 2. Directory Structure

```text
track E/
├── README.md                 # Track documentation and execution instructions
├── models/                   # Data models and synthetic instance generator
│   ├── problem_models.py     # Room, Faculty, StudentCohort, CourseSession, Problem, Solution
│   ├── generators.py         # Reproducible realistic university benchmark generator
│   └── __init__.py
├── validator/                # Independent constraint validator
│   ├── timetable_validator.py# Independent verification of hard & soft constraints
│   └── __init__.py
├── algorithms/               # Optimization algorithms
│   ├── greedy_scheduler.py   # Greedy most-constrained-first scheduler
│   ├── ilp_scheduler.py      # Exact ILP formulation solved via SciPy HiGHS (milp)
│   └── __init__.py
├── experiments/              # Benchmarks and visualization
│   ├── runner.py             # Small, Medium, Large benchmark comparisons
│   ├── visualization.py      # Room-versus-slot occupancy matrix plot generator
│   └── __init__.py
└── tests/                    # Unit testing suite
    └── test_track_e.py       # 7 tests (independent validator conflict catches, scheduler feasibility)
```

---

## 3. Mathematical Formulation

See detailed documentation in [`docs/track_e_formulation.md`](file:///E:/@Kavish_Data/OT_EXP8/docs/track_e_formulation.md).

### Decision Variables:
$$x_{i, r, t} \in \{0, 1\}$$
where $x_{i, r, t} = 1$ if session $i$ is assigned to room $r$ at time slot $t$.

### Hard Constraints:
1. **Exact Scheduling**: $\sum_{r} \sum_{t} x_{i, r, t} = 1, \quad \forall i$.
2. **Room Exclusivity**: $\sum_{i} x_{i, r, t} \le 1, \quad \forall r, t$.
3. **Faculty Exclusivity**: $\sum_{i \in F_f} \sum_{r} x_{i, r, t} \le 1, \quad \forall f, t$.
4. **Cohort Exclusivity**: $\sum_{i \in C_c} \sum_{r} x_{i, r, t} \le 1, \quad \forall c, t$.
5. **Room Capacity**: $x_{i, r, t} = 0, \quad \forall \text{Cap}_r < \text{Size}_{\text{Cohort}(i)}$.
6. **Faculty Availability**: $x_{i, r, t} = 0, \quad \forall t \in U_{\text{Faculty}(i)}$.

### Soft Constraints (Objective):
$$\min_x \sum_{i, r, t} C_{i, r, t} \cdot x_{i, r, t}$$
penalizing undesirable time slots, capacity waste (oversized rooms), and non-preferred faculty time slots.

---

## 4. Execution Instructions

### Run Unit Tests
```bash
python -m pytest "track E/tests/test_track_e.py" -v
```

### Run Experimental Benchmarks & Generate Plots
```bash
python "track E/experiments/runner.py"
```

All benchmark artifacts, metrics CSVs, and schedule grid occupancy plots are saved to `results/track_e/`.

