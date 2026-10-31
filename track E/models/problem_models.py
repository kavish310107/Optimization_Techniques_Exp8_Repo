"""Data models for University Timetable Optimization."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import numpy as np


@dataclass
class Room:
    id: str
    capacity: int
    building: str = "Main"


@dataclass
class Faculty:
    id: str
    name: str
    # Set of unavailable slot indices (e.g. {0, 1})
    unavailable_slots: Set[int] = field(default_factory=set)
    # Set of preferred slot indices (lower penalty if assigned here)
    preferred_slots: Set[int] = field(default_factory=set)


@dataclass
class StudentCohort:
    id: str
    size: int


@dataclass
class CourseSession:
    id: str                 # Unique session ID (e.g. "CS101_L1")
    course_name: str        # Course code / name
    faculty_id: str         # Instructor assigned
    cohort_id: str          # Student group attending
    duration_slots: int = 1 # Number of consecutive slots required (default 1)


@dataclass
class TimeSlot:
    index: int              # Global linear slot index: 0 ... (num_days * slots_per_day - 1)
    day: str                # e.g. "Mon", "Tue", "Wed", "Thu", "Fri"
    period: int             # Period within day: 0, 1, 2, 3...
    is_undesirable: bool = False # e.g. late Friday afternoon slot


@dataclass
class TimetableProblem:
    name: str
    rooms: List[Room]
    faculty: List[Faculty]
    cohorts: List[StudentCohort]
    sessions: List[CourseSession]
    days: List[str]
    periods_per_day: int
    slots: List[TimeSlot] = field(init=False)

    # Convenience lookups
    room_map: Dict[str, Room] = field(init=False)
    faculty_map: Dict[str, Faculty] = field(init=False)
    cohort_map: Dict[str, StudentCohort] = field(init=False)
    session_map: Dict[str, CourseSession] = field(init=False)

    def __post_init__(self):
        # Build global slots
        self.slots = []
        slot_idx = 0
        for day in self.days:
            for p in range(self.periods_per_day):
                # Friday last period or 8am can be flagged as undesirable for soft penalties
                undesirable = (day == self.days[-1] and p == self.periods_per_day - 1)
                self.slots.append(TimeSlot(index=slot_idx, day=day, period=p, is_undesirable=undesirable))
                slot_idx += 1

        self.room_map = {r.id: r for r in self.rooms}
        self.faculty_map = {f.id: f for f in self.faculty}
        self.cohort_map = {c.id: c for c in self.cohorts}
        self.session_map = {s.id: s for s in self.sessions}

    @property
    def num_slots(self) -> int:
        return len(self.slots)

    @property
    def num_rooms(self) -> int:
        return len(self.rooms)

    @property
    def num_sessions(self) -> int:
        return len(self.sessions)


@dataclass
class ScheduledAssignment:
    session_id: str
    room_id: str
    slot_index: int


@dataclass
class TimetableSolution:
    problem_name: str
    method: str
    assignments: List[ScheduledAssignment]
    unscheduled_sessions: List[str]
    runtime_ms: float
    solver_status: str
    # Feasibility metrics
    is_feasible: bool = False
    hard_violations: int = 0
    soft_penalty: float = 0.0
    room_utilization: float = 0.0
    violation_details: List[str] = field(default_factory=list)

