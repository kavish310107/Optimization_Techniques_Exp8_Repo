"""Independent Timetable Constraint Validator.

Validates any timetable schedule against ALL hard constraints and scores soft constraints
completely independently of the scheduling algorithm.
"""
from typing import List, Dict, Tuple, Set
import numpy as np
from models.problem_models import TimetableProblem, ScheduledAssignment, TimetableSolution


class TimetableValidator:
    """Independent validator checking feasibility, hard violations, and soft penalties."""

    def __init__(
        self,
        problem: TimetableProblem,
        w_undesirable: float = 10.0,
        w_capacity_waste: float = 0.1,
        w_faculty_non_pref: float = 5.0,
        w_student_gap: float = 2.0,
    ):
        self.problem = problem
        self.w_undesirable = w_undesirable
        self.w_capacity_waste = w_capacity_waste
        self.w_faculty_non_pref = w_faculty_non_pref
        self.w_student_gap = w_student_gap

    def validate(self, assignments: List[ScheduledAssignment]) -> Tuple[bool, int, float, float, List[str]]:
        """Validate schedule.
        
        Returns:
            (is_feasible, num_hard_violations, soft_penalty, room_utilization, violation_details)
        """
        violations = []
        p = self.problem

        # 1. Check all sessions exist and are scheduled at most once
        scheduled_session_ids = set()
        for a in assignments:
            if a.session_id not in p.session_map:
                violations.append(f"Hard Violation: Unknown session ID '{a.session_id}' in assignment.")
            elif a.session_id in scheduled_session_ids:
                violations.append(f"Hard Violation: Session '{a.session_id}' scheduled multiple times.")
            else:
                scheduled_session_ids.add(a.session_id)

        # 2. Check if all required sessions were scheduled
        missing_sessions = set(p.session_map.keys()) - scheduled_session_ids
        for ms in missing_sessions:
            violations.append(f"Hard Violation: Required session '{ms}' was NOT scheduled.")

        # 3. Track allocations per room-slot, faculty-slot, and cohort-slot
        room_slot_usage: Dict[Tuple[str, int], List[str]] = {}
        faculty_slot_usage: Dict[Tuple[str, int], List[str]] = {}
        cohort_slot_usage: Dict[Tuple[str, int], List[str]] = {}

        total_capacity_allocated = 0
        total_students_seated = 0

        for a in assignments:
            sess = p.session_map.get(a.session_id)
            if not sess:
                continue

            room = p.room_map.get(a.room_id)
            if not room:
                violations.append(f"Hard Violation: Unknown room ID '{a.room_id}'.")
                continue

            cohort = p.cohort_map.get(sess.cohort_id)
            fac = p.faculty_map.get(sess.faculty_id)

            # Slot bounds check
            if a.slot_index < 0 or a.slot_index >= p.num_slots:
                violations.append(f"Hard Violation: Slot index {a.slot_index} out of range [0, {p.num_slots}-1].")
                continue

            # Hard Constraint 1: Room capacity >= Cohort size
            if cohort and room.capacity < cohort.size:
                violations.append(
                    f"Hard Violation: Room '{room.id}' capacity ({room.capacity}) < "
                    f"Cohort '{cohort.id}' size ({cohort.size}) for session '{sess.id}'."
                )

            # Hard Constraint 2: Faculty availability
            if fac and a.slot_index in fac.unavailable_slots:
                violations.append(
                    f"Hard Violation: Faculty '{fac.id}' unavailable at slot {a.slot_index} for session '{sess.id}'."
                )

            # Record usages for overlap checks
            room_key = (a.room_id, a.slot_index)
            room_slot_usage.setdefault(room_key, []).append(sess.id)

            if fac:
                fac_key = (fac.id, a.slot_index)
                faculty_slot_usage.setdefault(fac_key, []).append(sess.id)

            if cohort:
                cohort_key = (cohort.id, a.slot_index)
                cohort_slot_usage.setdefault(cohort_key, []).append(sess.id)

            total_capacity_allocated += room.capacity
            if cohort:
                total_students_seated += cohort.size

        # Hard Constraint 3: Room double-booking
        for (r_id, s_idx), sess_list in room_slot_usage.items():
            if len(sess_list) > 1:
                violations.append(f"Hard Violation: Room '{r_id}' double-booked at slot {s_idx} by sessions: {sess_list}.")

        # Hard Constraint 4: Faculty double-booking
        for (f_id, s_idx), sess_list in faculty_slot_usage.items():
            if len(sess_list) > 1:
                violations.append(f"Hard Violation: Faculty '{f_id}' double-booked at slot {s_idx} by sessions: {sess_list}.")

        # Hard Constraint 5: Cohort double-booking
        for (c_id, s_idx), sess_list in cohort_slot_usage.items():
            if len(sess_list) > 1:
                violations.append(f"Hard Violation: Cohort '{c_id}' scheduled for overlapping sessions at slot {s_idx}: {sess_list}.")

        # --- Soft Constraint Penalties ---
        soft_penalty = 0.0

        for a in assignments:
            sess = p.session_map.get(a.session_id)
            if not sess:
                continue
            room = p.room_map[a.room_id]
            cohort = p.cohort_map[sess.cohort_id]
            fac = p.faculty_map[sess.faculty_id]
            slot = p.slots[a.slot_index]

            # 1. Undesirable slot penalty
            if slot.is_undesirable:
                soft_penalty += self.w_undesirable

            # 2. Capacity waste penalty (excess room capacity)
            excess_seats = max(0, room.capacity - cohort.size)
            soft_penalty += self.w_capacity_waste * excess_seats

            # 3. Faculty preference penalty (if assigned to slot outside preferred slots)
            if fac.preferred_slots and a.slot_index not in fac.preferred_slots:
                soft_penalty += self.w_faculty_non_pref

        # 4. Cohort schedule gaps within the same day
        # For each cohort and day, count empty periods between first and last scheduled session
        for c in p.cohorts:
            for day_idx, day_name in enumerate(p.days):
                day_start = day_idx * p.periods_per_day
                day_end = day_start + p.periods_per_day
                cohort_day_periods = [
                    p.slots[a.slot_index].period
                    for a in assignments
                    if p.session_map[a.session_id].cohort_id == c.id and day_start <= a.slot_index < day_end
                ]
                if len(cohort_day_periods) > 1:
                    cohort_day_periods.sort()
                    span = cohort_day_periods[-1] - cohort_day_periods[0] + 1
                    gaps = span - len(cohort_day_periods)
                    if gaps > 0:
                        soft_penalty += self.w_student_gap * gaps

        # Room utilization ratio
        room_utilization = (total_students_seated / max(1, total_capacity_allocated)) * 100.0

        num_hard_violations = len(violations)
        is_feasible = (num_hard_violations == 0)

        return is_feasible, num_hard_violations, soft_penalty, room_utilization, violations
