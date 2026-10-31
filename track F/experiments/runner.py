"""Comprehensive Track F Experiment Runner & Benchmark Suite.

Demonstrates:
1. Four Compulsory Optimizations:
   - Constant Folding & Propagation (CFP)
   - Common Subexpression Elimination (CSE)
   - Dead-Code Elimination (DCE)
   - Strength Reduction (SR)
2. Compiler Decision Posed as Chapter 6 Optimization:
   - Register Allocation via Graph Coloring: ILP (SciPy HiGHS) vs Greedy (Welsh-Powell).
3. Correctness Verification:
   - Compares observable program output before and after optimization across all benchmarks.
4. Performance Metrics:
   - Static Instruction Count (Before vs After)
   - Dynamic Executed Cycles (VM Run)
   - Wall-Clock Execution Time (ms)
   - Compile Time (ms)
   - Registers Used (Greedy vs ILP)

Outputs CSV tables and comparative visualization plots into results/track_f/.
"""
import os
import sys
import time
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK_F_DIR = os.path.dirname(CURR_DIR)
if TRACK_F_DIR not in sys.path:
    sys.path.insert(0, TRACK_F_DIR)

from frontend.parser import parse_code
from ir.tac import IRGenerator, Instruction
from passes.optimizations import (
    ConstantFoldingAndPropagation,
    StrengthReduction,
    CommonSubexpressionElimination,
    DeadCodeElimination,
)
from passes.register_alloc import (
    compute_liveness_and_interference,
    greedy_register_allocation,
    ilp_register_allocation,
)
from codegen.vm import TACVirtualMachine


# --- Benchmark Test Programs ---

PROGRAMS = {
    "Program_1_Constant_Folding": """
        x = 10 + 20 * 2;
        y = x - 5;
        z = y * 1;
        print(z);
    """,

    "Program_2_Common_Subexpression": """
        a = 4;
        b = 5;
        x = a * b + 10;
        y = a * b + 20;
        z = (a * b) + (a * b);
        print(x);
        print(y);
        print(z);
    """,

    "Program_3_Strength_Reduction": """
        val = 14;
        m1 = val * 2;
        m2 = val * 1;
        m3 = val * 0;
        m4 = val + 0;
        m5 = val / 1;
        print(m1);
        print(m2);
        print(m3);
        print(m4);
        print(m5);
    """,

    "Program_4_Dead_Code": """
        a = 100;
        b = 200;
        dead1 = a * b + 42;
        dead2 = dead1 * 2;
        live = a + 5;
        print(live);
    """,

    "Program_5_Complex_Loop": """
        sum = 0;
        i = 1;
        while (i <= 5) {
            term = i * 2;
            unused = term + 999;
            sum = sum + term;
            i = i + 1;
        }
        print(sum);
    """
}


def compile_and_optimize(source_code: str) -> Dict[str, Any]:
    """Runs the full compiler pipeline: Parse -> IR -> Optimizations -> Register Alloc -> VM."""
    t0_compile = time.perf_counter()

    # 1. Frontend
    ast = parse_code(source_code)
    # 2. Unoptimized IR
    ir_gen = IRGenerator()
    unopt_ir = ir_gen.generate(ast)

    # 3. Optimization Pipeline
    cfp = ConstantFoldingAndPropagation()
    sr = StrengthReduction()
    cse = CommonSubexpressionElimination()
    dce = DeadCodeElimination()

    opt_ir = list(unopt_ir)
    # Run multiple iterative passes until convergence
    for _ in range(3):
        opt_ir = cfp.run(opt_ir)
        opt_ir = sr.run(opt_ir)
        opt_ir = cse.run(opt_ir)
        opt_ir = dce.run(opt_ir)

    compile_time_ms = (time.perf_counter() - t0_compile) * 1000.0

    # 4. Register Allocation on Optimized IR (Chapter 6 optimization decision)
    var_list, adj = compute_liveness_and_interference(opt_ir)
    reg_greedy = greedy_register_allocation(var_list, adj)
    reg_ilp = ilp_register_allocation(var_list, adj)

    # 5. Execution in Virtual Machine (Correctness Verification)
    vm_unopt = TACVirtualMachine(unopt_ir)
    out_unopt, cycles_unopt, time_unopt = vm_unopt.run()

    vm_opt = TACVirtualMachine(opt_ir, register_map=reg_ilp)
    out_opt, cycles_opt, time_opt = vm_opt.run()

    # Verification: output must be identical
    is_correct = (out_unopt == out_opt)

    return {
        "unopt_ir": unopt_ir,
        "opt_ir": opt_ir,
        "unopt_count": len(unopt_ir),
        "opt_count": len(opt_ir),
        "reduction_pct": round(((len(unopt_ir) - len(opt_ir)) / max(1, len(unopt_ir))) * 100.0, 1),
        "out_unopt": out_unopt,
        "out_opt": out_opt,
        "is_correct": is_correct,
        "cycles_unopt": cycles_unopt,
        "cycles_opt": cycles_opt,
        "time_unopt_ms": round(time_unopt, 3),
        "time_opt_ms": round(time_opt, 3),
        "compile_time_ms": round(compile_time_ms, 3),
        "regs_greedy": len(set(reg_greedy.values())),
        "regs_ilp": len(set(reg_ilp.values())),
    }


