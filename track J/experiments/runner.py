"""
Benchmark Runner and Evaluation Pipeline for Track J: Software-Engineering Optimization.
Runs:
1. Full comparative benchmark (Naive Baseline vs Greedy vs Exact ILP vs Budgeted DP).
2. Scalability benchmark across test suite sizes N in {50, 100, 200, 400}.
3. Fault detection effectiveness (APFD curve and fault discovery timeline).
4. Generates CSV tables and publication-quality plots in results/track_j/.
"""

import os
import sys
import time
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add track J to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import generate_realistic_ci_test_suite, compute_apfd
from src.solvers import (
    solve_naive_full_suite,
    solve_greedy_additional_coverage,
    solve_ilp_minimum_cost_suite,
    solve_budgeted_dp_suite
)


def run_test_suite_minimization_benchmark() -> pd.DataFrame:
    """Evaluates optimization methods on a realistic CI regression test suite (150 tests, 80 requirements)."""
    suite = generate_realistic_ci_test_suite(num_tests=150, num_requirements=80, num_faults=25, seed=42)
    
    # 1. Naive Full Suite
    res_naive = solve_naive_full_suite(suite, seed=42)
    # 2. Greedy Additional Coverage
    res_greedy = solve_greedy_additional_coverage(suite)
    # 3. Exact ILP (SciPy HiGHS)
    res_ilp = solve_ilp_minimum_cost_suite(suite)
    # 4. Budgeted DP (Budget = 400 ms, ~10% of full suite time)
    res_dp = solve_budgeted_dp_suite(suite, time_budget_ms=400.0)
    
    rows = [res_naive, res_greedy, res_ilp, res_dp]
    records = []
    
    baseline_time = res_naive["total_duration_ms"]
    
    for r in rows:
        duration = r["total_duration_ms"]
        time_savings_pct = ((baseline_time - duration) / baseline_time) * 100.0
        records.append({
            "method": r["method"],
            "tests_selected": r["num_selected"],
            "suite_reduction_pct": ((len(suite.test_cases) - r["num_selected"]) / len(suite.test_cases)) * 100.0,
            "execution_time_ms": duration,
            "execution_time_savings_pct": time_savings_pct,
            "coverage_count": r["coverage_count"],
            "coverage_pct": r["coverage_pct"],
            "faults_detected": r["faults_detected_count"],
            "fault_retention_pct": (r["faults_detected_count"] / max(1, suite.num_faults)) * 100.0,
            "apfd_metric": r["apfd_score"],
            "optimization_solve_time_ms": r["solver_time_ms"]
        })
        
    return pd.DataFrame(records)


