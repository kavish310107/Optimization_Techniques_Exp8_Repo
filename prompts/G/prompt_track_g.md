# Track G Prompt: Operating-System Optimization

## Assignment Requirements (Pages 4–5 of Assignment PDF)
1. **Target**: Modify the xv6 teaching OS kernel to optimize an operating system concept.
   - Selected Optimization: **Priority-Based Process Scheduler with Dynamic Aging & Starvation Mitigation**.
   - Optional comparison baseline: Standard xv6 Round-Robin (RR) scheduling.
2. **Components**:
   - Kernel source modifications:
     - `kernel/proc.h`: Add priority (`priority`), dynamic priority (`dynamic_priority`), wait ticks, and run ticks to `struct proc`.
     - `kernel/proc.c`: Update scheduler loop to select runnable process with highest priority (lowest numerical priority value in range 0–31, where 0 is highest priority), with periodic dynamic aging of waiting processes to prevent starvation.
     - `kernel/syscall.h` & `kernel/syscall.c`: Add system calls `SYS_setpriority` and `SYS_getpinfo`.
     - `kernel/sysproc.c`: Implement `sys_setpriority` and `sys_getpinfo`.
     - `user/user.h` & `user/usys.pl`: Expose system calls to user space.
     - `user/priority_test.c`: Benchmark / verification program in user space.
   - Patch file: Generate `xv6_priority_scheduler.patch` containing standard unified diff.
   - Scheduler Simulator & Validation Harness: Since the Windows host lacks `riscv64-unknown-elf-gcc` and `qemu-system-riscv64`, implement a deterministic cycle-accurate / tick-accurate OS scheduler simulator replicating xv6 process state transitions (`UNUSED`, `SLEEPING`, `RUNNABLE`, `RUNNING`, `ZOMBIE`), timer interrupt preemptions, process yield logic, and aging.
   - Experiments: Benchmark baseline Round-Robin vs Priority with Aging across 3 workloads:
     1. CPU-bound batch compute tasks.
     2. Interactive I/O-bound burst tasks.
     3. Mixed priority heterogeneous workload.
   - Metrics: Average Turnaround Time, Average Waiting Time, Response Time, Total Context Switches, and Jain's Fairness Index.
   - Deliverables:
     - Source tree in `track G/xv6-source/`
     - Patch in `track G/patch/xv6_priority_scheduler.patch`
     - Simulator in `track G/simulator/`
     - Benchmark scripts in `track G/experiments/`
     - Tests in `track G/tests/`
     - Results & plots in `results/track_g/`
     - Documentation in `track G/README.md`, `CHECKLIST.md`, `README.md`, and `REPORT.md`.

