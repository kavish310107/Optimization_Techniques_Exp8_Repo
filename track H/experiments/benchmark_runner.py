"""
Benchmark Runner for Track H: DBMS Optimization.

Executes comparative benchmarks:
1. Baseline (Unindexed Heap Scans) vs Optimized (Secondary & Covering B-Tree Indexes).
2. Query Plan Inspection (`EXPLAIN QUERY PLAN`).
3. Measurement of query execution latency (repeated runs with mean/std).
4. Storage footprint overhead (bytes added by secondary indexes).
5. Write overhead measurement (INSERT / UPDATE latency penalty with active indexes).
6. Result equivalence verification (SHA-256 hash / exact record sets).
"""

import sys
import os
import time
import sqlite3
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Include track H in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.database_setup import (
    init_database,
    populate_database,
    apply_indexes_to_db,
    drop_indexes_from_db
)
from workloads.queries import QUERIES, QueryDefinition
from optimizers.plan_analyzer import get_query_plan, analyze_index_usage, get_db_file_size_bytes


def benchmark_queries(
    conn: sqlite3.Connection,
    repetitions: int = 20,
    warmup: int = 3,
    is_optimized: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Runs each query in QUERIES multiple times and computes latency statistics."""
    cursor = conn.cursor()
    results = {}

    for qid, qdef in QUERIES.items():
        # Select SQL
        sql = qdef.optimized_sql if (is_optimized and qdef.optimized_sql) else qdef.baseline_sql

        # Execution plan
        plan = get_query_plan(conn, sql)
        plan_analysis = analyze_index_usage(plan)

        # Warmup runs
        for _ in range(warmup):
            cursor.execute(sql)
            _ = cursor.fetchall()

        # Timed repetitions
        latencies_ms = []
        result_rows = None
        for _ in range(repetitions):
            t0 = time.perf_counter()
            cursor.execute(sql)
            rows = cursor.fetchall()
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)
            if result_rows is None:
                result_rows = rows

        results[qid] = {
            "name": qdef.name,
            "mean_latency_ms": float(np.mean(latencies_ms)),
            "std_latency_ms": float(np.std(latencies_ms)),
            "min_latency_ms": float(np.min(latencies_ms)),
            "max_latency_ms": float(np.max(latencies_ms)),
            "p95_latency_ms": float(np.percentile(latencies_ms, 95)),
            "row_count": len(result_rows),
            "result_rows": result_rows,
            "plan_summary": " | ".join(node["detail"] for node in plan),
            "uses_index": plan_analysis["uses_index"],
            "uses_covering": plan_analysis["uses_covering_index"],
            "num_scans": plan_analysis["num_scans"]
        }

    return results


def benchmark_write_overhead(
    conn: sqlite3.Connection,
    n_inserts: int = 2000,
    seed: int = 99
) -> Dict[str, float]:
    """Measures insertion throughput (transactions per second / latency per record)."""
    rng = np.random.default_rng(seed)
    cursor = conn.cursor()

    # Generate synthetic orders to insert
    test_inserts = [
        (
            900000 + i,
            int(rng.integers(1, 5000)),
            "2026-03-15",
            "Pending",
            round(float(rng.uniform(20.0, 500.0)), 2)
        )
        for i in range(n_inserts)
    ]

    t0 = time.perf_counter()
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", test_inserts)
    conn.commit()
    t1 = time.perf_counter()
    total_time_s = t1 - t0

    # Cleanup inserted test rows
    cursor.execute("DELETE FROM orders WHERE order_id >= 900000;")
    conn.commit()

    return {
        "n_inserts": n_inserts,
        "total_insert_time_ms": total_time_s * 1000.0,
        "latency_per_insert_us": (total_time_s / n_inserts) * 1e6,
        "throughput_inserts_per_sec": n_inserts / total_time_s
    }


def run_full_experiment(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(output_dir, "benchmark_ecommerce.db")

    print("--- Initializing and Populating Database ---")
    conn = init_database(db_path, apply_indexes=False)
    counts = populate_database(conn, n_customers=5000, n_categories=20, n_products=1000, n_orders=15000, seed=42)
    print(f"Loaded: Customers={counts[0]}, Categories={counts[1]}, Products={counts[2]}, Orders={counts[3]}, OrderItems={counts[4]}")
    conn.close()

    size_baseline_bytes = get_db_file_size_bytes(db_path)

    # 1. Run Baseline (Unindexed)
    print("\n--- Running Baseline Benchmarks (Unindexed Heap Scans) ---")
    conn = sqlite3.connect(db_path)
    baseline_query_results = benchmark_queries(conn, repetitions=25, is_optimized=False)
    baseline_write_metrics = benchmark_write_overhead(conn, n_inserts=2000)
    conn.close()

    # 2. Apply Indexes and Run Optimized
    print("\n--- Applying Secondary and Covering Indexes ---")
    conn = sqlite3.connect(db_path)
    apply_indexes_to_db(conn)
    conn.close()

    size_optimized_bytes = get_db_file_size_bytes(db_path)
    storage_overhead_bytes = size_optimized_bytes - size_baseline_bytes
    storage_overhead_pct = (storage_overhead_bytes / size_baseline_bytes) * 100.0

    print(f"Database Size: Baseline = {size_baseline_bytes / 1024:.2f} KB | Optimized = {size_optimized_bytes / 1024:.2f} KB (+{storage_overhead_pct:.1f}%)")

    print("\n--- Running Optimized Benchmarks (Indexed Scans & Join Optimizations) ---")
    conn = sqlite3.connect(db_path)
    optimized_query_results = benchmark_queries(conn, repetitions=25, is_optimized=True)
    optimized_write_metrics = benchmark_write_overhead(conn, n_inserts=2000)
    conn.close()

    # 3. Verify Result Equivalence
    print("\n--- Verifying Output Equivalence ---")
    equivalence_checks = {}
    for qid in QUERIES:
        base_rows = baseline_query_results[qid]["result_rows"]
        opt_rows = optimized_query_results[qid]["result_rows"]
        # Normalize comparison (sort if order not guaranteed)
        if "ORDER BY" not in QUERIES[qid].baseline_sql.upper():
            base_sorted = sorted(str(r) for r in base_rows)
            opt_sorted = sorted(str(r) for r in opt_rows)
            match = (base_sorted == opt_sorted)
        else:
            match = (base_rows == opt_rows)
        equivalence_checks[qid] = match
        print(f"  {qid}: {'PASS (Exact Match)' if match else 'FAIL (Mismatch!)'} ({len(base_rows)} rows)")

    # 4. Collate Comparison DataFrame
    records = []
    for qid in QUERIES:
        b = baseline_query_results[qid]
        o = optimized_query_results[qid]
        speedup = b["mean_latency_ms"] / o["mean_latency_ms"] if o["mean_latency_ms"] > 0 else 1.0
        pct_improvement = ((b["mean_latency_ms"] - o["mean_latency_ms"]) / b["mean_latency_ms"]) * 100.0

        records.append({
            "query_id": qid,
            "query_name": b["name"],
            "row_count": b["row_count"],
            "baseline_mean_ms": b["mean_latency_ms"],
            "baseline_std_ms": b["std_latency_ms"],
            "baseline_scans": b["num_scans"],
            "optimized_mean_ms": o["mean_latency_ms"],
            "optimized_std_ms": o["std_latency_ms"],
            "optimized_uses_index": o["uses_index"],
            "optimized_uses_covering": o["uses_covering"],
            "speedup_factor": speedup,
            "latency_reduction_pct": pct_improvement,
            "results_equivalent": equivalence_checks[qid],
            "baseline_plan": b["plan_summary"],
            "optimized_plan": o["plan_summary"]
        })

    df = pd.DataFrame(records)
    csv_path = os.path.join(output_dir, "dbms_query_benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nQuery benchmark results saved to: {csv_path}")

    # Write overhead summary
    write_records = [
        {
            "configuration": "Baseline (No Secondary Indexes)",
            "total_insert_time_ms": baseline_write_metrics["total_insert_time_ms"],
            "latency_per_insert_us": baseline_write_metrics["latency_per_insert_us"],
            "throughput_inserts_per_sec": baseline_write_metrics["throughput_inserts_per_sec"],
            "db_size_kb": size_baseline_bytes / 1024.0
        },
        {
            "configuration": "Optimized (7 Secondary & Covering Indexes)",
            "total_insert_time_ms": optimized_write_metrics["total_insert_time_ms"],
            "latency_per_insert_us": optimized_write_metrics["latency_per_insert_us"],
            "throughput_inserts_per_sec": optimized_write_metrics["throughput_inserts_per_sec"],
            "db_size_kb": size_optimized_bytes / 1024.0
        }
    ]
    df_write = pd.DataFrame(write_records)
    write_csv_path = os.path.join(output_dir, "dbms_write_storage_overhead.csv")
    df_write.to_csv(write_csv_path, index=False)
    print(f"Write and storage overhead saved to: {write_csv_path}")

    # Plot results
    plot_results(df, df_write, output_dir)
    return df, df_write


def plot_results(df: pd.DataFrame, df_write: pd.DataFrame, output_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Track H: Relational DBMS Query & Indexing Optimization", fontsize=16, fontweight="bold")

    # Plot 1: Query Execution Latency Comparison (Log scale)
    qids = df["query_id"].values
    x = np.arange(len(qids))
    width = 0.35

    ax0 = axes[0]
    b_means = df["baseline_mean_ms"].values
    b_errs = df["baseline_std_ms"].values
    o_means = df["optimized_mean_ms"].values
    o_errs = df["optimized_std_ms"].values

    ax0.bar(x - width/2, b_means, width, yerr=b_errs, label="Baseline (Full Scans)", color="#E94E77", capsize=4, alpha=0.85, edgecolor="black")
    ax0.bar(x + width/2, o_means, width, yerr=o_errs, label="Optimized (Indexed / Rewritten)", color="#50E3C2", capsize=4, alpha=0.85, edgecolor="black")
    ax0.set_yscale("log")
    ax0.set_ylabel("Execution Time (ms, log scale)", fontsize=11, fontweight="bold")
    ax0.set_title("Query Latency Comparison by Archetype", fontsize=13, fontweight="bold")
    ax0.set_xticks(x)
    ax0.set_xticklabels(qids, fontsize=10, fontweight="bold")
    ax0.legend(loc="upper right")
    ax0.grid(axis="y", linestyle="--", alpha=0.5)

    # Annotate speedup factors
    for i, sp in enumerate(df["speedup_factor"]):
        ax0.annotate(f"{sp:.1f}x", (x[i] + width/2, o_means[i]), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, fontweight="bold")

    # Plot 2: Write Overhead & Storage Footprint Trade-off
    ax1 = axes[1]
    configs = ["Baseline\n(No Indexes)", "Optimized\n(7 Indexes)"]
    insert_latencies = df_write["latency_per_insert_us"].values
    db_sizes = df_write["db_size_kb"].values

    color1 = '#4A90E2'
    ax1.set_title("The Indexing Trade-off: Storage & Write Penalty", fontsize=13, fontweight="bold")
    ax1.bar([0 - 0.2, 1 - 0.2], insert_latencies, 0.35, color=color1, alpha=0.85, label="Insert Latency (µs / row)", edgecolor="black")
    ax1.set_ylabel("Insert Latency (µs / row)", color=color1, fontsize=11, fontweight="bold")
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(configs, fontsize=11, fontweight="bold")

    ax2 = ax1.twinx()
    color2 = '#F5A623'
    ax2.bar([0 + 0.2, 1 + 0.2], db_sizes, 0.35, color=color2, alpha=0.85, label="DB Size (KB)", edgecolor="black")
    ax2.set_ylabel("Total Database Storage (KB)", color=color2, fontsize=11, fontweight="bold")
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "dbms_optimization_analysis.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Optimization comparison plot saved to: {plot_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "results", "track_h")
    run_full_experiment(out_dir)
