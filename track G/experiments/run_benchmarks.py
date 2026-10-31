"""
Track G Benchmark Experiments.

Compares standard xv6 Round-Robin against Priority Scheduler with Dynamic Aging
across 3 distinct workloads:
1. CPU-Bound Batch: Long computational tasks with differing priorities.
2. Interactive I/O Burst: Mixture of short I/O-intensive and long CPU tasks.
3. Mixed Heterogeneous: Diverse burst lengths, arrival offsets, and priorities.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add simulator to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulator.scheduler_sim import Process, Xv6SchedulerSimulator


def generate_workload_cpu_bound() -> list[Process]:
    """Workload 1: Pure CPU compute tasks with distinct priority levels."""
    return [
        Process(pid=1, name="HighPrio_Batch1", arrival_time=0, total_cpu_time=40, priority=4),
        Process(pid=2, name="HighPrio_Batch2", arrival_time=0, total_cpu_time=30, priority=8),
        Process(pid=3, name="MedPrio_Batch1",  arrival_time=0, total_cpu_time=50, priority=16),
        Process(pid=4, name="LowPrio_Batch1",  arrival_time=0, total_cpu_time=60, priority=24),
        Process(pid=5, name="LowPrio_Batch2",  arrival_time=0, total_cpu_time=40, priority=28),
    ]


def generate_workload_interactive_io() -> list[Process]:
    """Workload 2: Interactive tasks with frequent I/O yields competing with background compute."""
    return [
        # Interactive tasks: high priority, frequent short I/O blocks
        Process(pid=10, name="Interactive_GUI",   arrival_time=0, total_cpu_time=20, io_frequency=4, io_duration=3, priority=2),
        Process(pid=11, name="Interactive_Shell", arrival_time=5, total_cpu_time=25, io_frequency=5, io_duration=2, priority=4),
        # Background worker tasks: lower priority, pure CPU
        Process(pid=12, name="Background_Worker1", arrival_time=0, total_cpu_time=80, io_frequency=0, io_duration=0, priority=20),
        Process(pid=13, name="Background_Worker2", arrival_time=0, total_cpu_time=70, io_frequency=0, io_duration=0, priority=22),
    ]


def generate_workload_mixed() -> list[Process]:
    """Workload 3: Mixed heterogeneous processes arriving dynamically."""
    return [
        Process(pid=20, name="Kernel_Daemon",   arrival_time=0,  total_cpu_time=15, io_frequency=3, io_duration=2, priority=0),
        Process(pid=21, name="Render_Job",      arrival_time=2,  total_cpu_time=60, io_frequency=0, io_duration=0, priority=12),
        Process(pid=22, name="Editor_UI",       arrival_time=5,  total_cpu_time=25, io_frequency=5, io_duration=4, priority=4),
        Process(pid=23, name="Compile_Worker",  arrival_time=10, total_cpu_time=50, io_frequency=0, io_duration=0, priority=16),
        Process(pid=24, name="Backup_Service",  arrival_time=15, total_cpu_time=45, io_frequency=10, io_duration=5, priority=28),
        Process(pid=25, name="Telemetry_Log",   arrival_time=20, total_cpu_time=20, io_frequency=4, io_duration=2, priority=26),
    ]


def run_all_benchmarks(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    workloads = {
        "CPU_Bound_Batch": generate_workload_cpu_bound(),
        "Interactive_IO_Burst": generate_workload_interactive_io(),
        "Mixed_Heterogeneous": generate_workload_mixed()
    }
    
    policies = ["round_robin", "priority", "priority_no_aging"]
    records = []

    for w_name, w_procs in workloads.items():
        for pol in policies:
            sim = Xv6SchedulerSimulator(policy=pol, aging_threshold=10, time_quantum=1)
            sim.load_workload(w_procs)
            metrics = sim.run()
            metrics["workload"] = w_name
            records.append(metrics)

    df = pd.DataFrame(records)
    csv_path = os.path.join(output_dir, "scheduler_benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"Benchmark results saved to: {csv_path}")

    # Plot comparisons
    plot_benchmark_results(df, output_dir)
    return df


def plot_benchmark_results(df: pd.DataFrame, output_dir: str):
    workloads = df["workload"].unique()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("xv6 Operating System Scheduler Optimization: Round-Robin vs Priority (Aging)", fontsize=16, fontweight="bold")

    metrics_to_plot = [
        ("avg_waiting_time", "Average Waiting Time (ticks)", axes[0, 0]),
        ("avg_turnaround_time", "Average Turnaround Time (ticks)", axes[0, 1]),
        ("avg_response_time", "Average Response Time (ticks)", axes[1, 0]),
        ("jains_fairness_index", "Jain's Fairness Index", axes[1, 1])
    ]

    x = np.arange(len(workloads))
    width = 0.25

    policies = ["round_robin", "priority", "priority_no_aging"]
    labels = ["Round-Robin (Default)", "Priority with Aging", "Priority (No Aging)"]
    colors = ["#4A90E2", "#50E3C2", "#E94E77"]

    for col_name, title, ax in metrics_to_plot:
        for idx, (pol, lbl, clr) in enumerate(zip(policies, labels, colors)):
            sub_df = df[df["policy"] == pol]
            vals = [sub_df[sub_df["workload"] == w][col_name].values[0] for w in workloads]
            ax.bar(x + idx * width - width, vals, width, label=lbl, color=clr, alpha=0.85, edgecolor="black")

        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(workloads, rotation=15, ha="right", fontsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        if col_name == "jains_fairness_index":
            ax.set_ylim(0, 1.05)

    axes[0, 0].legend(loc="upper left")
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "scheduler_performance.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Benchmark performance plot saved to: {plot_path}")


if __name__ == "__main__":
    output_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "results", "track_g")
    run_all_benchmarks(output_directory)

