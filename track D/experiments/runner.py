"""Comprehensive Track D Experiment Runner:
1. Benchmark 1: Submodular Facility Location (Greedy vs Lazy Greedy vs Exact (1 - 1/e) check).
2. Benchmark 2: Parallel Program Speedup, Efficiency & Amdahl/Gustafson Modeling.
3. Benchmark 3: Distributed Federated Averaging (FedAvg vs Centralized Baseline under varying local steps).
4. Benchmark 4: Multi-Task Optimization (MGDA & GradNorm vs Equal Task Weighting).

Saves structured CSV metrics and high-resolution figures into results/track_d/.
"""
import os
import sys
import time
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK_D_DIR = os.path.dirname(CURR_DIR)
if TRACK_D_DIR not in sys.path:
    sys.path.insert(0, TRACK_D_DIR)

from submodular import (
    FacilityLocationFunction,
    greedy_submodular_selection,
    lazy_greedy_submodular_selection,
    exact_submodular_maximization,
)
from parallel import (
    ParallelOptimizationBenchmark,
    fit_amdahl_and_gustafson,
)
from distributed import (
    FederatedDataset,
    run_centralized_training,
    run_fedavg,
)
from multitask import (
    TwoTaskModel,
    run_equal_weighting_optimization,
    run_mgda_optimization,
    run_gradnorm_optimization,
)


def experiment_submodular_facility(out_dir: str) -> pd.DataFrame:
    """Benchmark 1: Submodular facility location and empirical (1 - 1/e) guarantee verification."""
    # 20 candidate facilities, 50 client locations
    rng = np.random.RandomState(42)
    n_fac = 18
    n_cli = 40
    # Euclidean distance-based utility M_ij = exp(-d_ij)
    fac_coords = rng.uniform(0, 10, size=(n_fac, 2))
    cli_coords = rng.uniform(0, 10, size=(n_cli, 2))
    dists = np.linalg.norm(fac_coords[:, np.newaxis, :] - cli_coords[np.newaxis, :, :], axis=2)
    M = np.exp(-dists / 3.0)

    func = FacilityLocationFunction(M)
    dim_returns_valid = func.check_diminishing_returns(num_checks=100)

    records = []
    # Test cardinality budget k from 1 to 5
    for k in range(1, 6):
        t0 = time.perf_counter()
        exact_S, exact_val = exact_submodular_maximization(func, k)
        exact_time = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        greedy_S, greedy_val = greedy_submodular_selection(func, k)
        greedy_time = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        lazy_S, lazy_val, lazy_evals = lazy_greedy_submodular_selection(func, k)
        lazy_time = (time.perf_counter() - t0) * 1000.0

        ratio = greedy_val / exact_val
        records.append({
            "Budget k": k,
            "Exact Value": round(exact_val, 3),
            "Greedy Value": round(greedy_val, 3),
            "Lazy Greedy Value": round(lazy_val, 3),
            "Approximation Ratio": round(ratio, 4),
            "Theoretical Bound (1 - 1/e)": 0.6321,
            "Exact Time (ms)": round(exact_time, 2),
            "Greedy Time (ms)": round(greedy_time, 2),
            "Lazy Time (ms)": round(lazy_time, 2),
            "Lazy Function Evals": lazy_evals,
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "submodular_facility_results.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(df["Budget k"], df["Exact Value"], marker="o", label="Exact Optimal $F(S^*)$", color="black")
    plt.plot(df["Budget k"], df["Greedy Value"], marker="s", label="Standard Greedy", color="#1f77b4")
    plt.plot(df["Budget k"], df["Exact Value"] * (1 - 1/np.e), linestyle="--", label="Theoretical Bound $(1 - 1/e) F^*$", color="red")
    plt.title("Submodular Facility Location: Greedy vs Exact vs $(1 - 1/e)$ Bound")
    plt.xlabel("Facility Selection Budget ($k$)")
    plt.ylabel("Coverage Utility $F(S)$")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "submodular_facility_guarantee.png"), dpi=200)
    plt.close()

    return df