def run_scalability_benchmark() -> pd.DataFrame:
    """Evaluates solver runtime and reduction efficiency as test suite size scales up to 400 tests."""
    sizes = [50, 100, 200, 400]
    records = []
    
    for n in sizes:
        # Scale requirements proportionally
        n_reqs = max(20, n // 2)
        suite = generate_realistic_ci_test_suite(num_tests=n, num_requirements=n_reqs, num_faults=20, seed=42 + n)
        
        t0_naive = time.perf_counter()
        res_naive = solve_naive_full_suite(suite)
        t_naive = (time.perf_counter() - t0_naive) * 1000.0
        
        res_greedy = solve_greedy_additional_coverage(suite)
        res_ilp = solve_ilp_minimum_cost_suite(suite)
        
        records.append({
            "test_suite_size_N": n,
            "num_requirements": n_reqs,
            "naive_duration_ms": res_naive["total_duration_ms"],
            "greedy_duration_ms": res_greedy["total_duration_ms"],
            "greedy_tests_count": res_greedy["num_selected"],
            "greedy_solve_time_ms": res_greedy["solver_time_ms"],
            "ilp_duration_ms": res_ilp["total_duration_ms"],
            "ilp_tests_count": res_ilp["num_selected"],
            "ilp_solve_time_ms": res_ilp["solver_time_ms"],
            "ilp_runtime_speedup_vs_full": res_naive["total_duration_ms"] / res_ilp["total_duration_ms"]
        })
        
    return pd.DataFrame(records)


def plot_track_j_results(df_main: pd.DataFrame, df_scale: pd.DataFrame, output_dir: str):
    """Generates comparative charts illustrating suite reduction, APFD prioritization, and solver scalability."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Track J: Software-Engineering Optimization (CI Test-Suite Minimization)", fontsize=15, fontweight="bold")
    
    # Subplot 1: Test Suite Execution Time & Reduction
    ax0 = axes[0]
    methods = ["Naive Full", "Greedy", "Exact ILP", "Budgeted DP"]
    times = df_main["execution_time_ms"].values
    colors = ["#E74C3C", "#F39C12", "#2ECC71", "#3498DB"]
    bars = ax0.bar(methods, times, color=colors, edgecolor="black", alpha=0.85)
    ax0.set_ylabel("CI Test Execution Time (ms)", fontsize=11, fontweight="bold")
    ax0.set_title("Test Execution Time Reduction", fontsize=12, fontweight="bold")
    ax0.grid(axis="y", linestyle="--", alpha=0.6)
    for bar in bars:
        yval = bar.get_height()
        ax0.text(bar.get_x() + bar.get_width()/2.0, yval + 50, f"{yval:.0f} ms", ha='center', va='bottom', fontsize=9, fontweight="bold")
        
    # Subplot 2: APFD (Average Percentage of Faults Detected)
    ax1 = axes[1]
    apfd_vals = df_main["apfd_metric"].values
    bars1 = ax1.bar(methods, apfd_vals, color=colors, edgecolor="black", alpha=0.85)
    ax1.set_ylabel("APFD Score (Fault Detection Speed)", fontsize=11, fontweight="bold")
    ax1.set_title("Prioritization Effectiveness (APFD)", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, 1.05)
    ax1.grid(axis="y", linestyle="--", alpha=0.6)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f"{yval:.3f}", ha='center', va='bottom', fontsize=9, fontweight="bold")
        
    # Subplot 3: Scalability across suite sizes
    ax2 = axes[2]
    ax2.plot(df_scale["test_suite_size_N"], df_scale["naive_duration_ms"], 'o--', color="#E74C3C", label="Naive Full Suite")
    ax2.plot(df_scale["test_suite_size_N"], df_scale["greedy_duration_ms"], 's-', color="#F39C12", label="Greedy Reduced Suite")
    ax2.plot(df_scale["test_suite_size_N"], df_scale["ilp_duration_ms"], '^-', color="#2ECC71", label="Exact ILP Reduced Suite")
    ax2.set_xlabel("Original Test Suite Size ($N$)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Suite Run Duration (ms)", fontsize=11, fontweight="bold")
    ax2.set_title("Scalability vs Suite Size", fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "test_suite_minimization_analysis.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Track J optimization plot saved to: {plot_path}")


def run_all_experiments():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "results", "track_j")
    os.makedirs(out_dir, exist_ok=True)
    
    print("=================================================================")
    print("Track J: Running Test-Suite Minimization & Prioritization Benchmark")
    print("=================================================================")
    df_main = run_test_suite_minimization_benchmark()
    csv_main = os.path.join(out_dir, "test_suite_minimization_results.csv")
    df_main.to_csv(csv_main, index=False)
    print(df_main[["method", "tests_selected", "execution_time_ms", "execution_time_savings_pct", "coverage_pct", "apfd_metric"]])
    
    print("\n=================================================================")
    print("Track J: Running Scalability Benchmark across Suite Sizes")
    print("=================================================================")
    df_scale = run_scalability_benchmark()
    csv_scale = os.path.join(out_dir, "test_suite_scalability_results.csv")
    df_scale.to_csv(csv_scale, index=False)
    print(df_scale[["test_suite_size_N", "naive_duration_ms", "ilp_duration_ms", "ilp_runtime_speedup_vs_full", "ilp_solve_time_ms"]])
    
    plot_track_j_results(df_main, df_scale, out_dir)
    print("\n[Track J] All experiments completed successfully.")


if __name__ == "__main__":
    run_all_experiments()

