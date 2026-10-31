"""Optimization Passes for MiniLang 3-Address Code:
1. Constant Folding & Constant Propagation
2. Common Subexpression Elimination (CSE)
3. Dead-Code Elimination (DCE)
4. Strength Reduction (e.g. x * 2 -> x + x, x * 0 -> 0, x * 1 -> x)
5. Register Allocation via Graph Coloring (Chapter 6 formulation solved via ILP or Greedy)
"""
from typing import List, Dict, Set, Tuple, Optional, Any
import numpy as np
from ir.tac import Instruction


class OptimizationPass:
    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        raise NotImplementedError


class ConstantFoldingAndPropagation(OptimizationPass):
    """Folds arithmetic operations on literals and propagates known constants."""

    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        # Track known constants: var_name -> integer_value
        # In presence of control flow (labels/jumps), reset constants conservatively
        known_constants: Dict[str, int] = {}
        new_insts = []

        for inst in instructions:
            # Control-flow barrier: clear known constants to preserve sound correctness
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_ZERO"):
                known_constants.clear()
                new_insts.append(inst)
                continue

            # 1. Propagate constants into operands src1 and src2
            src1 = inst.src1
            src2 = inst.src2
            if isinstance(src1, str) and src1 in known_constants:
                src1 = known_constants[src1]
            if isinstance(src2, str) and src2 in known_constants:
                src2 = known_constants[src2]

            # 2. Fold operations on two constant operands
            if isinstance(src1, int) and isinstance(src2, int):
                folded_val = None
                if inst.op == "ADD":
                    folded_val = src1 + src2
                elif inst.op == "SUB":
                    folded_val = src1 - src2
                elif inst.op == "MUL":
                    folded_val = src1 * src2
                elif inst.op == "DIV" and src2 != 0:
                    folded_val = src1 // src2
                elif inst.op == "MOD" and src2 != 0:
                    folded_val = src1 % src2
                elif inst.op == "EQ":
                    folded_val = 1 if src1 == src2 else 0
                elif inst.op == "NEQ":
                    folded_val = 1 if src1 != src2 else 0
                elif inst.op == "LT":
                    folded_val = 1 if src1 < src2 else 0
                elif inst.op == "GT":
                    folded_val = 1 if src1 > src2 else 0
                elif inst.op == "LE":
                    folded_val = 1 if src1 <= src2 else 0
                elif inst.op == "GE":
                    folded_val = 1 if src1 >= src2 else 0

                if folded_val is not None:
                    # Simplify to ASSIGN literal
                    new_inst = Instruction("ASSIGN", dest=inst.dest, src1=folded_val)
                    new_insts.append(new_inst)
                    if inst.dest:
                        known_constants[inst.dest] = folded_val
                    continue

            # Handle direct assignment of constant
            if inst.op == "ASSIGN":
                new_inst = Instruction("ASSIGN", dest=inst.dest, src1=src1)
                new_insts.append(new_inst)
                if isinstance(src1, int) and inst.dest:
                    known_constants[inst.dest] = src1
                elif inst.dest in known_constants:
                    del known_constants[inst.dest]
                continue

            # Default: update instruction with propagated operands
            new_inst = Instruction(inst.op, dest=inst.dest, src1=src1, src2=src2)
            new_insts.append(new_inst)
            # If variable redefined non-constantly, remove from known constants
            if inst.dest and inst.dest in known_constants:
                del known_constants[inst.dest]

        return new_insts


class StrengthReduction(OptimizationPass):
    """Replaces computationally expensive operations with cheaper primitives:
    - x * 2  =>  x + x
    - x * 1  =>  x
    - x * 0  =>  0
    - x + 0  =>  x
    - x - 0  =>  x
    - x / 1  =>  x
    """

    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        new_insts = []
        for inst in instructions:
            if inst.op == "MUL":
                # x * 2 or 2 * x => x + x
                if inst.src2 == 2:
                    new_insts.append(Instruction("ADD", dest=inst.dest, src1=inst.src1, src2=inst.src1))
                    continue
                elif inst.src1 == 2:
                    new_insts.append(Instruction("ADD", dest=inst.dest, src1=inst.src2, src2=inst.src2))
                    continue
                # x * 1 or 1 * x => x
                elif inst.src2 == 1:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src1))
                    continue
                elif inst.src1 == 1:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src2))
                    continue
                # x * 0 or 0 * x => 0
                elif inst.src2 == 0 or inst.src1 == 0:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=0))
                    continue

            elif inst.op == "ADD":
                if inst.src2 == 0:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src1))
                    continue
                elif inst.src1 == 0:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src2))
                    continue

            elif inst.op == "SUB":
                if inst.src2 == 0:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src1))
                    continue

            elif inst.op == "DIV":
                if inst.src2 == 1:
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=inst.src1))
                    continue

            new_insts.append(inst)
        return new_insts


class CommonSubexpressionElimination(OptimizationPass):
    """Local CSE: Eliminates redundant identical computations within basic blocks."""

    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        new_insts = []
        # Map: (op, src1, src2) -> previous_dest_variable
        available_expressions: Dict[Tuple[str, Any, Any], str] = {}

        for inst in instructions:
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_ZERO"):
                available_expressions.clear()
                new_insts.append(inst)
                continue

            if inst.op in ("ADD", "SUB", "MUL", "DIV", "MOD", "EQ", "NEQ", "LT", "GT", "LE", "GE"):
                key = (inst.op, inst.src1, inst.src2)
                # For commutative operations (+, *, ==, !=), sort operands to catch symmetry
                if inst.op in ("ADD", "MUL", "EQ", "NEQ") and isinstance(inst.src1, str) and isinstance(inst.src2, str):
                    if inst.src1 > inst.src2:
                        key = (inst.op, inst.src2, inst.src1)

                if key in available_expressions:
                    prev_var = available_expressions[key]
                    # Reuse previous computation
                    new_insts.append(Instruction("ASSIGN", dest=inst.dest, src1=prev_var))
                    continue
                else:
                    available_expressions[key] = inst.dest
                    new_insts.append(inst)

            elif inst.op == "ASSIGN":
                # Invalidate any stored expression containing this variable
                to_delete = [k for k in available_expressions if k[1] == inst.dest or k[2] == inst.dest]
                for k in to_delete:
                    del available_expressions[k]
                new_insts.append(inst)

            else:
                new_insts.append(inst)

        return new_insts


class DeadCodeElimination(OptimizationPass):
    """Dead Code Elimination: Iteratively removes unused temporary and variable assignments."""

    def run(self, instructions: List[Instruction]) -> List[Instruction]:
        changed = True
        current_insts = list(instructions)

        while changed:
            changed = False
            # 1. Collect all used variables
            used_variables: Set[str] = set()
            for inst in current_insts:
                if isinstance(inst.src1, str):
                    used_variables.add(inst.src1)
                if isinstance(inst.src2, str):
                    used_variables.add(inst.src2)

            filtered_insts = []
            for inst in current_insts:
                # Critical instructions with side-effects cannot be removed
                if inst.op in ("PRINT", "LABEL", "JUMP", "JUMP_IF_ZERO"):
                    filtered_insts.append(inst)
                elif inst.dest and inst.dest not in used_variables:
                    # Destination is never read; discard dead computation
                    changed = True
                else:
                    filtered_insts.append(inst)

            current_insts = filtered_insts

        return current_insts
