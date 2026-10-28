# Assignment Deliverables & Implementation Checklist

This checklist tracks assignment requirements, deliverable status, testing status, and completion across all shared files and individual tracks (A–J).

---

## 1. Shared Setup & Governance

- [x] Repository folder structure created (Tracks A–J with exact casing and spaces)
- [x] Shared documentation files initialized (`README.md`, `CHECKLIST.md`, `REPORT.md`, `failure_log.md`, `tool_comparison.md`)
- [x] Version control rules configured (`.gitignore`, `.gitattributes`)
- [x] Dependency specification initialized (`requirements.txt`)
- [x] Prompt records initialized under `prompts/`
- [ ] Assignment requirements document / PDF verified for all tracks

---

## 2. Track Implementation Matrix

| Track | Specification Status | Implementation Status | Test & Validation Status | Results Generated | Track Completion |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Track A** | Fully Specified (Sec. 5 & 6) | Completed | 11/11 Passed | Generated (`results/track_a/`) | 🟢 Complete |
| **Track B** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track C** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track D** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track E** | Case Study Proposed (Timetabling) | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track F** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track G** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track H** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track I** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |
| **Track J** | Pending Spec | Not Started | Not Started | Not Started | ⚪ Incomplete |

---

## 3. Sequential Progress Milestones

- [x] **Phase 0: Setup and Shared Structure**
  - Project structure matches reference organization requirements.
  - No track implementations started prior to setup sign-off and specification confirmation.
- [x] **Phase 1: Track A (Continuous Optimization)**
  - [x] First-order methods: GD, SGD, Mini-batch SGD, Momentum, NAG, AdaGrad, RMSProp, Adam.
  - [x] Second-order & curvature methods: Newton's Method with damping, Gauss-Newton for least squares.
  - [x] Curvature approximations: Empirical diagonal Fisher, Hessian-Vector Products (HVP).
  - [x] Backpropagation distinct from optimizer implemented on TwoLayerMLP.
  - [x] Objective landscapes: Strongly convex quadratic, non-convex Rosenbrock, non-convex saddle escape.
  - [x] Empirical comparisons: Convergence curves, runtime, distance to optimum, learning rate sensitivity.
  - [x] Comprehensive test suite (11 unit tests passed).
  - [x] Artifacts, tables, and plots saved to `results/track_a/`.
- [ ] **Phase 2: Track B**
- [ ] **Phase 3: Track C**
- [ ] **Phase 4: Track D**
- [ ] **Phase 5: Track E** (Verify Smart University Course Timetable Optimization against Track E requirements)
- [ ] **Phase 6: Track F**
- [ ] **Phase 7: Track G**
- [ ] **Phase 8: Track H**
- [ ] **Phase 9: Track I**
- [ ] **Phase 10: Track J**
- [ ] **Phase 11: Final Synthesis** (Consolidate REPORT.md, tool_comparison.md, failure_log.md)