def experiment_parallel_scaling(out_dir: str) -> pd.DataFrame:
    """Benchmark 2: Multi-core parallel scaling, Amdahl's Law and Gustafson's Law."""
    bench = ParallelOptimizationBenchmark(num_samples=180000, num_features=60, seed=42)

    seq_time = bench.run_sequential()
    worker_counts = [1, 2, 4]  # Up to available CPU cores
    records = []
    speedups = []

    for w in worker_counts:
        par_time, loss, _ = bench.run_parallel(num_workers=w)
        speedup = seq_time / par_time
        efficiency = speedup / w
        speedups.append(speedup)
        records.append({
            "Workers (p)": w,
            "Execution Time (ms)": round(par_time, 2),
            "Measured Speedup (S_p)": round(speedup, 3),
            "Parallel Efficiency": round(efficiency, 3),
            "Loss": round(loss, 6),
        })

    fit_params = fit_amdahl_and_gustafson(worker_counts, speedups)
    s = fit_params["serial_fraction_s"]

    # Add theoretical predictions based on fitted serial fraction s
    for r in records:
        w = r["Workers (p)"]
        r["Amdahl Speedup (Predicted)"] = round(1.0 / (s + (1.0 - s) / w), 3)
        r["Gustafson Speedup (Predicted)"] = round(s + w * (1.0 - s), 3)

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "parallel_scaling_results.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(df["Workers (p)"], df["Measured Speedup (S_p)"], marker="o", label="Measured Speedup", color="#1f77b4", linewidth=2)
    plt.plot(df["Workers (p)"], df["Amdahl Speedup (Predicted)"], linestyle="--", label=f"Amdahl's Law (s={s})", color="#2ca02c")
    plt.plot(df["Workers (p)"], df["Workers (p)"], linestyle=":", label="Ideal Linear Speedup", color="gray")
    plt.title("Parallel Optimization Speedup & Amdahl's Law Scaling")
    plt.xlabel("Number of CPU Workers (p)")
    plt.ylabel("Speedup $S_p = T_1 / T_p$")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "parallel_speedup_amdahl.png"), dpi=200)
    plt.close()

    return df


