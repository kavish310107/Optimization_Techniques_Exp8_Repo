"""Visualization tools for university timetables."""
import os
from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np

from models.problem_models import TimetableProblem, TimetableSolution


def plot_room_schedule_grid(problem: TimetableProblem, solution: TimetableSolution, out_path: str):
    """Render a visual Room vs Time-Slot schedule occupancy matrix."""
    num_rooms = problem.num_rooms
    num_slots = problem.num_slots

    grid = np.zeros((num_rooms, num_slots))
    label_grid = [["" for _ in range(num_slots)] for _ in range(num_rooms)]

    room_idx_map = {r.id: i for i, r in enumerate(problem.rooms)}

    for a in solution.assignments:
        r_i = room_idx_map.get(a.room_id)
        s_i = a.slot_index
        if r_i is not None and 0 <= s_i < num_slots:
            grid[r_i, s_i] = 1.0
            label_grid[r_i][s_i] = a.session_id

    fig, ax = plt.subplots(figsize=(max(10, num_slots * 0.8), max(5, num_rooms * 0.9)))
    cax = ax.imshow(grid, cmap="Blues", aspect="auto", vmin=0, vmax=1.5)

    # Labels
    ax.set_yticks(np.arange(num_rooms))
    ax.set_yticklabels([f"{r.id} (Cap: {r.capacity})" for r in problem.rooms])

    slot_labels = [f"{s.day}\nP{s.period+1}" for s in problem.slots]
    ax.set_xticks(np.arange(num_slots))
    ax.set_xticklabels(slot_labels, rotation=45, ha="right", fontsize=8)

    # Add text overlay
    for r in range(num_rooms):
        for s in range(num_slots):
            txt = label_grid[r][s]
            if txt:
                ax.text(s, r, txt, ha="center", va="center", color="navy", fontsize=7, weight="bold")

    plt.title(f"Timetable Schedule Occupancy: {solution.method}\n({problem.name} - Feasible: {solution.is_feasible}, Soft Penalty: {solution.soft_penalty:.1f})")
    plt.xlabel("Day & Time Period")
    plt.ylabel("Assigned Classroom")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
