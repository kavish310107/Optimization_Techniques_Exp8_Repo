# Track E Mathematical Formulation: Smart University Course Timetable Optimization

## 1. Problem Description & Real-Process Motivation
University timetable construction is an NP-hard combinatorial scheduling challenge in education and campus infrastructure. Manual scheduling or ad-hoc assignment leads to room capacity mismatches, student schedule fragmentation, faculty availability conflicts, and room double-booking.

## 2. Sets and Indices
- $I = \{1, \dots, N_s\}$: Set of course sessions to schedule.
- $R = \{1, \dots, N_r\}$: Set of available classrooms.
- $T = \{1, \dots, N_t\}$: Set of available time slots across all days ($N_t = \text{days} \times \text{periods}$).
- $F = \{1, \dots, N_f\}$: Set of faculty instructors.
- $C = \{1, \dots, N_c\}$: Set of student cohorts.

## 3. Parameters
- $\text{Cap}_r$: Seating capacity of room $r$.
- $\text{Size}_c$: Student enrollment in cohort $c$.
- $\text{Faculty}(i) \in F$: Faculty assigned to session $i$.
- $\text{Cohort}(i) \in C$: Student cohort attending session $i$.
- $U_f \subseteq T$: Unavailable time slots for faculty $f$.
- $P_f \subseteq T$: Preferred time slots for faculty $f$.
- $U_{\text{slot}} \subseteq T$: Undesirable slots (e.g. late Friday periods).

## 4. Decision Variables
Binary decision variables:
$$x_{i, r, t} \in \{0, 1\} \quad \forall i \in I, r \in R, t \in T$$
where $x_{i, r, t} = 1$ if session $i$ is assigned to room $r$ at slot $t$, and $0$ otherwise.

## 5. Hard Constraints (Mandatory for Feasibility)

### 5.1 Exact Session Scheduling
Every required session must be assigned to exactly one room and time slot:
$$\sum_{r \in R} \sum_{t \in T} x_{i, r, t} = 1 \quad \forall i \in I$$

### 5.2 Room Exclusivity (No Double-Booking)
At most one session may occupy any room at any given time slot:
$$\sum_{i \in I} x_{i, r, t} \le 1 \quad \forall r \in R, t \in T$$

### 5.3 Faculty Exclusivity (No Overlapping Teaching)
A faculty instructor cannot teach multiple sessions at the same slot:
$$\sum_{i \in I : \text{Faculty}(i) = f} \sum_{r \in R} x_{i, r, t} \le 1 \quad \forall f \in F, t \in T$$

### 5.4 Cohort Exclusivity (No Overlapping Attendance)
A student cohort cannot attend multiple lectures at the same slot:
$$\sum_{i \in I : \text{Cohort}(i) = c} \sum_{r \in R} x_{i, r, t} \le 1 \quad \forall c \in C, t \in T$$

### 5.5 Room Capacity Feasibility
Sessions cannot be assigned to rooms with insufficient capacity:
$$x_{i, r, t} = 0 \quad \forall i \in I, r \in R, t \in T \quad \text{where } \text{Cap}_r < \text{Size}_{\text{Cohort}(i)}$$

### 5.6 Faculty Availability
Faculty cannot be scheduled during declared unavailable slots:
$$x_{i, r, t} = 0 \quad \forall i \in I, r \in R, t \in U_{\text{Faculty}(i)}$$

## 6. Objective Function (Soft Constraint Minimization)
Minimize the weighted sum of scheduling preferences and operational waste:
$$\min_{x} \sum_{i \in I} \sum_{r \in R} \sum_{t \in T} C_{i, r, t} \cdot x_{i, r, t}$$
where:
$$C_{i, r, t} = w_{\text{undesirable}} \cdot \mathbb{I}(t \in U_{\text{slot}}) + w_{\text{waste}} \cdot \max(0, \text{Cap}_r - \text{Size}_{\text{Cohort}(i)}) + w_{\text{pref}} \cdot \mathbb{I}(t \notin P_{\text{Faculty}(i)})$$

## 7. Algorithms Evaluated
1. **Greedy Heuristic (Most Constrained First)**: Orders sessions descending by difficulty ($\text{Size}_c + 15 \times |U_f|$); performs greedy local best-fit assignment.
2. **Integer Linear Programming (ILP)**: Canonical branch-and-cut optimization using SciPy's HiGHS solver backend, producing globally optimal soft-penalty assignments subject to all hard constraints.

