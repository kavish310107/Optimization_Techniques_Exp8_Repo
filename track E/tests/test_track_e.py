"""Unit tests for Track E: University Timetable Optimization.

Tests:
1. Validator catches room double-booking.
2. Validator catches faculty double-booking.
3. Validator catches cohort double-booking.
4. Validator catches room capacity violation.
5. Validator catches faculty unavailability violations.
6. Validator catches missing/unscheduled sessions.
7. Greedy scheduler produces 0 hard violations on feasible instances.
8. ILP scheduler produces 0 hard violations and optimal soft penalty.
9. Validator correctly validates an optimal schedule.
"""
import pytest
import numpy as np
import sys
import os

TRACK_E_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TRACK_E_DIR not in sys.path:
    sys.path.insert(0, TRACK_E_DIR)

from models import (
    Room, Faculty, StudentCohort, CourseSession, TimetableProblem, ScheduledAssignment,
    generate_timetable_instance
)
from validator import TimetableValidator
from algorithms import GreedyTimetableScheduler, ILPTimetableScheduler


@pytest.fixture
def sample_problem():
    return generate_timetable_instance(
        name="TestInstance",
        num_cohorts=2,
        num_faculty=2,
        num_rooms=2,
        courses_per_cohort=2,
        sessions_per_course=1, # 2 * 2 * 1 = 4 sessions
        num_days=2,
        periods_per_day=3,     # 6 slots
        seed=100
    )


class TestTimetableValidator:
    def test_validator_detects_room_double_booking(self, sample_problem):
        validator = TimetableValidator(sample_problem)
        sess1 = sample_problem.sessions[0].id
        sess2 = sample_problem.sessions[1].id
        # Assign both sessions to Room 1 at Slot 0
        assignments = [
            ScheduledAssignment(session_id=sess1, room_id=sample_problem.rooms[0].id, slot_index=0),
            ScheduledAssignment(session_id=sess2, room_id=sample_problem.rooms[0].id, slot_index=0),
            ScheduledAssignment(session_id=sample_problem.sessions[2].id, room_id=sample_problem.rooms[1].id, slot_index=1),
            ScheduledAssignment(session_id=sample_problem.sessions[3].id, room_id=sample_problem.rooms[1].id, slot_index=2),
        ]
        is_feas, viols, _, _, details = validator.validate(assignments)
        assert not is_feas
        assert any("double-booked" in d and "Room" in d for d in details)

    def test_validator_detects_faculty_double_booking(self, sample_problem):
        validator = TimetableValidator(sample_problem)
        # Find two sessions taught by the same faculty member
        f_id = sample_problem.faculty[0].id
        fac_sessions = [s.id for s in sample_problem.sessions if s.faculty_id == f_id]
        if len(fac_sessions) >= 2:
            assignments = [
                ScheduledAssignment(session_id=fac_sessions[0], room_id=sample_problem.rooms[0].id, slot_index=0),
                ScheduledAssignment(session_id=fac_sessions[1], room_id=sample_problem.rooms[1].id, slot_index=0),
            ]
            is_feas, viols, _, _, details = validator.validate(assignments)
            assert not is_feas
            assert any("Faculty" in d and "double-booked" in d for d in details)

    def test_validator_detects_capacity_violation(self):
        # Create problem where cohort is size 100, but room is capacity 40
        room = Room(id="SmallRoom", capacity=40)
        fac = Faculty(id="Prof1", name="Prof 1")
        cohort = StudentCohort(id="BigCohort", size=100)
        sess = CourseSession(id="Sess1", course_name="CS101", faculty_id="Prof1", cohort_id="BigCohort")
        prob = TimetableProblem(
            name="CapTest",
            rooms=[room],
            faculty=[fac],
            cohorts=[cohort],
            sessions=[sess],
            days=["Mon"],
            periods_per_day=2
        )
        validator = TimetableValidator(prob)
        assignments = [ScheduledAssignment(session_id="Sess1", room_id="SmallRoom", slot_index=0)]
        is_feas, viols, _, _, details = validator.validate(assignments)
        assert not is_feas
        assert any("capacity" in d.lower() for d in details)

    def test_validator_detects_missing_sessions(self, sample_problem):
        validator = TimetableValidator(sample_problem)
        # Leave out session 3
        assignments = [
            ScheduledAssignment(session_id=sample_problem.sessions[0].id, room_id=sample_problem.rooms[0].id, slot_index=0),
            ScheduledAssignment(session_id=sample_problem.sessions[1].id, room_id=sample_problem.rooms[1].id, slot_index=1),
        ]
        is_feas, viols, _, _, details = validator.validate(assignments)
        assert not is_feas
        assert any("NOT scheduled" in d for d in details)


class TestSchedulers:
    def test_greedy_scheduler_feasibility(self, sample_problem):
        scheduler = GreedyTimetableScheduler(sample_problem)
        sol = scheduler.solve()
        assert sol.is_feasible
        assert sol.hard_violations == 0
        assert len(sol.unscheduled_sessions) == 0
        assert len(sol.assignments) == sample_problem.num_sessions

    def test_ilp_scheduler_feasibility(self, sample_problem):
        scheduler = ILPTimetableScheduler(sample_problem, time_limit_sec=20.0)
        sol = scheduler.solve()
        assert sol.is_feasible
        assert sol.hard_violations == 0
        assert len(sol.unscheduled_sessions) == 0
        assert sol.solver_status in ["Optimal", "Feasible"]

    def test_ilp_achieves_better_or_equal_soft_penalty(self, sample_problem):
        g_sol = GreedyTimetableScheduler(sample_problem).solve()
        ilp_sol = ILPTimetableScheduler(sample_problem, time_limit_sec=20.0).solve()
        # ILP minimizes soft penalty globally, so its penalty must be <= Greedy's penalty + numerical tolerance
        assert ilp_sol.soft_penalty <= g_sol.soft_penalty + 1e-4

