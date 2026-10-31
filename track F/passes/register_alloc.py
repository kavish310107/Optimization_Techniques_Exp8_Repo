"""Register Allocation via Graph Coloring (Chapter 6 Optimization Formulation).

Formulation:
Given an interference graph G = (V, E) where:
- Vertices V are variables / temporaries.
- Edges E exist between variables whose live ranges overlap.
- We want to assign each variable to one of K physical registers {R0, R1, ...}
  such that adjacent nodes receive different colors (no register clash).

Algorithms:
1. Greedy Graph Coloring (Welsh-Powell / Chaitin's heuristic: highest degree first).
2. Integer Linear Programming (ILP) Formulation:
   Minimize total colors / spill penalties subject to:
   - Exactly one color per variable: sum_{c} x_{v, c} = 1
   - Color conflict: x_{u, c} + x_{v, c} <= 1 for all (u, v) in E
"""
from typing import List, Dict, Set, Tuple
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from ir.tac import Instruction


def compute_liveness_and_interference(instructions: List[Instruction]) -> Tuple[List[str], Dict[str, Set[str]]]:
    """Compute variable live ranges and construct the interference graph.
    
    In the presence of loops (backward branches), any variable defined before or inside
    a loop and used in or after a loop must have its live range extend across the entire loop.
    """
    # Collect all variables (EXCLUDING control-flow labels)
    all_vars: Set[str] = set()
    label_names = {inst.dest for inst in instructions if inst.op == "LABEL"}

    for inst in instructions:
        if inst.dest and inst.op != "LABEL" and inst.dest not in label_names:
            all_vars.add(inst.dest)
        if isinstance(inst.src1, str) and inst.src1 not in label_names:
            all_vars.add(inst.src1)
        if isinstance(inst.src2, str) and inst.src2 not in label_names:
            all_vars.add(inst.src2)

    var_list = sorted(list(all_vars))

    first_seen = {v: len(instructions) for v in var_list}
    last_seen = {v: -1 for v in var_list}

    for idx, inst in enumerate(instructions):
        referenced = []
        if inst.dest and inst.op != "LABEL" and inst.dest in all_vars:
            referenced.append(inst.dest)
        if isinstance(inst.src1, str) and inst.src1 in all_vars:
            referenced.append(inst.src1)
        if isinstance(inst.src2, str) and inst.src2 in all_vars:
            referenced.append(inst.src2)

        for v in referenced:
            first_seen[v] = min(first_seen[v], idx)
            last_seen[v] = max(last_seen[v], idx)

    # Detect loops via backward JUMP instructions
    label_positions = {inst.dest: idx for idx, inst in enumerate(instructions) if inst.op == "LABEL"}
    for idx, inst in enumerate(instructions):
        if inst.op == "JUMP" and inst.dest in label_positions:
            target_idx = label_positions[inst.dest]
            if target_idx < idx:
                # Loop span is [target_idx, idx]
                # Any variable whose live range overlaps this loop must be live throughout the whole loop
                for v in var_list:
                    if first_seen[v] <= idx and last_seen[v] >= target_idx:
                        first_seen[v] = min(first_seen[v], target_idx)
                        last_seen[v] = max(last_seen[v], idx)

    # Build interference graph: edge if live intervals overlap
    adj: Dict[str, Set[str]] = {v: set() for v in var_list}
    for i in range(len(var_list)):
        u = var_list[i]
        for j in range(i + 1, len(var_list)):
            v = var_list[j]
            # Overlap check
            if not (last_seen[u] < first_seen[v] or last_seen[v] < first_seen[u]):
                adj[u].add(v)
                adj[v].add(u)

    return var_list, adj


def greedy_register_allocation(var_list: List[str], adj: Dict[str, Set[str]]) -> Dict[str, str]:
    """Greedy Welsh-Powell heuristic: order by descending node degree."""
    # Sort vertices by degree descending
    sorted_vars = sorted(var_list, key=lambda v: len(adj[v]), reverse=True)
    color_map: Dict[str, int] = {}

    for v in sorted_vars:
        # Find colors used by neighbors
        used_colors = {color_map[neighbor] for neighbor in adj[v] if neighbor in color_map}
        # Assign lowest available color
        color = 0
        while color in used_colors:
            color += 1
        color_map[v] = color

    return {v: f"R{c}" for v, c in color_map.items()}


def ilp_register_allocation(var_list: List[str], adj: Dict[str, Set[str]], max_registers: int = 8) -> Dict[str, str]:
    """Integer Linear Programming (ILP) formulation for optimal register allocation."""
    n = len(var_list)
    if n == 0:
        return {}

    K = min(max_registers, n)
    var_to_idx = {v: i for i, v in enumerate(var_list)}

    # Variables: x_{v, c} in {0, 1} indicates variable v gets register c
    num_vars = n * K
    def idx(v_i, c_i):
        return v_i * K + c_i

    # Objective: Minimize total registers used: minimize sum_c c * sum_v x_{v, c}
    c_obj = np.zeros(num_vars, dtype=float)
    for v_i in range(n):
        for c_i in range(K):
            c_obj[idx(v_i, c_i)] = c_i * 1.0  # Prefer lower register indices

    # Constraints:
    # 1. Exactly one color per variable: sum_c x_{v, c} = 1  (n constraints)
    # 2. No two interfering variables have same color: x_{u, c} + x_{v, c} <= 1  (num_edges * K constraints)
    edges = []
    for i in range(n):
        u = var_list[i]
        for neighbor in adj[u]:
            j = var_to_idx[neighbor]
            if i < j:
                edges.append((i, j))

    num_constraints = n + len(edges) * K
    A = np.zeros((num_constraints, num_vars), dtype=float)
    lhs = np.zeros(num_constraints, dtype=float)
    rhs = np.zeros(num_constraints, dtype=float)

    row = 0
    # Exactly one color
    for v_i in range(n):
        for c_i in range(K):
            A[row, idx(v_i, c_i)] = 1.0
        lhs[row] = 1.0
        rhs[row] = 1.0
        row += 1

    # Conflict constraints
    for (u_i, v_i) in edges:
        for c_i in range(K):
            A[row, idx(u_i, c_i)] = 1.0
            A[row, idx(v_i, c_i)] = 1.0
            lhs[row] = 0.0
            rhs[row] = 1.0
            row += 1

    integrality = np.ones(num_vars, dtype=int)
    bounds = Bounds(lb=np.zeros(num_vars), ub=np.ones(num_vars))
    constraints = LinearConstraint(A, lb=lhs, ub=rhs)

    res = milp(c=c_obj, integrality=integrality, constraints=constraints, bounds=bounds)

    if res.success and res.x is not None:
        sol = np.round(res.x).astype(int)
        alloc = {}
        for v_i, v in enumerate(var_list):
            for c_i in range(K):
                if sol[idx(v_i, c_i)] == 1:
                    alloc[v] = f"R{c_i}"
                    break
        return alloc
    else:
        # Fallback to greedy if ILP solver fails or is unbounded
        return greedy_register_allocation(var_list, adj)
