"""Virtual Machine / Interpreter for executing 3-Address Code and measuring runtime."""
import time
from typing import List, Dict, Any, Tuple
from ir.tac import Instruction


class TACVirtualMachine:
    """Stackless register/memory interpreter for MiniLang 3-Address Code."""

    def __init__(self, instructions: List[Instruction], register_map: Dict[str, str] = None):
        self.instructions = instructions
        self.register_map = register_map or {}
        # Memory storage: register/var name -> int value
        self.memory: Dict[str, int] = {}
        self.output: List[int] = []
        # Label to instruction index mapping
        self.labels: Dict[str, int] = {}
        for idx, inst in enumerate(instructions):
            if inst.op == "LABEL":
                self.labels[inst.dest] = idx

    def resolve(self, val: Any) -> int:
        if isinstance(val, int):
            return val
        elif isinstance(val, str):
            # Check register mapping if enabled
            mapped_key = self.register_map.get(val, val)
            return self.memory.get(mapped_key, 0)
        return 0

    def store(self, var: str, val: int):
        mapped_key = self.register_map.get(var, var)
        self.memory[mapped_key] = val

    def run(self, max_steps: int = 100000) -> Tuple[List[int], int, float]:
        """Execute instructions.
        
        Returns:
            (output_list, total_executed_cycles, elapsed_time_ms)
        """
        pc = 0
        cycles = 0
        t0 = time.perf_counter()

        while pc < len(self.instructions) and cycles < max_steps:
            inst = self.instructions[pc]
            cycles += 1

            if inst.op == "LABEL":
                pc += 1
                continue
            elif inst.op == "ASSIGN":
                self.store(inst.dest, self.resolve(inst.src1))
                pc += 1
            elif inst.op == "PRINT":
                val = self.resolve(inst.src1)
                self.output.append(val)
                pc += 1
            elif inst.op == "JUMP":
                pc = self.labels[inst.dest] + 1
            elif inst.op == "JUMP_IF_ZERO":
                cond = self.resolve(inst.src1)
                if cond == 0:
                    pc = self.labels[inst.dest] + 1
                else:
                    pc += 1
            else:
                # Arithmetic / logic operations
                v1 = self.resolve(inst.src1)
                v2 = self.resolve(inst.src2)
                res = 0
                if inst.op == "ADD":
                    res = v1 + v2
                elif inst.op == "SUB":
                    res = v1 - v2
                elif inst.op == "MUL":
                    res = v1 * v2
                elif inst.op == "DIV":
                    res = v1 // v2 if v2 != 0 else 0
                elif inst.op == "MOD":
                    res = v1 % v2 if v2 != 0 else 0
                elif inst.op == "EQ":
                    res = 1 if v1 == v2 else 0
                elif inst.op == "NEQ":
                    res = 1 if v1 != v2 else 0
                elif inst.op == "LT":
                    res = 1 if v1 < v2 else 0
                elif inst.op == "GT":
                    res = 1 if v1 > v2 else 0
                elif inst.op == "LE":
                    res = 1 if v1 <= v2 else 0
                elif inst.op == "GE":
                    res = 1 if v1 >= v2 else 0

                self.store(inst.dest, res)
                pc += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return self.output, cycles, elapsed_ms
