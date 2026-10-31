# Optimize Anything: Optimization Techniques Assignment

A comprehensive investigation and implementation of optimization methodologies across ten tracks (Track A through Track J), exploring mathematical formulations, algorithmic implementations, and empirical benchmark comparisons.

---

## Repository Structure

```text
├── .gitattributes
├── .gitignore
├── requirements.txt
├── README.md
├── CHECKLIST.md
├── REPORT.md
├── failure_log.md
├── tool_comparison.md
├── docs/                 # Shared technical notes, mathematical formulations & documentation
├── prompts/              # Prompt history organized by track
│   ├── 00_setup/
│   ├── A/ ... J/
├── results/              # Benchmark tables, plots, and experiment artifacts
├── tools/                # Shared utilities and reusable helpers across tracks
├── track A/              # Implementation for Track A
├── track B/              # Implementation for Track B
├── track C/              # Implementation for Track C
├── track D/              # Implementation for Track D
├── track E/              # Implementation for Track E
├── track F/              # Implementation for Track F
├── track G/              # Implementation for Track G
├── track H/              # Implementation for Track H
├── track I/              # Implementation for Track I
└── track J/              # Implementation for Track J
```

---

## Track Overview

| Track | Title / Topic | Primary Algorithms | Status |
|:---:|:---|:---|:---:|
| **Track A** | Continuous Optimization (Chapter 6 methods) | GD, SGD, Momentum, NAG, AdaGrad, RMSProp, Adam, Newton, Gauss-Newton, Diag-Fisher, HVP | Completed |
| **Track B** | Discrete Optimization (Chapter 6 methods) | Greedy, Dynamic Programming, Branch-and-Bound, ILP (HiGHS), QUBO, Ising conversions | Completed |
| **Track C** | Quantum Optimization (Chapter 6 methods) | QAOA, VQE, Parameter-Shift, SPSA, QNG, Barren Plateau analysis | Completed |
| **Track D** | Submodular, Parallel & Distributed Optimization | Greedy & Lazy Greedy, Amdahl/Gustafson parallel scaling, FedAvg, MGDA & GradNorm | Completed |
| **Track E** | Main Real-Process Case Study: University Course Timetable Optimization | Greedy (Difficulty-First) vs. Exact Integer Linear Programming (SciPy HiGHS) | Completed |
| **Track F** | Compiler Optimization | MiniLang compiler, 4 optimizations (CFP, DCE, CSE, SR), ILP/Greedy Register Allocation | Completed |
| **Track G** | Operating-System Optimization | xv6 Priority Scheduler with Dynamic Aging, unified kernel patch, discrete-event OS simulator | Completed |
| **Track H** | Pending specification | TBD | Not Started |
| **Track I** | Pending specification | TBD | Not Started |
| **Track J** | Pending specification | TBD | Not Started |

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Recommended: isolated virtual environment

### Environment Setup
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Unix/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## AI Tools Register (Section 8 Disclosure)

| AI Tool / Model | Version / Interface | Tracks | Date(s) | Activities / Contributions |
|:---|:---|:---|:---|:---|
| **Gemini (Antigravity Assistant)** | Gemini 3.8 Flash (Low) | Setup, Tracks A, B, C, D, E, F | 2026-10-28 to 2026-10-31 | Architecture design, algorithm implementation, unit testing, benchmark execution, documentation |

---

## Execution Instructions

### Track A: Continuous Optimization
Run tests:
```bash
python -m pytest "track A/tests/test_track_a.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track A/experiments/runner.py"
```
Generated artifacts are saved in `results/track_a/`.

### Track B: Discrete Optimization
Run tests:
```bash
python -m pytest "track B/tests/test_track_b.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track B/experiments/runner.py"
```
Generated artifacts, CSV files, plots, and matrices ($W, Q$) are saved in `results/track_b/`.

### Track C: Quantum Optimization
Run tests:
```bash
python -m pytest "track C/tests/test_track_c.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track C/experiments/runner.py"
```
Generated artifacts, CSV files, and plots are saved in `results/track_c/`.

### Track D: Submodular, Parallel, and Distributed Optimization
Run tests:
```bash
python -m pytest "track D/tests/test_track_d.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track D/experiments/runner.py"
```
Generated artifacts, CSV files, and plots are saved in `results/track_d/`.

### Track E: Main Case Study (Smart University Course Timetable Optimization)
Run tests:
```bash
python -m pytest "track E/tests/test_track_e.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track E/experiments/runner.py"
```
Generated artifacts, CSV benchmark tables, and schedule occupancy grid plots are saved in `results/track_e/`.

### Track F: Compiler Optimization
Run tests:
```bash
python -m pytest "track F/tests/test_track_f.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track F/experiments/runner.py"
```
Generated artifacts, CSV benchmark tables, and optimization comparison bar charts are saved in `results/track_f/`.

### Track G: Operating-System Optimization
Run tests:
```bash
python -m pytest "track G/tests/test_track_g.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track G/experiments/run_benchmarks.py"
```
Generated unified kernel patch is located at `track G/patch/xv6_priority_scheduler.patch`.
Generated artifacts, CSV benchmark tables, and scheduler performance comparison bar charts are saved in `results/track_g/`.


### Track G: Operating-System Optimization
Run tests:
```bash
python -m pytest "track H/tests/test_track_h.py" -v
```
Run experimental benchmarks and generate visualizations:
```bash
python "track H/experiments/run_benchmarks.py"
```
Generated unified kernel patch is located at `track H/patch/xv6_priority_scheduler.patch`.
Generated artifacts, CSV benchmark tables, and scheduler performance comparison bar charts are saved in `results/track_H/`.
---

## Notes on Version Control & Workflow
- Manual commit/push workflow is maintained by the user after track review.
- Project ZIP archives are excluded via `.gitignore` to prevent recursive bundling.

