"""Parallel module exports."""
from .parallel_opt import (
    ParallelOptimizationBenchmark,
    fit_amdahl_and_gustafson,
)

__all__ = [
    "ParallelOptimizationBenchmark",
    "fit_amdahl_and_gustafson",
]

