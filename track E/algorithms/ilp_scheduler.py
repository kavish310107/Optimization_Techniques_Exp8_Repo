"""Integer Linear Programming (ILP) Formulation & Solver for University Course Timetabling.

Mathematical Formulation:
-------------------------
Decision Variables:
    x_{i, r, s} in {0, 1}
    where:
        i in Sessions (1 ... N_s)
        r in Rooms (1 ... N_r)
        s in Slots (1 ... N_t)
    x_{i, r, s} = 1 if session i is assigned to room r at time slot s, 0 otherwise.

Hard Constraints:
-----------------
1. All sessions must be scheduled:
    sum_{r} sum_{s} x_{i, r, s} = 1,   forall i
    (or <= 1 with large penalty for unscheduled in partial formulation)

2. No Room Double-Booking:
    sum_{i} x_{i, r, s} <= 1,           forall r, s

3. No Faculty Double-Booking:
    sum_{i in Sessions(f)} sum_{r} x_{i, r, s} <= 1,   forall faculty f, slot s

4. No Student Cohort Double-Booking:
    sum_{i in Sessions(c)} sum_{r} x_{i, r, s} <= 1,   forall cohort c, slot s

5. Room Capacity Feasibility:
    x_{i, r, s} = 0,   forall i, r where Capacity(r) < CohortSize(i)

6. Faculty Availability:
    x_{i, r, s} = 0,   forall i in Sessions(f), r, s in Unavailable(f)

Objective Function:
-------------------
Minimize total soft constraint penalty:
    min sum_{i, r, s} C_{i, r, s} * x_{i, r, s}

where:
    C_{i, r, s} = w_undesirable * I(s is undesirable)
                + w_waste * max(0, Capacity(r) - CohortSize(i))
                + w_faculty_pref * I(s not in Preferred(f))

Solved using SciPy's HiGHS branch-and-cut solver (`scipy.optimize.milp`).
"""
import time
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import dok_matrix

from models.problem_models import TimetableProblem, ScheduledAssignment, TimetableSolution
from validator.timetable_validator import TimetableValidator


