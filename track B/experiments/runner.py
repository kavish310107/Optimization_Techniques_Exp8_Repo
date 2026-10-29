"""Comprehensive Track B Experiment Runner:
1. Benchmark 1: Exact vs Heuristic on 0-1 Knapsack (Greedy vs DP vs B&B vs ILP).
2. Benchmark 2: Scalability Benchmark (Runtime vs Number of Items N).
3. Benchmark 3: Max-Cut QUBO & Ising Classical Baseline (Greedy vs Annealing vs Exact Ground State).
4. Benchmark 4: QUBO Penalty Term Formulations (Knapsack capacity constraint penalty tuning).

Saves CSV metrics and high-resolution comparison plots into results/track_b/.
"""
import os
import sys
import time
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK_B_DIR = os.path.dirname(CURR_DIR)
if TRACK_B_DIR not in sys.path:
    sys.path.insert(0, TRACK_B_DIR)

from problems import KnapsackProblem, MaxCutProblem
from algorithms import (
    GreedyKnapsack,
    DynamicProgrammingKnapsack,
    BranchAndBoundKnapsack,
    ILPKnapsack,
    GreedyMaxCut,
    SimulatedAnnealingQUBO,
    ClassicalExactIsingSolver,
)


def experiment_knapsack_comparison(out_dir: str) -> pd.DataFrame:
    """Benchmark 1: Fair comparison on standard 0-1 Knapsack instance."""
    # Classical standard benchmark instance: 15 items with uncorrelated values and weights
    rng = np.random.RandomState(42)
    n = 15
    values = rng.randint(20, 100, size=n).astype(float)
    weights = rng.randint(10, 50, size=n).astype(float)
    capacity = float(np.sum(weights) * 0.45)  # 45% of total weight

    prob = KnapsackProblem(values=values, weights=weights, capacity=capacity, name="BenchmarkKnapsack_15")

    solvers = [
        ("Greedy (Density)", GreedyKnapsack()),
        ("Dynamic Programming", DynamicProgrammingKnapsack()),
        ("Branch and Bound", BranchAndBoundKnapsack()),
        ("ILP (SciPy HiGHS)", ILPKnapsack()),
    ]

    records = []
    # Optimal value known from ILP/DP
    exact_sol = ILPKnapsack().solve(prob)
    opt_val = exact_sol.objective_value

    for name, solver in solvers:
        sol = solver.solve(prob)
        gap = ((opt_val - sol.objective_value) / opt_val) * 100.0
        records.append({
            "Method": name,
            "Objective Value": sol.objective_value,
            "Feasible": sol.feasible,
            "Optimality Gap (%)": round(gap, 2),
            "Runtime (ms)": round(sol.runtime_ms, 3),
            "Items Selected": int(np.sum(sol.variables)),
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "knapsack_methods_comparison.csv"), index=False)

    # Bar chart comparison
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    x_pos = np.arange(len(df))
    bars = ax1.bar(x_pos - 0.2, df["Objective Value"], width=0.4, label="Objective Value", color="#1f77b4")
    ax1.set_ylabel("Total Knapsack Value", color="#1f77b4")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(df["Method"], rotation=15)

    ax2 = ax1.twinx()
    ax2.plot(x_pos + 0.2, df["Runtime (ms)"], color="#d62728", marker="o", linewidth=2, label="Runtime (ms)")
    ax2.set_ylabel("Runtime (ms, log scale)", color="#d62728")
    ax2.set_yscale("log")

    plt.title("Knapsack: Greedy vs Dynamic Programming vs Branch-and-Bound vs ILP")
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, "knapsack_methods_comparison.png"), dpi=200)
    plt.close()

    return df


