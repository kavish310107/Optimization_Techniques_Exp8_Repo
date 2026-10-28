"""Comprehensive Experiment Runner for Track A.

Executes and logs:
1. Benchmark 1: Convex Quadratic Optimization (GD, Momentum, NAG, AdaGrad, RMSProp, Adam, Newton).
2. Benchmark 2: Non-Convex Rosenbrock Valley Optimization.
3. Benchmark 3: Non-Convex Saddle Point Escape Dynamics.
4. Benchmark 4: Gauss-Newton on Non-Linear Least Squares.
5. Benchmark 5: Mini-Batch SGD and Full-Batch Backprop on Two-Layer MLP.
6. Benchmark 6: Learning Rate Sensitivity Analysis.
7. Benchmark 7: Curvature Approximations & Hessian-Vector Products (HVP).

Outputs structured CSV metrics and figures to results/track_a/.
"""
import os
import sys
import time
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure local imports work cleanly
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TRACK_A_DIR = os.path.dirname(CURR_DIR)
if TRACK_A_DIR not in sys.path:
    sys.path.insert(0, TRACK_A_DIR)

from optimizers import (
    GradientDescent,
    Momentum,
    NesterovAcceleratedGradient,
    AdaGrad,
    RMSProp,
    Adam,
    NewtonsMethod,
    GaussNewton,
    DiagonalFisherOptimizer,
    hessian_vector_product,
)
from objectives import (
    ConvexQuadratic,
    Rosenbrock,
    SaddleFunction,
    NonLinearLeastSquares,
)
from models import TwoLayerMLP