class ILPTimetableScheduler:
    """Exact Integer Linear Programming scheduler using SciPy HiGHS backend."""

    def __init__(self, problem: TimetableProblem, time_limit_sec: float = 30.0):
        self.problem = problem
        self.validator = TimetableValidator(problem)
        self.time_limit_sec = float(time_limit_sec)

    def solve(self) -> TimetableSolution:
        t0 = time.perf_counter()
        p = self.problem

        num_sess = p.num_sessions
        num_rooms = p.num_rooms
        num_slots = p.num_slots
        num_vars = num_sess * num_rooms * num_slots

        # Variable indexing helper
        def var_idx(i_idx: int, r_idx: int, s_idx: int) -> int:
            return i_idx * (num_rooms * num_slots) + r_idx * num_slots + s_idx

        # Objective vector c
        c = np.zeros(num_vars, dtype=float)
        # Bounds: default [0, 1] for binary variables
        lb = np.zeros(num_vars, dtype=float)
        ub = np.ones(num_vars, dtype=float)

        for i_idx, sess in enumerate(p.sessions):
            cohort = p.cohort_map[sess.cohort_id]
            fac = p.faculty_map[sess.faculty_id]

            for r_idx, room in enumerate(p.rooms):
                cap_waste = max(0, room.capacity - cohort.size)
                cap_feasible = (room.capacity >= cohort.size)

                for s_idx, slot in enumerate(p.slots):
                    idx = var_idx(i_idx, r_idx, s_idx)

                    # Infeasible placements enforced by setting upper bound = 0
                    if not cap_feasible or s_idx in fac.unavailable_slots:
                        ub[idx] = 0.0
                        continue

                    # Soft penalty cost
                    cost = 0.0
                    if slot.is_undesirable:
                        cost += self.validator.w_undesirable
                    cost += self.validator.w_capacity_waste * cap_waste
                    if fac.preferred_slots and s_idx not in fac.preferred_slots:
                        cost += self.validator.w_faculty_non_pref

                    c[idx] = cost

        # Constraints construction using sparse matrix
        # 1. Each session scheduled exactly once: sum_{r, s} x_{i, r, s} = 1  (N_s constraints)
        # 2. Room double-booking: sum_{i} x_{i, r, s} <= 1                    (N_r * N_s constraints)
        # 3. Faculty double-booking: sum_{i in fac} sum_{r} x_{i, r, s} <= 1 (N_f * N_s constraints)
        # 4. Cohort double-booking: sum_{i in coh} sum_{r} x_{i, r, s} <= 1  (N_c * N_s constraints)

        total_constraints = num_sess + (num_rooms * num_slots) + (len(p.faculty) * num_slots) + (len(p.cohorts) * num_slots)
        A = dok_matrix((total_constraints, num_vars), dtype=float)
        lhs = np.zeros(total_constraints, dtype=float)
        rhs = np.zeros(total_constraints, dtype=float)

        row = 0

        # 1. Exact session assignment
        for i_idx in range(num_sess):
            for r_idx in range(num_rooms):
                for s_idx in range(num_slots):
                    A[row, var_idx(i_idx, r_idx, s_idx)] = 1.0
            lhs[row] = 1.0
            rhs[row] = 1.0
            row += 1

        # 2. Room capacity / exclusivity
        for r_idx in range(num_rooms):
            for s_idx in range(num_slots):
                for i_idx in range(num_sess):
                    A[row, var_idx(i_idx, r_idx, s_idx)] = 1.0
                lhs[row] = 0.0
                rhs[row] = 1.0
                row += 1

        # 3. Faculty exclusivity
        for f in p.faculty:
            fac_sess_indices = [i for i, s in enumerate(p.sessions) if s.faculty_id == f.id]
            for s_idx in range(num_slots):
                for i_idx in fac_sess_indices:
                    for r_idx in range(num_rooms):
                        A[row, var_idx(i_idx, r_idx, s_idx)] = 1.0
                lhs[row] = 0.0
                rhs[row] = 1.0
                row += 1

        # 4. Cohort exclusivity
        for coh in p.cohorts:
            coh_sess_indices = [i for i, s in enumerate(p.sessions) if s.cohort_id == coh.id]
            for s_idx in range(num_slots):
                for i_idx in coh_sess_indices:
                    for r_idx in range(num_rooms):
                        A[row, var_idx(i_idx, r_idx, s_idx)] = 1.0
                lhs[row] = 0.0
                rhs[row] = 1.0
                row += 1

        A_csr = A.tocsr()
        constraints = LinearConstraint(A_csr, lb=lhs, ub=rhs)
        integrality = np.ones(num_vars, dtype=int)  # 1 = binary/integer
        var_bounds = Bounds(lb=lb, ub=ub)

        # Call SciPy HiGHS MILP solver
        res = milp(
            c=c,
            integrality=integrality,
            constraints=constraints,
            bounds=var_bounds,
            options={"time_limit": self.time_limit_sec}
        )

        runtime_ms = (time.perf_counter() - t0) * 1000.0

        assignments: List[ScheduledAssignment] = []
        unscheduled: List[str] = []

        if res.success and res.x is not None:
            x_sol = np.round(res.x).astype(int)
            for i_idx, sess in enumerate(p.sessions):
                scheduled = False
                for r_idx, room in enumerate(p.rooms):
                    for s_idx in range(num_slots):
                        if x_sol[var_idx(i_idx, r_idx, s_idx)] == 1:
                            assignments.append(
                                ScheduledAssignment(session_id=sess.id, room_id=room.id, slot_index=s_idx)
                            )
                            scheduled = True
                            break
                    if scheduled:
                        break
                if not scheduled:
                    unscheduled.append(sess.id)
            solver_status = "Optimal" if res.status == 0 else "Feasible"
        else:
            solver_status = f"Infeasible/Failed ({res.status_message})"
            # All sessions unscheduled if solver failed
            unscheduled = [s.id for s in p.sessions]

        # Run independent validator
        is_feas, hard_viols, soft_pen, room_util, details = self.validator.validate(assignments)

        return TimetableSolution(
            problem_name=p.name,
            method="Integer Linear Programming (SciPy HiGHS)",
            assignments=assignments,
            unscheduled_sessions=unscheduled,
            runtime_ms=runtime_ms,
            solver_status=solver_status,
            is_feasible=is_feas,
            hard_violations=hard_viols,
            soft_penalty=soft_pen,
            room_utilization=room_util,
            violation_details=details
        )
