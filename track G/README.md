# Track G: Operating-System Optimization (xv6 Priority Scheduler with Dynamic Aging)

## 1. Overview
Track G implements an operating system kernel optimization targeting process scheduling in the **MIT xv6-riscv** teaching operating system. 

Default xv6 employs a basic **Round-Robin (RR)** scheduler where the scheduler loop scans the process table sequentially and dispatches runnable processes for a single timer tick slice without distinguishing interactive low-latency tasks from background compute-heavy batches.

In Track G, we optimize the kernel CPU scheduler by implementing:
1. **Priority Scheduling (0–31)**: Lower integer values denote higher scheduling priorities (0 = real-time / critical, 31 = lowest idle background priority).
2. **Dynamic Aging & Anti-Starvation Mechanism**: Waiting processes in the `RUNNABLE` state accumulate wait ticks; exceeding `AGING_THRESHOLD` (10 ticks) elevates their dynamic priority by 1 level towards 0, ensuring low-priority processes cannot be starved indefinitely by compute-heavy high-priority tasks.
3. **Decay Upon Execution**: Processes elevated via aging decay back to their base static priority upon receiving CPU execution.
4. **Kernel System Calls**:
   - `setpriority(int pid, int priority)` (`SYS_setpriority = 22`): Allows modifying static and dynamic process priority.
   - `getpinfo(struct pstat *st)` (`SYS_getpinfo = 23`): Extracts process accounting statistics (`priority`, `dynamic_priority`, `ticks`, `wait_ticks`, `state`).

---

## 2. Directory Structure
```
track G/
├── xv6-source/                    # Modified xv6 kernel & user space files
│   ├── kernel/
│   │   ├── proc.h                 # PCB with priority, dynamic_priority, wait_ticks
│   │   ├── proc.c                 # Priority scheduler loop with aging & setpriority
│   │   ├── pstat.h                # Process statistics tracking structure
│   │   ├── syscall.h              # Syscall IDs 22 (setpriority) and 23 (getpinfo)
│   │   └── sysproc.c              # Kernel syscall implementations
│   └── user/
│       ├── user.h                 # User space headers and prototypes
│       ├── usys.pl                # Syscall assembly generator
│       └── priority_test.c        # User space benchmark / verification utility
├── patch/
│   └── xv6_priority_scheduler.patch # Unified diff against pristine xv6-riscv
├── simulator/
│   └── scheduler_sim.py           # Cycle-accurate discrete-event xv6 scheduler simulator
├── experiments/
│   └── run_benchmarks.py          # Benchmark runner across 3 workloads
├── tests/
│   └── test_track_g.py            # Pytest suite validating state transitions & aging
└── README.md
```

---

## 3. Environment & Execution
Native compilation and execution of xv6 require `riscv64-unknown-elf-gcc` and `qemu-system-riscv64`. On systems equipped with this cross-compilation toolchain, the patch can be applied directly to a clean checkout of `xv6-riscv`:

```bash
# On Linux / WSL with RISC-V QEMU toolchain:
git clone https://github.com/mit-pdos/xv6-riscv.git
cd xv6-riscv
patch -p1 < /path/to/xv6_priority_scheduler.patch
make qemu
# In xv6 shell:
$ priority_test
```

### Reproducible Host Simulation
Because our Windows host environment lacks native RISC-V cross-compilers, a deterministic, tick-accurate discrete-event simulator (`simulator/scheduler_sim.py`) faithfully models xv6's PCB transitions (`UNUSED`, `RUNNABLE`, `RUNNING`, `SLEEPING`, `ZOMBIE`), time quantum expiration, and priority preemption.

To run the benchmarks and generate performance plots:
```bash
python "track G/experiments/run_benchmarks.py"
```

To run the verification test suite:
```bash
pytest "track G/tests/test_track_g.py"
```

---

## 4. Benchmark Results Summary
Three distinct workloads were benchmarked across 3 scheduling policies:
1. **CPU-Bound Batch**: 5 computational tasks with static priorities ranging from 4 to 28.
2. **Interactive I/O Burst**: 2 high-priority interactive tasks yielding frequently for I/O vs 2 low-priority background workers.
3. **Mixed Heterogeneous**: 6 processes with staggered arrival times, varying burst lengths, and mixed I/O frequencies.

| Workload | Scheduler Policy | Avg Turnaround (ticks) | Avg Waiting (ticks) | Avg Response (ticks) | Jain's Fairness |
|---|---|---|---|---|---|
| **CPU-Bound Batch** | Round-Robin (Default) | 190.6 | 190.6 | 2.0 | 0.983 |
| | Priority with Aging | **129.4** (-32.1%) | **129.4** (-32.1%) | 64.8 | 0.779 |
| | Priority (No Aging) | 126.0 | 126.0 | 82.0 | 0.781 |
| **Interactive I/O Burst** | Round-Robin (Default) | 136.75 | 131.75 | 1.25 | 0.866 |
| | Priority with Aging | **102.0** (-25.4%) | **97.0** (-26.4%) | 12.0 | 0.701 |
| | Priority (No Aging) | 99.5 | 94.5 | 32.25 | 0.697 |
| **Mixed Heterogeneous** | Round-Robin (Default) | 149.83 | 141.17 | 1.17 | 0.885 |
| | Priority with Aging | **116.83** (-22.0%) | **108.17** (-23.4%) | 48.5 | 0.757 |
| | Priority (No Aging) | 114.83 | 106.17 | 60.5 | 0.749 |

### Key Observations:
- **Turnaround & Waiting Time Reduction**: Prioritizing higher-urgency and shorter interactive jobs reduced mean turnaround times by **22.0% to 32.1%** compared to standard Round-Robin.
- **Starvation Mitigation**: Pure static priority scheduling without aging starved low-priority processes (e.g., initial response time of 82.0 ticks in CPU-bound batch). Enabling dynamic aging reduced response latency by **21.0%** while maintaining the throughput advantages of priority scheduling.
- **Fairness vs Priority Trade-off**: Standard Round-Robin provides superior Jain's fairness (0.88–0.98) at the cost of high latency for critical tasks; Priority scheduling achieves purposeful differentiated QoS (0.70–0.78 fairness).

