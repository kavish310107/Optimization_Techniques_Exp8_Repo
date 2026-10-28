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
| **Track A** | Pending specification | TBD | Not Started |
| **Track B** | Pending specification | TBD | Not Started |
| **Track C** | Pending specification | TBD | Not Started |
| **Track D** | Pending specification | TBD | Not Started |
| **Track E** | Smart University Course Timetable Optimization | Greedy vs. Integer Linear Programming (ILP) | Pending Spec Verification |
| **Track F** | Pending specification | TBD | Not Started |
| **Track G** | Pending specification | TBD | Not Started |
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

## Execution Instructions

Each track is implemented independently within its designated folder (`track <X>/`). Refer to each track's local documentation or run tests via pytest:
```bash
pytest
```
Results, benchmark logs, and visualizations will be stored under the `results/` directory.

---

## Notes on Version Control & Workflow
- Manual commit/push workflow is maintained by the user after track review.
- Project ZIP archives are excluded via `.gitignore` to prevent recursive bundling.

