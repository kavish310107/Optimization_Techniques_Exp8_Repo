"""Base discrete problem and solution classes."""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import numpy as np


@dataclass
class DiscreteSolution:
    """Standard container for discrete optimization solutions."""
    variables: np.ndarray             # Decision variable assignments (e.g., binary 0/1 or spins -1/+1)
    objective_value: float            # Evaluated objective score
    feasible: bool                    # Feasibility flag
    runtime_ms: float                 # Solution elapsed time in milliseconds
    method_name: str                  # Name of solver / heuristic used
    extra: Optional[Dict[str, Any]] = None  # Extra metadata (e.g. nodes explored, iterations, cuts)

