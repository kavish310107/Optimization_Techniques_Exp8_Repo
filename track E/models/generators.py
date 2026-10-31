"""Synthetic dataset generator for realistic university timetabling benchmarks."""
from typing import List
import numpy as np
from .problem_models import Room, Faculty, StudentCohort, CourseSession, TimetableProblem


def generate_timetable_instance(
    name: str = "University_Benchmark",
    num_cohorts: int = 4,
    num_faculty: int = 6,
    num_rooms: int = 4,
    courses_per_cohort: int = 4,
    sessions_per_course: int = 2,
    num_days: int = 5,
    periods_per_day: int = 4,
    seed: int = 42,
) -> TimetableProblem:
    """Generate a reproducible, realistic university timetabling problem instance."""
    rng = np.random.RandomState(seed)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"][:num_days]
    total_slots = len(days) * periods_per_day

    # 1. Cohorts
    cohorts = []
    cohort_sizes = [30, 45, 60, 80, 100, 120]
    for i in range(num_cohorts):
        size = cohort_sizes[i % len(cohort_sizes)]
        cohorts.append(StudentCohort(id=f"Cohort_{i+1}", size=size))

    # 2. Rooms with varying capacities
    rooms = []
    room_caps = [35, 50, 70, 90, 120, 150]
    for r in range(num_rooms):
        cap = room_caps[r % len(room_caps)]
        rooms.append(Room(id=f"Room_{r+1}", capacity=cap, building="Engineering"))

    # 3. Faculty with occasional unavailable slots and preferences
    faculty = []
    for f in range(num_faculty):
        # 1 or 2 unavailable slots randomly chosen
        unavail = set(rng.choice(total_slots, size=min(2, total_slots), replace=False).tolist())
        # 2 preferred slots
        pref_candidates = [s for s in range(total_slots) if s not in unavail]
        pref = set(rng.choice(pref_candidates, size=min(3, len(pref_candidates)), replace=False).tolist())
        faculty.append(Faculty(id=f"Prof_{f+1}", name=f"Professor {f+1}", unavailable_slots=unavail, preferred_slots=pref))

    # 4. Sessions
    sessions = []
    session_counter = 1
    for c_idx, cohort in enumerate(cohorts):
        for course_idx in range(courses_per_cohort):
            c_name = f"CS{c_idx+1}0{course_idx+1}"
            # Assign a faculty member
            assigned_fac = faculty[(c_idx * courses_per_cohort + course_idx) % num_faculty].id
            for s in range(sessions_per_course):
                sess_id = f"{c_name}_S{s+1}"
                sessions.append(CourseSession(
                    id=sess_id,
                    course_name=c_name,
                    faculty_id=assigned_fac,
                    cohort_id=cohort.id,
                    duration_slots=1
                ))
                session_counter += 1

    return TimetableProblem(
        name=name,
        rooms=rooms,
        faculty=faculty,
        cohorts=cohorts,
        sessions=sessions,
        days=days,
        periods_per_day=periods_per_day
    )

