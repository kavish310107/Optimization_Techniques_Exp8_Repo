"""Comprehensive Track E Experiment Runner:
1. Compares Greedy Heuristic vs Exact Integer Linear Programming (ILP via HiGHS).
2. Evaluates across three realistic university scale instances:
   - Small: 2 Cohorts, 3 Faculty, 2 Rooms, 12 Sessions, 12 Slots (3 days x 4 periods)
   - Medium: 3 Cohorts, 5 Faculty, 3 Rooms, 24 Sessions, 20 Slots (5 days x 4 periods)
   - Large: 4 Cohorts, 6 Faculty, 4 Rooms, 32 Sessions, 20 Slots (5 days x 4 periods)
3. Evaluates:
   - Schedule Feasibility (0 hard violations)
   - Unscheduled Sessions
   - Soft Constraint Penalty
   - Room Utilization (%)
   - Execution Runtime (ms)
   - Solver Status
4. Generates visual schedule grids and comparative metrics CSV tables.
"""
import os
import sys
import time
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK_E_DIR = os.path.dirname(CURR_DIR)
if TRACK_E_DIR not in sys.path:
    sys.path.insert(0, TRACK_E_DIR)

from models import generate_timetable_instance, TimetableProblem
from algorithms import GreedyTimetableScheduler, ILPTimetableScheduler
from experiments.visualization import plot_room_schedule_grid


