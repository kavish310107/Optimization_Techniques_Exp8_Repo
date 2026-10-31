# Track E Prompt Record: Smart University Course Timetable Optimization

- **Track**: Track E (Main Real-Process Case Study)
- **Date**: 2026-10-31
- **AI Tool**: Gemini (Antigravity Assistant)
- **Kind of Work**: Problem formulation, case study verification against Section 4 & 6 criteria, modular timetable model implementation, greedy heuristic, ILP solver (via SciPy HiGHS / exact MILP), independent constraint validator, benchmark experiments, visualization, testing, and documentation.

## User Prompt Excerpt:
> Implement **Track E: Smart University Course Timetable Optimization** in the existing `track E/` folder of my Optimization Techniques assignment.
> 1. Inspect the assignment and reference repository:
>    - Verify our proposed university timetable case study satisfies Track E requirements (open-domain real-process optimization, Chapter 6 methods comparison, strategy-selection table, baseline vs optimized).
>    - Stop and report if there is a mismatch. (No mismatch: Page 2 & 3 explicitly list "Transport and infrastructure: Routing, traffic management, timetabling... Other domains: education" and state students choose any domain).
> 2. Define the timetable problem: Courses/sessions, faculty, rooms with capacities, time slots/days, student cohorts.
> 3. Hard constraints (no faculty clash, no room clash, no student cohort clash, room capacity >= student cohort size, all sessions scheduled) and soft constraints (undesirable slots, student gaps, room waste, faculty preferences).
> 4. Algorithms: Greedy heuristic (difficulty-first ordering) vs. Integer Linear Programming (ILP via SciPy HiGHS / exact formulation).
> 5. Experiments: Instances of increasing scale (Small, Medium, Large); measure feasibility, violations, unscheduled sessions, soft penalty, room utilization, runtime, solver status.
> 6. Independent validator: Standalone verification testing valid schedules and deliberate injected conflicts.
> 7. Tests, visualizations (schedule grid plots), track README, and updates to shared files (CHECKLIST.md, README.md, failure_log.md, tool_comparison.md, REPORT.md).