def experiment_scalability(out_dir: str) -> pd.DataFrame:
    """Benchmark 2: Scalability as problem size N grows."""
    n_sizes = [10, 15, 20, 25, 30, 40, 50, 75, 100]
    rng = np.random.RandomState(123)

    records = []

    for n in n_sizes:
        v = rng.randint(15, 100, size=n).astype(float)
        w = rng.randint(10, 50, size=n).astype(float)
        cap = float(np.sum(w) * 0.40)
        prob = KnapsackProblem(values=v, weights=w, capacity=cap)

        # Greedy
        g_sol = GreedyKnapsack().solve(prob)
        records.append({"N": n, "Method": "Greedy", "Runtime (ms)": g_sol.runtime_ms, "Value": g_sol.objective_value})

        # ILP (HiGHS)
        ilp_sol = ILPKnapsack().solve(prob)
        records.append({"N": n, "Method": "ILP (HiGHS)", "Runtime (ms)": ilp_sol.runtime_ms, "Value": ilp_sol.objective_value})

        # DP (pseudo-polynomial)
        dp_sol = DynamicProgrammingKnapsack().solve(prob)
        records.append({"N": n, "Method": "Dynamic Programming", "Runtime (ms)": dp_sol.runtime_ms, "Value": dp_sol.objective_value})

        # Branch and Bound (NP-hard worst case: run up to n=25 to demonstrate exponential blowup)
        if n <= 25:
            bb_sol = BranchAndBoundKnapsack().solve(prob)
            records.append({"N": n, "Method": "Branch and Bound", "Runtime (ms)": bb_sol.runtime_ms, "Value": bb_sol.objective_value})

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "scalability_benchmark.csv"), index=False)

    plt.figure(figsize=(9, 5))
    for m in ["Greedy", "ILP (HiGHS)", "Dynamic Programming", "Branch and Bound"]:
        sub = df[df["Method"] == m]
        plt.plot(sub["N"], sub["Runtime (ms)"], marker="o", label=m)

    plt.yscale("log")
    plt.title("Discrete Scalability: Runtime vs Problem Dimension N")
    plt.xlabel("Number of Items (N)")
    plt.ylabel("Execution Time (ms, log scale)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "scalability_runtime.png"), dpi=200)
    plt.close()

    return df


def experiment_maxcut_qubo_ising(out_dir: str) -> pd.DataFrame:
    """Benchmark 3: Max-Cut formulated as QUBO and Ising model (Classical baseline for Track C QAOA)."""
    # 8-node regular / random graph instance
    rng = np.random.RandomState(99)
    n = 8
    # Symmetric weighted adjacency matrix
    raw_W = rng.randint(1, 10, size=(n, n)).astype(float)
    W = np.triu(raw_W, 1) + np.triu(raw_W, 1).T
    maxcut_prob = MaxCutProblem(adjacency_matrix=W, name="MaxCut_8Node")

    # 1. Exact Classical Ground State
    exact_solver = ClassicalExactIsingSolver()
    exact_sol = exact_solver.solve(maxcut_prob)
    max_cut = exact_sol.objective_value
    ground_energy = exact_sol.extra["ground_state_energy"]

    # 2. Greedy Partition Heuristic
    greedy_solver = GreedyMaxCut()
    greedy_sol = greedy_solver.solve(maxcut_prob)

    # 3. Simulated Annealing on QUBO formulation
    Q, offset = maxcut_prob.to_qubo()
    sa_solver = SimulatedAnnealingQUBO(steps_per_t=100, seed=42)
    sa_sol = sa_solver.solve(Q, offset)
    # Recover cut from SA binary solution
    sa_cut = maxcut_prob.evaluate_cut(sa_sol.variables)

    # Convert binary to Ising spin and verify Hamiltonian energy
    greedy_spins = maxcut_prob.binary_to_spin(greedy_sol.variables)
    greedy_energy = maxcut_prob.evaluate_energy(greedy_spins)

    sa_spins = maxcut_prob.binary_to_spin(sa_sol.variables)
    sa_energy = maxcut_prob.evaluate_energy(sa_spins)

    records = [
        {
            "Method": "Exact Classical Ground State",
            "Max Cut Weight": max_cut,
            "Ising Energy H(s)": ground_energy,
            "Optimality Gap (%)": 0.0,
            "Runtime (ms)": round(exact_sol.runtime_ms, 3),
            "Spin Configuration": str(exact_sol.extra["spins"]),
        },
        {
            "Method": "Simulated Annealing (QUBO)",
            "Max Cut Weight": sa_cut,
            "Ising Energy H(s)": sa_energy,
            "Optimality Gap (%)": round(((max_cut - sa_cut) / max_cut) * 100.0, 2),
            "Runtime (ms)": round(sa_sol.runtime_ms, 3),
            "Spin Configuration": str(sa_spins.astype(int).tolist()),
        },
        {
            "Method": "Greedy Local Search",
            "Max Cut Weight": greedy_sol.objective_value,
            "Ising Energy H(s)": greedy_energy,
            "Optimality Gap (%)": round(((max_cut - greedy_sol.objective_value) / max_cut) * 100.0, 2),
            "Runtime (ms)": round(greedy_sol.runtime_ms, 3),
            "Spin Configuration": str(greedy_spins.astype(int).tolist()),
        },
    ]

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "maxcut_qubo_ising_baseline.csv"), index=False)

    # Save baseline instance data for direct Track C consumption
    np.save(os.path.join(out_dir, "track_b_maxcut_W.npy"), W)
    np.save(os.path.join(out_dir, "track_b_maxcut_Q.npy"), Q)

    plt.figure(figsize=(7, 4.5))
    methods = [r["Method"] for r in records]
    cuts = [r["Max Cut Weight"] for r in records]
    plt.bar(methods, cuts, color=["#2ca02c", "#ff7f0e", "#1f77b4"], width=0.5)
    plt.title(f"Max-Cut Benchmark (N={n} Nodes): Classical Baseline for Track C")
    plt.ylabel("Cut Weight (Maximized)")
    plt.ylim(0, max_cut * 1.25)
    for i, v in enumerate(cuts):
        plt.text(i, v + 1, f"Cut={v}\n(Gap={records[i]['Optimality Gap (%)']}%)", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "maxcut_classical_baseline.png"), dpi=200)
    plt.close()

    return df