def experiment_federated_fedavg(out_dir: str) -> pd.DataFrame:
    """Benchmark 3: Distributed Federated Averaging (FedAvg) vs Centralized Training."""
    # 5 clients, non-IID local datasets
    data = FederatedDataset(num_clients=5, samples_per_client=200, dim=12, non_iid=True, seed=42)

    # 1. Centralized baseline (100 total gradient updates)
    cent_res = run_centralized_training(data, total_steps=100, lr=0.1)

    # 2. FedAvg with varying local steps E: E=1, E=5, E=10 across 20 communication rounds
    local_step_configs = [1, 5, 10]
    records = [
        {
            "Method": "Centralized Baseline",
            "Communication Rounds": 0,
            "Local Steps (E)": 0,
            "Final Loss": round(cent_res["final_loss"], 4),
            "Runtime (ms)": round(cent_res["runtime_ms"], 2),
        }
    ]

    fed_histories = {}
    for E in local_step_configs:
        fed_res = run_fedavg(data, rounds=20, local_steps=E, local_lr=0.08, seed=42)
        records.append({
            "Method": f"FedAvg (E={E})",
            "Communication Rounds": 20,
            "Local Steps (E)": E,
            "Final Loss": round(fed_res["final_loss"], 4),
            "Runtime (ms)": round(fed_res["runtime_ms"], 2),
        })
        fed_histories[f"FedAvg (E={E})"] = fed_res["loss_history"]

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "federated_fedavg_results.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    for name, hist in fed_histories.items():
        plt.plot(hist, marker="o", label=name)
    plt.axhline(y=cent_res["final_loss"], color="red", linestyle="--", label=f"Centralized Loss ({cent_res['final_loss']:.3f})")
    plt.title("Federated Averaging (FedAvg): Convergence vs Local Steps E")
    plt.xlabel("Communication Round")
    plt.ylabel("Global Logistic Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "federated_fedavg_convergence.png"), dpi=200)
    plt.close()

    return df


def experiment_multitask_optimization(out_dir: str) -> pd.DataFrame:
    """Benchmark 4: Multi-Task Optimization (MGDA vs GradNorm vs Equal Task Weighting)."""
    model = TwoTaskModel(dim=15, num_samples=250, seed=42)

    # 1. Equal Weighting
    eq_res = run_equal_weighting_optimization(model, steps=80, lr=0.04)

    # 2. MGDA (Multiple Gradient Descent Algorithm)
    mgda_res = run_mgda_optimization(model, steps=80, lr=0.04)

    # 3. GradNorm
    gn_res = run_gradnorm_optimization(model, steps=80, lr=0.04)

    records = [
        {
            "Method": "Equal Weighting (Baseline)",
            "Final Task 1 Loss": round(eq_res["final_L1"], 4),
            "Final Task 2 Loss": round(eq_res["final_L2"], 4),
            "Combined Loss (Sum)": round(eq_res["final_L1"] + eq_res["final_L2"], 4),
        },
        {
            "Method": "MGDA (Pareto Stationary)",
            "Final Task 1 Loss": round(mgda_res["final_L1"], 4),
            "Final Task 2 Loss": round(mgda_res["final_L2"], 4),
            "Combined Loss (Sum)": round(mgda_res["final_L1"] + mgda_res["final_L2"], 4),
        },
        {
            "Method": "GradNorm",
            "Final Task 1 Loss": round(gn_res["final_L1"], 4),
            "Final Task 2 Loss": round(gn_res["final_L2"], 4),
            "Combined Loss (Sum)": round(gn_res["final_L1"] + gn_res["final_L2"], 4),
        },
    ]

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "multitask_optimization_results.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(eq_res["hist_L1"], label="Equal: Task 1", linestyle="--", color="#1f77b4")
    plt.plot(eq_res["hist_L2"], label="Equal: Task 2", linestyle=":", color="#1f77b4")
    plt.plot(mgda_res["hist_L1"], label="MGDA: Task 1", color="#2ca02c")
    plt.plot(mgda_res["hist_L2"], label="MGDA: Task 2", color="#ff7f0e")
    plt.title("Multi-Task Optimization: Pareto Balancing (MGDA vs Equal Weighting)")
    plt.xlabel("Iteration")
    plt.ylabel("Individual Task Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "multitask_mgda_comparison.png"), dpi=200)
    plt.close()

    return df


def main():
    out_dir = os.path.join(TRACK_D_DIR, "..", "results", "track_d")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("==================================================")
    print("RUNNING TRACK D EXPERIMENTAL SUITE")
    print(f"Results output folder: {out_dir}")
    print("==================================================")

    print("\n[1/4] Running Submodular Facility Location (Greedy vs (1 - 1/e))...")
    df_sub = experiment_submodular_facility(out_dir)
    print(df_sub.to_string(index=False))

    print("\n[2/4] Running Multi-Core Parallel Scaling & Amdahl's Law...")
    df_par = experiment_parallel_scaling(out_dir)
    print(df_par.to_string(index=False))

    print("\n[3/4] Running Distributed Federated Averaging (FedAvg vs Centralized)...")
    df_fed = experiment_federated_fedavg(out_dir)
    print(df_fed.to_string(index=False))

    print("\n[4/4] Running Multi-Task Optimization (MGDA, GradNorm, Equal Weights)...")
    df_mt = experiment_multitask_optimization(out_dir)
    print(df_mt.to_string(index=False))

    print("\nAll Track D experiments completed successfully.")


if __name__ == "__main__":
    main()

