"""
xv6 Scheduler Simulation Engine.

Replicates the xv6 operating system kernel process scheduling subsystem:
- Process Control Block (PCB) state transitions: UNUSED -> RUNNABLE <-> RUNNING -> SLEEPING -> ZOMBIE
- Timer ticks and time slice preemptions (default 1 tick time slice in xv6)
- Round-Robin scheduling (baseline xv6)
- Priority scheduling with dynamic aging (Track G optimization)
- Workload models: CPU-bound, I/O burst, and Mixed priority hierarchies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import numpy as np


class ProcState(Enum):
    UNUSED = "UNUSED"
    RUNNABLE = "RUNNABLE"
    RUNNING = "RUNNING"
    SLEEPING = "SLEEPING"
    ZOMBIE = "ZOMBIE"


@dataclass
class Process:
    pid: int
    name: str
    arrival_time: int
    total_cpu_time: int
    io_frequency: int = 0      # 0 means pure CPU bound; k > 0 means yields to I/O every k ticks
    io_duration: int = 0       # ticks spent in SLEEPING before returning to RUNNABLE
    priority: int = 16         # static priority (0 to 31, 0 is highest)
    
    # Dynamic state
    state: ProcState = ProcState.UNUSED
    remaining_cpu_time: int = 0
    dynamic_priority: int = 16
    wait_ticks: int = 0
    current_io_wait: int = 0
    ticks_since_last_io: int = 0
    
    # Performance metrics
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    total_wait_time: int = 0
    response_time: Optional[int] = None
    context_switches: int = 0

    def __post_init__(self):
        self.remaining_cpu_time = self.total_cpu_time
        self.dynamic_priority = self.priority


class Xv6SchedulerSimulator:
    """Cycle/Tick-accurate discrete-event simulator of xv6 process scheduler."""
    
    def __init__(self, policy: str = "priority", aging_threshold: int = 10, time_quantum: int = 1):
        assert policy in ["round_robin", "priority", "priority_no_aging"]
        self.policy = policy
        self.aging_threshold = aging_threshold
        self.time_quantum = time_quantum
        
        self.current_tick: int = 0
        self.processes: List[Process] = []
        self.running_proc: Optional[Process] = None
        self.quantum_counter: int = 0
        self.rr_index: int = 0
        self.total_context_switches: int = 0
        self.timeline: List[Tuple[int, Optional[int]]] = [] # (tick, running_pid)

    def load_workload(self, processes: List[Process]):
        self.processes = [
            Process(
                pid=p.pid,
                name=p.name,
                arrival_time=p.arrival_time,
                total_cpu_time=p.total_cpu_time,
                io_frequency=p.io_frequency,
                io_duration=p.io_duration,
                priority=p.priority
            )
            for p in processes
        ]

    def run(self, max_ticks: int = 10000) -> Dict[str, float]:
        self.current_tick = 0
        self.running_proc = None
        self.quantum_counter = 0
        self.rr_index = 0
        self.total_context_switches = 0
        self.timeline = []

        while self.current_tick < max_ticks:
            # 1. Admit arriving processes
            for p in self.processes:
                if p.state == ProcState.UNUSED and p.arrival_time <= self.current_tick:
                    p.state = ProcState.RUNNABLE
                    p.wait_ticks = 0

            # 2. Advance I/O waiting for SLEEPING processes
            for p in self.processes:
                if p.state == ProcState.SLEEPING:
                    p.current_io_wait -= 1
                    if p.current_io_wait <= 0:
                        p.state = ProcState.RUNNABLE
                        p.wait_ticks = 0

            # 3. Check termination of all processes
            active = [p for p in self.processes if p.state != ProcState.ZOMBIE]
            if not active:
                break

            # 4. Check if current running process yields or finishes
            if self.running_proc is not None:
                # Check if finished
                if self.running_proc.remaining_cpu_time <= 0:
                    self.running_proc.state = ProcState.ZOMBIE
                    self.running_proc.finish_time = self.current_tick
                    self.running_proc = None
                    self.quantum_counter = 0
                # Check if initiates I/O
                elif self.running_proc.io_frequency > 0 and self.running_proc.ticks_since_last_io >= self.running_proc.io_frequency:
                    self.running_proc.state = ProcState.SLEEPING
                    self.running_proc.current_io_wait = self.running_proc.io_duration
                    self.running_proc.ticks_since_last_io = 0
                    self.running_proc = None
                    self.quantum_counter = 0
                # Check time quantum expiration or preemptive yield
                elif self.quantum_counter >= self.time_quantum:
                    self.running_proc.state = ProcState.RUNNABLE
                    # If dynamic priority was elevated, decay back towards static priority
                    if self.policy == "priority" and self.running_proc.dynamic_priority < self.running_proc.priority:
                        self.running_proc.dynamic_priority += 1
                    self.running_proc = None
                    self.quantum_counter = 0

            # 5. Aging logic for waiting RUNNABLE processes
            for p in self.processes:
                if p.state == ProcState.RUNNABLE:
                    p.wait_ticks += 1
                    p.total_wait_time += 1
                    if self.policy == "priority":
                        if p.wait_ticks >= self.aging_threshold:
                            # Promote priority towards 0
                            p.dynamic_priority = max(0, p.dynamic_priority - 1)
                            p.wait_ticks = 0

            # 6. Dispatch next process if CPU is idle
            # In xv6, timer interrupt checks if a higher priority process is runnable
            if self.running_proc is not None and self.policy == "priority":
                runnables = [p for p in self.processes if p.state == ProcState.RUNNABLE]
                if runnables:
                    min_prio_runnable = min(runnables, key=lambda p: (p.dynamic_priority, p.pid))
                    if min_prio_runnable.dynamic_priority < self.running_proc.dynamic_priority:
                        # Preempt currently running process
                        self.running_proc.state = ProcState.RUNNABLE
                        if self.running_proc.dynamic_priority < self.running_proc.priority:
                            self.running_proc.dynamic_priority += 1
                        self.running_proc = None
                        self.quantum_counter = 0
            runnables = [p for p in self.processes if p.state == ProcState.RUNNABLE]
            if self.running_proc is None and runnables:
                next_proc = None
                if self.policy == "round_robin":
                    # Circular search in process table (standard xv6 scheduler)
                    n = len(self.processes)
                    for offset in range(n):
                        idx = (self.rr_index + offset) % n
                        cand = self.processes[idx]
                        if cand.state == ProcState.RUNNABLE:
                            next_proc = cand
                            self.rr_index = (idx + 1) % n
                            break
                elif self.policy in ["priority", "priority_no_aging"]:
                    # Select minimum dynamic priority value (0 is highest priority)
                    # Tie-break by arrival time / PID
                    next_proc = min(runnables, key=lambda p: (p.dynamic_priority if self.policy == "priority" else p.priority, p.pid))
                
                if next_proc is not None:
                    next_proc.state = ProcState.RUNNING
                    next_proc.wait_ticks = 0
                    next_proc.context_switches += 1
                    self.total_context_switches += 1
                    if next_proc.start_time is None:
                        next_proc.start_time = self.current_tick
                        next_proc.response_time = self.current_tick - next_proc.arrival_time
                    self.running_proc = next_proc
                    self.quantum_counter = 0

            # 7. Execute 1 tick on CPU
            if self.running_proc is not None:
                self.running_proc.remaining_cpu_time -= 1
                self.running_proc.ticks_since_last_io += 1
                self.quantum_counter += 1
                self.timeline.append((self.current_tick, self.running_proc.pid))
            else:
                self.timeline.append((self.current_tick, None))

            self.current_tick += 1

        # Post-simulation cleanup for any process finishing at the final tick
        if self.running_proc is not None and self.running_proc.remaining_cpu_time <= 0:
            self.running_proc.state = ProcState.ZOMBIE
            self.running_proc.finish_time = self.current_tick

        return self.compute_metrics()

    def compute_metrics(self) -> Dict[str, float]:
        n = len(self.processes)
        if n == 0:
            return {}

        turnaround_times = []
        waiting_times = []
        response_times = []

        for p in self.processes:
            finish = p.finish_time if p.finish_time is not None else self.current_tick
            tt = finish - p.arrival_time
            turnaround_times.append(tt)
            waiting_times.append(p.total_wait_time)
            resp = p.response_time if p.response_time is not None else tt
            response_times.append(resp)

        # Jain's Fairness Index for turnaround times
        # J = (sum x_i)^2 / (n * sum x_i^2)
        tt_arr = np.array(turnaround_times, dtype=float)
        jain_fairness = (np.sum(tt_arr) ** 2) / (n * np.sum(tt_arr ** 2)) if np.sum(tt_arr ** 2) > 0 else 1.0

        return {
            "policy": self.policy,
            "total_ticks": float(self.current_tick),
            "total_context_switches": float(self.total_context_switches),
            "avg_turnaround_time": float(np.mean(turnaround_times)),
            "std_turnaround_time": float(np.std(turnaround_times)),
            "avg_waiting_time": float(np.mean(waiting_times)),
            "std_waiting_time": float(np.std(waiting_times)),
            "avg_response_time": float(np.mean(response_times)),
            "std_response_time": float(np.std(response_times)),
            "jains_fairness_index": float(jain_fairness)
        }
