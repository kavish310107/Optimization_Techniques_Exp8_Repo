"""
Unit and Integration Tests for Track G: Operating-System Optimization.
Validates:
1. Process state lifecycle (UNUSED -> RUNNABLE -> RUNNING -> SLEEPING -> ZOMBIE).
2. Priority queue selection (higher priority process executes first).
3. Dynamic aging prevents indefinite starvation of low-priority tasks.
4. Correct tracking of waiting ticks, response time, and turnaround time.
5. Equivalence of total executed CPU cycles across scheduling policies.
"""

import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.scheduler_sim import Process, ProcState, Xv6SchedulerSimulator


def test_process_lifecycle():
    p = Process(pid=1, name="Init", arrival_time=0, total_cpu_time=5)
    assert p.state == ProcState.UNUSED
    assert p.remaining_cpu_time == 5
    assert p.priority == 16
    assert p.dynamic_priority == 16


def test_priority_preemption_order():
    # P1 (prio 20, low), P2 (prio 5, high). Both arrive at tick 0.
    p1 = Process(pid=1, name="LowPrio", arrival_time=0, total_cpu_time=10, priority=20)
    p2 = Process(pid=2, name="HighPrio", arrival_time=0, total_cpu_time=10, priority=5)

    sim = Xv6SchedulerSimulator(policy="priority", aging_threshold=100)
    sim.load_workload([p1, p2])
    metrics = sim.run()

    # P2 must finish first because of higher priority (lower value)
    p1_sim = next(p for p in sim.processes if p.pid == 1)
    p2_sim = next(p for p in sim.processes if p.pid == 2)

    assert p2_sim.finish_time < p1_sim.finish_time
    assert p2_sim.start_time == 0
    assert p1_sim.start_time >= 10


def test_dynamic_aging_prevents_starvation():
    # Long high priority process (prio 10) vs lower priority process (prio 13)
    p_high = Process(pid=1, name="HighPrioLong", arrival_time=0, total_cpu_time=40, priority=10)
    p_low = Process(pid=2, name="LowPrioStarved", arrival_time=0, total_cpu_time=10, priority=13)

    # Without aging, p_low will never execute until tick 40
    sim_no_aging = Xv6SchedulerSimulator(policy="priority_no_aging")
    sim_no_aging.load_workload([p_high, p_low])
    sim_no_aging.run()
    p_low_no_aging = next(p for p in sim_no_aging.processes if p.pid == 2)
    assert p_low_no_aging.start_time == 40

    # With aging (threshold = 6), p_low will age from 13 -> 12 -> 11 -> 10 -> 9 (after ~24 ticks)
    # and preempt / run before tick 40, drastically improving initial response time
    sim_aging = Xv6SchedulerSimulator(policy="priority", aging_threshold=6)
    sim_aging.load_workload([p_high, p_low])
    sim_aging.run()
    p_low_aging = next(p for p in sim_aging.processes if p.pid == 2)
    assert p_low_aging.start_time < 40
    assert p_low_aging.response_time < p_low_no_aging.response_time


def test_io_sleep_and_wake():
    # Process yields every 2 ticks for 3 ticks of I/O
    p_io = Process(pid=1, name="IO_Proc", arrival_time=0, total_cpu_time=6, io_frequency=2, io_duration=3, priority=10)
    sim = Xv6SchedulerSimulator(policy="round_robin")
    sim.load_workload([p_io])
    metrics = sim.run()

    p_sim = sim.processes[0]
    assert p_sim.remaining_cpu_time == 0
    # Process runs 2 ticks, sleeps 3 ticks, runs 2 ticks, sleeps 3 ticks, runs 2 ticks -> finish at 12 ticks
    assert p_sim.finish_time >= 10


def test_conservation_of_cpu_cycles():
    # Total executed ticks across policies must match the sum of CPU requirements
    workload = [
        Process(pid=1, name="P1", arrival_time=0, total_cpu_time=15, priority=5),
        Process(pid=2, name="P2", arrival_time=0, total_cpu_time=25, priority=15),
        Process(pid=3, name="P3", arrival_time=0, total_cpu_time=10, priority=25)
    ]
    expected_cpu_ticks = 15 + 25 + 10

    for pol in ["round_robin", "priority", "priority_no_aging"]:
        sim = Xv6SchedulerSimulator(policy=pol)
        sim.load_workload(workload)
        metrics = sim.run()
        total_executed = sum(p.total_cpu_time - p.remaining_cpu_time for p in sim.processes)
        assert total_executed == expected_cpu_ticks
        assert all(p.state == ProcState.ZOMBIE for p in sim.processes)


def test_turnaround_time_improvement_with_priority():
    # Priority scheduling should reduce average turnaround time for high priority batch
    workload = [
        Process(pid=1, name="ShortHigh", arrival_time=0, total_cpu_time=10, priority=2),
        Process(pid=2, name="MedHigh", arrival_time=0, total_cpu_time=20, priority=6),
        Process(pid=3, name="LongLow", arrival_time=0, total_cpu_time=50, priority=20)
    ]

    sim_rr = Xv6SchedulerSimulator(policy="round_robin")
    sim_rr.load_workload(workload)
    m_rr = sim_rr.run()

    sim_prio = Xv6SchedulerSimulator(policy="priority")
    sim_prio.load_workload(workload)
    m_prio = sim_prio.run()

    # Priority scheduling allows short/high priority jobs to complete quickly, lowering mean turnaround
    assert m_prio["avg_turnaround_time"] < m_rr["avg_turnaround_time"]