def run_track_f_benchmarks(out_dir: str):
    print("==================================================")
    print("RUNNING TRACK F EXPERIMENTAL SUITE (MINILANG COMPILER)")
    print(f"Results output folder: {out_dir}")
    print("==================================================")

    records = []

    for name, code in PROGRAMS.items():
        print(f"\n--- Compiling & Benchmarking: {name} ---")
        res = compile_and_optimize(code)

        print(f"Original IR instructions:  {res['unopt_count']}")
        print(f"Optimized IR instructions: {res['opt_count']} ({res['reduction_pct']}% reduction)")
        print(f"Execution Output Correct:  {res['is_correct']} (Unopt: {res['out_unopt']} | Opt: {res['out_opt']})")
        print(f"Executed Cycles:           {res['cycles_unopt']} -> {res['cycles_opt']}")
        print(f"Register Allocation:       Greedy={res['regs_greedy']} regs | ILP={res['regs_ilp']} regs")

        records.append({
            "Program": name,
            "Unopt Instructions": res["unopt_count"],
            "Opt Instructions": res["opt_count"],
            "Instruction Reduction (%)": res["reduction_pct"],
            "Unopt Cycles": res["cycles_unopt"],
            "Opt Cycles": res["cycles_opt"],
            "Cycle Reduction (%)": round(((res["cycles_unopt"] - res["cycles_opt"]) / max(1, res["cycles_unopt"])) * 100.0, 1),
            "Output Preserved": res["is_correct"],
            "Program Output": str(res["out_opt"]),
            "Registers (Greedy)": res["regs_greedy"],
            "Registers (ILP)": res["regs_ilp"],
            "Compile Time (ms)": res["compile_time_ms"],
            "VM Runtime (ms)": res["time_opt_ms"],
        })

    df = pd.DataFrame(records)
    csv_path = os.path.join(out_dir, "compiler_benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nBenchmark table saved to: {csv_path}")

    # Comparative Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    p_names = [p.replace("Program_", "P").replace("_", " ") for p in df["Program"]]
    x = np.arange(len(p_names))
    width = 0.35

    # 1. Static Instruction Count
    ax1.bar(x - width/2, df["Unopt Instructions"], width, label="Unoptimized TAC", color="#d62728")
    ax1.bar(x + width/2, df["Opt Instructions"], width, label="Optimized TAC", color="#2ca02c")
    ax1.set_ylabel("Instruction Count")
    ax1.set_title("Static IR Code Size Reduction")
    ax1.set_xticks(x)
    ax1.set_xticklabels(p_names, rotation=20, ha="right", fontsize=8)
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. Dynamic Executed Cycles
    ax2.bar(x - width/2, df["Unopt Cycles"], width, label="Unoptimized Cycles", color="#1f77b4")
    ax2.bar(x + width/2, df["Opt Cycles"], width, label="Optimized Cycles", color="#ff7f0e")
    ax2.set_ylabel("VM Execution Cycles")
    ax2.set_title("Dynamic Instruction Execution Savings")
    ax2.set_xticks(x)
    ax2.set_xticklabels(p_names, rotation=20, ha="right", fontsize=8)
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "compiler_optimizations_comparison.png"), dpi=200)
    plt.close()

    return df


def main():
    out_dir = os.path.join(TRACK_F_DIR, "..", "results", "track_f")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    df = run_track_f_benchmarks(out_dir)
    print("\nSummary Table:")
    print(df[["Program", "Unopt Instructions", "Opt Instructions", "Instruction Reduction (%)", "Output Preserved", "Registers (ILP)"]].to_string(index=False))


if __name__ == "__main__":
    main()

