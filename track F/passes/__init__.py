"""Passes module exports."""
from .optimizations import (
    OptimizationPass,
    ConstantFoldingAndPropagation,
    StrengthReduction,
    CommonSubexpressionElimination,
    DeadCodeElimination,
)
from .register_alloc import (
    compute_liveness_and_interference,
    greedy_register_allocation,
    ilp_register_allocation,
)

__all__ = [
    "OptimizationPass",
    "ConstantFoldingAndPropagation",
    "StrengthReduction",
    "CommonSubexpressionElimination",
    "DeadCodeElimination",
    "compute_liveness_and_interference",
    "greedy_register_allocation",
    "ilp_register_allocation",
]