def run_track_e_experiments(out_dir: str):
    """Run comparative benchmark suite on Greedy vs ILP."""
    print("==================================================")
    print("RUNNING TRACK E EXPERIMENTAL SUITE (UNIVERSITY TIMETABLE)")
    print(f"Results output folder: {out_dir}")
    print("==================================================")

    # 1. Define problem scale instances
    instances = [
        ("Small_Instance", {
            "num_cohorts": 2,
            "num_faculty": 3,
            "num_rooms": 2,
            "courses_per_cohort": 3,
            "sessions_per_course": 2,  # 2 * 3 * 2 = 12 sessions
            "num_days": 3,
            "periods_per_day": 4,      # 12 slots * 2 rooms = 24 room-slots capacity
            "seed": 42
        }),
        ("Medium_Instance", {
            "num_cohorts": 3,
            "num_faculty": 5,
            "num_rooms": 3,
            "courses_per_cohort": 4,
            "sessions_per_course": 2,  # 3 * 4 * 2 = 24 sessions
            "num_days": 5,
            "periods_per_day": 4,      # 20 slots * 3 rooms = 60 room-slots capacity
            "seed": 42
        }),
        ("Large_Instance", {
            "num_cohorts": 4,
            "num_faculty": 6,
            "num_rooms": 4,
            "courses_per_cohort": 4,
            "sessions_per_course": 2,  # 4 * 4 * 2 = 32 sessions
            "num_days": 5,
            "periods_per_day": 4,      # 20 slots * 4 rooms = 80 room-slots capacity
            "seed": 42
        }),
    ]

    records = []

    for name, params in instances:
        print(f"\n--- Testing Instance: {name} ---")
        problem = generate_timetable_instance(name=name, **params)
        print(f"Sessions: {problem.num_sessions}, Rooms: {problem.num_rooms}, Slots: {problem.num_slots}, Decision Vars: {problem.num_sessions * problem.num_rooms * problem.num_slots}")

        # 1. Greedy Scheduler
        greedy_sched = GreedyTimetableScheduler(problem)
        greedy_sol = greedy_sched.solve()
        print(f"[Greedy] Feasible: {greedy_sol.is_feasible}, Unscheduled: {len(greedy_sol.unscheduled_sessions)}, Soft Penalty: {greedy_sol.soft_penalty:.2f}, Utilization: {greedy_sol.room_utilization:.1f}%, Runtime: {greedy_sol.runtime_ms:.2f} ms")

        # 2. ILP Scheduler (SciPy HiGHS)
        ilp_sched = ILPTimetableScheduler(problem, time_limit_sec=40.0)
        ilp_sol = ilp_sched.solve()
        print(f"[ILP]    Feasible: {ilp_sol.is_feasible}, Unscheduled: {len(ilp_sol.unscheduled_sessions)}, Soft Penalty: {ilp_sol.soft_penalty:.2f}, Utilization: {ilp_sol.room_utilization:.1f}%, Runtime: {ilp_sol.runtime_ms:.2f} ms")

        # Record metrics
        records.append({
            "Instance": name,
            "Method": "Greedy (Difficulty-First)",
            "Total Sessions": problem.num_sessions,
            "Scheduled": len(greedy_sol.assignments),
            "Unscheduled": len(greedy_sol.unscheduled_sessions),
            "Hard Violations": greedy_sol.hard_violations,
            "Feasible": greedy_sol.is_feasible,
            "Soft Penalty": round(greedy_sol.soft_penalty, 2),
            "Room Utilization (%)": round(greedy_sol.room_utilization, 2),
            "Runtime (ms)": round(greedy_sol.runtime_ms, 2),
            "Solver Status": greedy_sol.solver_status,
        })
        records.append({
            "Instance": name,
            "Method": "ILP (SciPy HiGHS)",
            "Total Sessions": problem.num_sessions,
            "Scheduled": len(ilp_sol.assignments),
            "Unscheduled": len(ilp_sol.unscheduled_sessions),
            "Hard Violations": ilp_sol.hard_violations,
            "Feasible": ilp_sol.is_feasible,
            "Soft Penalty": round(ilp_sol.soft_penalty, 2),
            "Room Utilization (%)": round(ilp_sol.room_utilization, 2),
            "Runtime (ms)": round(ilp_sol.runtime_ms, 2),
            "Solver Status": ilp_sol.solver_status,
        })

        # Generate schedule grid plots for medium instance
        if name == "Medium_Instance":
            plot_room_schedule_grid(problem, greedy_sol, os.path.join(out_dir, "timetable_grid_greedy_medium.png"))
            plot_room_schedule_grid(problem, ilp_sol, os.path.join(out_dir, "timetable_grid_ilp_medium.png"))

    df = pd.DataFrame(records)
    csv_path = os.path.join(out_dir, "timetable_benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nBenchmark table saved to: {csv_path}")

    # Comparative Plot: Soft Penalty & Runtime
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    inst_names = [inst[0] for inst in instances]
    x = np.arange(len(inst_names))
    width = 0.35

    greedy_penalties = [df[(df["Instance"] == inst) & (df["Method"] == "Greedy (Difficulty-First)")]["Soft Penalty"].values[0] for inst in inst_names]
    ilp_penalties = [df[(df["Instance"] == inst) & (df["Method"] == "ILP (SciPy HiGHS)")]["Soft Penalty"].values[0] for inst in inst_names]

    ax1.bar(x - width/2, greedy_penalties, width, label="Greedy", color="#ff7f0e")
    ax1.bar(x + width/2, ilp_penalties, width, label="ILP (HiGHS)", color="#1f77b4")
    ax1.set_ylabel("Soft Penalty Score (Lower is Better)")
    ax1.set_title("Soft Penalty Comparison: Greedy vs ILP")
    ax1.set_xticks(x)
    ax1.set_xticklabels([i.replace("_", "\n") for i in inst_names])
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    greedy_runtimes = [df[(df["Instance"] == inst) & (df["Method"] == "Greedy (Difficulty-First)")]["Runtime (ms)"].values[0] for inst in inst_names]
    ilp_runtimes = [df[(df["Instance"] == inst) & (df["Method"] == "ILP (SciPy HiGHS)")]["Runtime (ms)"].values[0] for inst in inst_names]

    ax2.plot(inst_names, greedy_runtimes, marker="o", label="Greedy Runtime", color="#ff7f0e", linewidth=2)
    ax2.plot(inst_names, ilp_runtimes, marker="s", label="ILP Runtime", color="#1f77b4", linewidth=2)
    ax2.set_ylabel("Runtime (ms, log scale)")
    ax2.set_yscale("log")
    ax2.set_title("Runtime Comparison (Log Scale)")
    ax2.set_xticks(x)
    ax2.set_xticklabels([i.replace("_", "\n") for i in inst_names])
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "timetable_algorithm_comparison.png"), dpi=200)
    plt.close()

    return df


def main():
    out_dir = os.path.join(TRACK_E_DIR, "..", "results", "track_e")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    df = run_track_e_experiments(out_dir)
    print("\nSummary Table:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()

