"""Greedy heuristic scheduler for university course timetabling.

Strategy:
1. Difficulty-First Ordering (Most Constrained First):
   - Sort sessions by difficulty heuristic:
     difficulty = (cohort_size) + 10 * (number of faculty unavailable slots)
   - Sessions requiring larger rooms and busier faculty are scheduled first.
2. Best-Fit Assignment:
   - For each session, scan all (room, slot) combinations.
   - Filter out hard-violating combinations (room capacity < cohort, faculty unavailable, room/faculty/cohort already booked).
   - Among feasible combinations, score each by soft-constraint cost:
     cost = undesirable_penalty + capacity_waste + faculty_preference_penalty
   - Assign session to the minimum-cost feasible (room, slot).
3. If no feasible (room, slot) exists, record the session as unscheduled explicitly.
"""
import time
from typing import List, Dict, Tuple, Set, Optional
import numpy as np
from models.problem_models import TimetableProblem, ScheduledAssignment, TimetableSolution
from validator.timetable_validator import TimetableValidator


class GreedyTimetableScheduler:
    """Heuristic greedy scheduler with most-constrained-first session ordering."""

    def __init__(self, problem: TimetableProblem):
        self.problem = problem
        self.validator = TimetableValidator(problem)

    def solve(self) -> TimetableSolution:
        t0 = time.perf_counter()
        p = self.problem

        # 1. Sort sessions by difficulty descending
        def session_difficulty(s):
            cohort = p.cohort_map[s.cohort_id]
            fac = p.faculty_map[s.faculty_id]
            # More students = fewer matching rooms; more unavailable slots = harder to place
            return cohort.size + 15 * len(fac.unavailable_slots)

        sorted_sessions = sorted(p.sessions, key=session_difficulty, reverse=True)

        # Track resource reservations
        # (room_id, slot_idx) -> session_id
        occupied_rooms: Set[Tuple[str, int]] = set()
        # (faculty_id, slot_idx) -> session_id
        occupied_faculty: Set[Tuple[str, int]] = set()
        # (cohort_id, slot_idx) -> session_id
        occupied_cohorts: Set[Tuple[str, int]] = set()

        assignments: List[ScheduledAssignment] = []
        unscheduled: List[str] = []

        for sess in sorted_sessions:
            cohort = p.cohort_map[sess.cohort_id]
            fac = p.faculty_map[sess.faculty_id]

            best_assignment: Optional[Tuple[str, int]] = None
            best_cost = float("inf")

            # Search feasible (room, slot)
            for r in p.rooms:
                # Hard Constraint 1: Capacity
                if r.capacity < cohort.size:
                    continue

                for slot in p.slots:
                    s_idx = slot.index

                    # Hard Constraint 2: Room occupied
                    if (r.id, s_idx) in occupied_rooms:
                        continue
                    # Hard Constraint 3: Faculty occupied or unavailable
                    if (fac.id, s_idx) in occupied_faculty or s_idx in fac.unavailable_slots:
                        continue
                    # Hard Constraint 4: Cohort occupied
                    if (cohort.id, s_idx) in occupied_cohorts:
                        continue

                    # Soft constraint evaluation for this placement
                    cost = 0.0
                    # Undesirable slot
                    if slot.is_undesirable:
                        cost += self.validator.w_undesirable
                    # Capacity waste
                    cost += self.validator.w_capacity_waste * (r.capacity - cohort.size)
                    # Faculty preference
                    if fac.preferred_slots and s_idx not in fac.preferred_slots:
                        cost += self.validator.w_faculty_non_pref

                    if cost < best_cost:
                        best_cost = cost
                        best_assignment = (r.id, s_idx)

            if best_assignment is not None:
                r_id, s_idx = best_assignment
                assignments.append(ScheduledAssignment(session_id=sess.id, room_id=r_id, slot_index=s_idx))
                occupied_rooms.add((r_id, s_idx))
                occupied_faculty.add((fac.id, s_idx))
                occupied_cohorts.add((cohort.id, s_idx))
            else:
                unscheduled.append(sess.id)

        runtime_ms = (time.perf_counter() - t0) * 1000.0

        # Independent validation of the final schedule
        is_feas, hard_viols, soft_pen, room_util, details = self.validator.validate(assignments)

        status = "Feasible" if is_feas else ("Partial" if assignments else "Failed")

        return TimetableSolution(
            problem_name=p.name,
            method="Greedy (Difficulty-First)",
            assignments=assignments,
            unscheduled_sessions=unscheduled,
            runtime_ms=runtime_ms,
            solver_status=status,
            is_feasible=is_feas,
            hard_violations=hard_viols,
            soft_penalty=soft_pen,
            room_utilization=room_util,
            violation_details=details
        )