def experiment_qubo_penalty_tuning(out_dir: str) -> pd.DataFrame:
    """Benchmark 4: Penalty parameter tuning in QUBO formulation of constrained problems."""
    # 6-item Knapsack solved via QUBO Simulated Annealing under different penalty weights
    values = np.array([10.0, 15.0, 20.0, 25.0, 30.0, 35.0])
    weights = np.array([3.0, 4.0, 5.0, 7.0, 8.0, 9.0])
    capacity = 14.0
    prob = KnapsackProblem(values=values, weights=weights, capacity=capacity)

    penalties = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0]
    records = []

    for P in penalties:
        Q, offset = prob.to_qubo(penalty_multiplier=P)
        sa = SimulatedAnnealingQUBO(steps_per_t=100, seed=42)
        sol = sa.solve(Q, offset)
        val, wt, feas = prob.evaluate(sol.variables)
        records.append({
            "Penalty Multiplier (P)": P,
            "Total Value": val,
            "Total Weight": wt,
            "Capacity": capacity,
            "Capacity Violation": max(0.0, wt - capacity),
            "Feasible": feas,
            "Runtime (ms)": round(sol.runtime_ms, 2)
        })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "qubo_penalty_tuning.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(df["Penalty Multiplier (P)"], df["Capacity Violation"], marker="s", color="red", label="Weight Excess (Violation)")
    plt.plot(df["Penalty Multiplier (P)"], df["Total Value"], marker="o", color="blue", label="Total Value")
    plt.axvline(x=2.5, color="green", linestyle="--", label="Optimal Penalty Threshold (P >= max v_i/w_i)")
    plt.xscale("log")
    plt.title("QUBO Constraint Enforcement: Penalty Multiplier Trade-Off")
    plt.xlabel("Penalty Multiplier P (log scale)")
    plt.ylabel("Metric Value")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "qubo_penalty_tuning.png"), dpi=200)
    plt.close()

    return df


def main():
    out_dir = os.path.join(TRACK_B_DIR, "..", "results", "track_b")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("==================================================")
    print("RUNNING TRACK B EXPERIMENTAL SUITE (DISCRETE)")
    print(f"Results output folder: {out_dir}")
    print("==================================================")

    print("\n[1/4] Running Knapsack Algorithmic Comparison (Greedy, DP, B&B, ILP)...")
    df_knap = experiment_knapsack_comparison(out_dir)
    print(df_knap.to_string(index=False))

    print("\n[2/4] Running Discrete Scalability Benchmark (Runtime vs N)...")
    df_scale = experiment_scalability(out_dir)
    print(df_scale.head(12).to_string(index=False))

    print("\n[3/4] Running Max-Cut QUBO & Ising Classical Baseline (for Track C)...")
    df_mc = experiment_maxcut_qubo_ising(out_dir)
    print(df_mc.to_string(index=False))

    print("\n[4/4] Running QUBO Penalty Parameter Tuning...")
    df_pen = experiment_qubo_penalty_tuning(out_dir)
    print(df_pen.to_string(index=False))

    print("\nAll Track B discrete experiments completed successfully.")


if __name__ == "__main__":
    main()