def run_optimizer_on_objective(
    optimizer,
    objective,
    x0: np.ndarray,
    max_iters: int = 200,
    tol: float = 1e-6,
    needs_hessian: bool = False,
    noise_std: float = 0.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run an optimizer on a continuous objective function with trajectory tracking."""
    optimizer.reset()
    rng = np.random.RandomState(seed)
    x = x0.copy().astype(float)

    trajectory = [x.copy()]
    losses = [objective.evaluate(x)]
    dist_opt = []
    d0 = objective.distance_to_optimum(x)
    if d0 is not None:
        dist_opt.append(d0)

    start_time = time.perf_counter()
    converged = False

    for it in range(max_iters):
        grad = objective.gradient(x)
        if noise_std > 0.0:
            grad = grad + rng.normal(0.0, noise_std, size=grad.shape)

        grad_norm = float(np.linalg.norm(grad))
        if grad_norm < tol:
            converged = True
            break

        kwargs = {}
        if needs_hessian:
            kwargs["hessian"] = objective.hessian(x)

        x_next = optimizer.step(x, grad, **kwargs)

        # Numerical instability guard
        if np.any(np.isnan(x_next)) or np.any(np.isinf(x_next)):
            break

        x = x_next
        trajectory.append(x.copy())
        losses.append(objective.evaluate(x))
        d = objective.distance_to_optimum(x)
        if d is not None:
            dist_opt.append(d)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "optimizer": optimizer.name,
        "objective": objective.name,
        "iterations": len(losses) - 1,
        "converged": converged,
        "final_loss": float(losses[-1]),
        "final_dist_opt": float(dist_opt[-1]) if dist_opt else None,
        "elapsed_ms": float(elapsed_ms),
        "trajectory": np.array(trajectory),
        "losses": np.array(losses),
        "dist_opt": np.array(dist_opt) if dist_opt else np.array([]),
    }


def experiment_convex_quadratic(out_dir: str) -> pd.DataFrame:
    """Experiment 1: Strongly convex quadratic comparison."""
    Q = np.array([[20.0, 0.0], [0.0, 2.0]], dtype=float)  # condition number = 10
    b = np.array([5.0, 1.0], dtype=float)
    obj = ConvexQuadratic(Q=Q, b=b)
    x0 = np.array([3.0, 4.0], dtype=float)

    # Maximum eigenvalue is L = 20.0, so stable step size for GD is lr < 2/L = 0.10.
    # For accelerated momentum/NAG, stable step size is lr <= 0.04 with beta=0.8.
    opts = [
        GradientDescent(lr=0.04),
        Momentum(lr=0.04, beta=0.8),
        NesterovAcceleratedGradient(lr=0.04, beta=0.8),
        AdaGrad(lr=0.5),
        RMSProp(lr=0.04),
        Adam(lr=0.08),
        NewtonsMethod(lr=1.0),
    ]

    records = []
    plt.figure(figsize=(9, 5))

    for opt in opts:
        needs_hess = (opt.name == "Newton")
        res = run_optimizer_on_objective(opt, obj, x0, max_iters=100, needs_hessian=needs_hess)
        records.append({
            "Optimizer": opt.name,
            "Iterations": res["iterations"],
            "Converged": res["converged"],
            "Final Loss": res["final_loss"],
            "Distance to Optimum": res["final_dist_opt"],
            "Runtime (ms)": round(res["elapsed_ms"], 3),
        })
        plt.semilogy(res["losses"], label=f"{opt.name} ({res['iterations']} iters)")

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "convex_quadratic_results.csv"), index=False)

    plt.title("Convergence on Strongly Convex Quadratic ($Q$ cond=10)")
    plt.xlabel("Iteration")
    plt.ylabel("Objective Value (log scale)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "convex_quadratic_convergence.png"), dpi=200)
    plt.close()

    return df


def experiment_rosenbrock(out_dir: str) -> pd.DataFrame:
    """Experiment 2: Non-convex Rosenbrock valley."""
    obj = Rosenbrock(a=1.0, b=100.0)
    x0 = np.array([-1.2, 1.0], dtype=float)  # Standard challenging start

    opts = [
        GradientDescent(lr=0.001),
        Momentum(lr=0.001, beta=0.9),
        NesterovAcceleratedGradient(lr=0.001, beta=0.9),
        AdaGrad(lr=0.2),
        RMSProp(lr=0.01),
        Adam(lr=0.05),
        NewtonsMethod(lr=1.0, damping=1e-2),
    ]

    records = []
    plt.figure(figsize=(9, 5))

    for opt in opts:
        needs_hess = (opt.name == "Newton")
        res = run_optimizer_on_objective(opt, obj, x0, max_iters=500, tol=1e-5, needs_hessian=needs_hess)
        records.append({
            "Optimizer": opt.name,
            "Iterations": res["iterations"],
            "Converged": res["converged"],
            "Final Loss": res["final_loss"],
            "Distance to Optimum": res["final_dist_opt"],
            "Runtime (ms)": round(res["elapsed_ms"], 3),
        })
        plt.semilogy(res["losses"], label=f"{opt.name} (Loss={res['final_loss']:.3e})")

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "rosenbrock_results.csv"), index=False)

    plt.title("Convergence on Non-Convex Rosenbrock Valley")
    plt.xlabel("Iteration")
    plt.ylabel("Objective Value (log scale)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rosenbrock_convergence.png"), dpi=200)
    plt.close()

    return df


def experiment_saddle_escape(out_dir: str) -> pd.DataFrame:
    """Experiment 3: Escape dynamics near strict saddle point (0, 0)."""
    obj = SaddleFunction()
    # Perturb slightly off saddle along negative curvature direction (y-axis)
    x0 = np.array([0.05, 0.001], dtype=float)

    opts = [
        GradientDescent(lr=0.05),
        Momentum(lr=0.05, beta=0.9),
        Adam(lr=0.05),
        RMSProp(lr=0.05),
        NewtonsMethod(lr=0.8, damping=1e-3),
    ]

    records = []
    plt.figure(figsize=(9, 5))

    for opt in opts:
        needs_hess = (opt.name == "Newton")
        res = run_optimizer_on_objective(opt, obj, x0, max_iters=150, needs_hessian=needs_hess)
        records.append({
            "Optimizer": opt.name,
            "Iterations": res["iterations"],
            "Converged": res["converged"],
            "Final Loss": res["final_loss"],
            "Final Position": np.round(res["trajectory"][-1], 4).tolist(),
            "Runtime (ms)": round(res["elapsed_ms"], 3),
        })
        plt.plot(res["losses"], label=f"{opt.name} (Final={res['final_loss']:.4f})")

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "saddle_escape_results.csv"), index=False)

    plt.axhline(y=-0.625, color="red", linestyle=":", label="Global Min (-0.625)")
    plt.title("Saddle Point Escape Trajectory (Strict Saddle at Origin)")
    plt.xlabel("Iteration")
    plt.ylabel("Objective Value f(x)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "saddle_escape.png"), dpi=200)
    plt.close()

    return df


def experiment_gauss_newton(out_dir: str) -> pd.DataFrame:
    """Experiment 4: Gauss-Newton vs. Gradient Descent on Non-Linear Least Squares."""
    nlls = NonLinearLeastSquares()
    theta0 = np.array([1.0, 0.1], dtype=float)  # initial parameter guess

    # 1. Gauss-Newton
    gn = GaussNewton(lr=1.0, damping=1e-4)
    theta = theta0.copy()
    gn_losses = [nlls.evaluate(theta)]
    start_t = time.perf_counter()
    for _ in range(50):
        r = nlls.residuals(theta)
        J = nlls.jacobian(theta)
        theta = gn.step(theta, residuals=r, jacobian=J)
        gn_losses.append(nlls.evaluate(theta))
        if np.linalg.norm(nlls.gradient(theta)) < 1e-6:
            break
    gn_time = (time.perf_counter() - start_t) * 1000.0

    # 2. Gradient Descent
    gd = GradientDescent(lr=0.01)
    theta_gd = theta0.copy()
    gd_losses = [nlls.evaluate(theta_gd)]
    start_t = time.perf_counter()
    for _ in range(50):
        grad = nlls.gradient(theta_gd)
        theta_gd = gd.step(theta_gd, grad)
        gd_losses.append(nlls.evaluate(theta_gd))
        if np.linalg.norm(grad) < 1e-6:
            break
    gd_time = (time.perf_counter() - start_t) * 1000.0

    records = [
        {"Method": "Gauss-Newton", "Iterations": len(gn_losses)-1, "Final Loss": gn_losses[-1], "Estimated Params": np.round(theta, 4).tolist(), "Runtime (ms)": round(gn_time, 3)},
        {"Method": "Gradient Descent", "Iterations": len(gd_losses)-1, "Final Loss": gd_losses[-1], "Estimated Params": np.round(theta_gd, 4).tolist(), "Runtime (ms)": round(gd_time, 3)},
    ]
    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "gauss_newton_vs_gd.csv"), index=False)

    plt.figure(figsize=(8, 4.5))
    plt.plot(gn_losses, label=f"Gauss-Newton (Iters={len(gn_losses)-1})", linewidth=2)
    plt.plot(gd_losses, label=f"Gradient Descent (Iters={len(gd_losses)-1})", linestyle="--", linewidth=2)
    plt.title("Gauss-Newton vs. Gradient Descent (Non-Linear Least Squares)")
    plt.xlabel("Iteration")
    plt.ylabel("Sum of Squared Residuals Loss")
    plt.yscale("log")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "gauss_newton_comparison.png"), dpi=200)
    plt.close()

    return df


def experiment_mlp_backpropagation(out_dir: str) -> pd.DataFrame:
    """Experiment 5: Small ML model training comparing Batch GD, Mini-batch SGD, and Adam with Backpropagation."""
    # Synthetic classification dataset (two moons or concentric circles)
    rng = np.random.RandomState(42)
    N = 400
    X = rng.randn(N, 2)
    # Target: binary circle boundary
    y = ((X[:, 0]**2 + X[:, 1]**2) < 1.2).astype(float).reshape(-1, 1)

    batch_configs = [
        ("Full-Batch GD", GradientDescent(lr=0.5), N),
        ("Mini-Batch SGD (batch=32)", GradientDescent(lr=0.1), 32),
        ("Pure SGD (batch=1)", GradientDescent(lr=0.02), 1),
        ("Adam (Mini-batch 32)", Adam(lr=0.05), 32),
    ]

    epochs = 40
    records = []
    loss_histories = {}

    for name, opt, b_size in batch_configs:
        mlp = TwoLayerMLP(input_dim=2, hidden_dim=8, seed=42)
        opt.reset()
        epoch_losses = []
        start_t = time.perf_counter()

        for epoch in range(epochs):
            # Shuffle indices
            perm = rng.permutation(N)
            X_shuff = X[perm]
            y_shuff = y[perm]

            num_batches = int(np.ceil(N / b_size))
            for b in range(num_batches):
                start_idx = b * b_size
                end_idx = min(start_idx + b_size, N)
                xb = X_shuff[start_idx:end_idx]
                yb = y_shuff[start_idx:end_idx]

                # 1. Forward
                y_pred = mlp.forward(xb)
                # 2. Backpropagation (analytical chain rule)
                grads_flat = mlp.backpropagation(yb)
                # 3. Optimizer update (distinct from backpropagation)
                params_flat = mlp.params_flat
                params_updated = opt.step(params_flat, grads_flat)
                mlp.set_params_flat(params_updated)

            # Evaluate epoch loss on full dataset
            full_pred = mlp.forward(X)
            e_loss = mlp.compute_loss(full_pred, y)
            epoch_losses.append(e_loss)

        run_time = (time.perf_counter() - start_t) * 1000.0
        acc = float(np.mean((full_pred >= 0.5) == y)) * 100.0
        records.append({
            "Method": name,
            "Batch Size": b_size,
            "Final Loss": epoch_losses[-1],
            "Final Accuracy (%)": round(acc, 2),
            "Runtime (ms)": round(run_time, 2),
        })
        loss_histories[name] = epoch_losses

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "mlp_training_results.csv"), index=False)

    plt.figure(figsize=(9, 5))
    for name, hist in loss_histories.items():
        plt.plot(hist, label=name)
    plt.title("Backpropagation on Two-Layer MLP: Batch vs Mini-batch vs Adam")
    plt.xlabel("Epoch")
    plt.ylabel("Binary Cross-Entropy Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "mlp_backprop_training.png"), dpi=200)
    plt.close()

    return df


def experiment_learning_rate_sensitivity(out_dir: str) -> pd.DataFrame:
    """Experiment 6: Hyperparameter sensitivity (Learning Rate sweeps)."""
    obj = Rosenbrock()
    x0 = np.array([-1.0, 1.0])
    lrs = [0.0001, 0.001, 0.005, 0.01, 0.05, 0.1]
    
    optimizers_to_sweep = [
        ("GD", lambda lr: GradientDescent(lr=lr)),
        ("Momentum", lambda lr: Momentum(lr=lr, beta=0.9)),
        ("RMSProp", lambda lr: RMSProp(lr=lr)),
        ("Adam", lambda lr: Adam(lr=lr)),
    ]

    records = []
    for opt_name, opt_factory in optimizers_to_sweep:
        for lr in lrs:
            opt = opt_factory(lr)
            res = run_optimizer_on_objective(opt, obj, x0, max_iters=250)
            records.append({
                "Optimizer": opt_name,
                "Learning Rate": lr,
                "Final Loss": min(res["final_loss"], 1e6),  # cap exploded values
                "Diverged": bool(res["final_loss"] > 1e4 or np.isnan(res["final_loss"])),
            })

    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "lr_sensitivity.csv"), index=False)

    plt.figure(figsize=(9, 5))
    for opt_name in ["GD", "Momentum", "RMSProp", "Adam"]:
        sub_df = df[df["Optimizer"] == opt_name]
        plt.plot(sub_df["Learning Rate"], sub_df["Final Loss"], marker="o", label=opt_name)

    plt.xscale("log")
    plt.yscale("log")
    plt.title("Learning Rate Sensitivity Analysis (Rosenbrock Valley)")
    plt.xlabel("Learning Rate (log scale)")
    plt.ylabel("Final Loss after 250 iterations (log scale)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "lr_sensitivity.png"), dpi=200)
    plt.close()

    return df


def experiment_curvature_and_hvp(out_dir: str) -> pd.DataFrame:
    """Experiment 7: Curvature Approximations & Hessian-Vector Products."""
    obj = ConvexQuadratic(Q=np.array([[10.0, 0.0], [0.0, 2.0]]))
    x = np.array([2.0, 3.0])
    v = np.array([1.0, 1.0])

    # 1. Exact H * v
    H_exact = obj.hessian(x)
    Hv_exact = H_exact @ v

    # 2. Pearlmutter / Finite Difference HVP
    Hv_approx = hessian_vector_product(obj.gradient, x, v, eps=1e-5)
    hvp_error = float(np.linalg.norm(Hv_exact - Hv_approx))

    # 3. Diagonal Fisher Optimizer comparison on noisy objective
    df_opt = DiagonalFisherOptimizer(lr=0.1)
    gd_opt = GradientDescent(lr=0.05)

    res_df = run_optimizer_on_objective(df_opt, obj, x, max_iters=80, noise_std=0.2)
    res_gd = run_optimizer_on_objective(gd_opt, obj, x, max_iters=80, noise_std=0.2)

    records = [
        {"Test": "HVP Accuracy", "Metric": "Euclidean Error ||Hv_exact - Hv_approx||", "Value": hvp_error},
        {"Test": "Noisy Optimization", "Metric": "Final Loss (Diagonal Fisher)", "Value": res_df["final_loss"]},
        {"Test": "Noisy Optimization", "Metric": "Final Loss (Standard GD)", "Value": res_gd["final_loss"]},
    ]
    df = pd.DataFrame(records)
    df.to_csv(os.path.join(out_dir, "curvature_and_hvp_results.csv"), index=False)
    return df


def main():
    out_dir = os.path.join(TRACK_A_DIR, "..", "results", "track_a")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print("==================================================")
    print("RUNNING TRACK A EXPERIMENTAL SUITE")
    print(f"Results output folder: {out_dir}")
    print("==================================================")

    print("\n[1/7] Running Convex Quadratic Benchmark...")
    df_quad = experiment_convex_quadratic(out_dir)
    print(df_quad.to_string(index=False))

    print("\n[2/7] Running Rosenbrock Valley Benchmark...")
    df_rosen = experiment_rosenbrock(out_dir)
    print(df_rosen.to_string(index=False))

    print("\n[3/7] Running Saddle Point Escape Dynamics Benchmark...")
    df_saddle = experiment_saddle_escape(out_dir)
    print(df_saddle.to_string(index=False))

    print("\n[4/7] Running Gauss-Newton vs. Gradient Descent...")
    df_gn = experiment_gauss_newton(out_dir)
    print(df_gn.to_string(index=False))

    print("\n[5/7] Running MLP Backpropagation and Batch Comparison...")
    df_mlp = experiment_mlp_backpropagation(out_dir)
    print(df_mlp.to_string(index=False))

    print("\n[6/7] Running Learning Rate Sensitivity Analysis...")
    df_lr = experiment_learning_rate_sensitivity(out_dir)
    print("LR sensitivity matrix written to CSV.")

    print("\n[7/7] Running Curvature Approximations & Hessian-Vector Products...")
    df_curv = experiment_curvature_and_hvp(out_dir)
    print(df_curv.to_string(index=False))

    print("\nAll Track A experiments completed successfully.")


if __name__ == "__main__":
    main()
