"""Linear Intermediate Representation (3-Address Code / Quadruples) and CFG."""
from dataclasses import dataclass
from typing import List, Optional, Union, Any, Dict, Set


@dataclass
class Instruction:
    op: str                      # "ASSIGN", "ADD", "SUB", "MUL", "DIV", "MOD", "LABEL", "JUMP", "JUMP_IF_ZERO", "PRINT"
    dest: Optional[str] = None   # Destination variable/temp/label
    src1: Optional[Union[str, int]] = None
    src2: Optional[Union[str, int]] = None

    def __str__(self):
        if self.op == "LABEL":
            return f"{self.dest}:"
        elif self.op == "JUMP":
            return f"    goto {self.dest}"
        elif self.op == "JUMP_IF_ZERO":
            return f"    if not {self.src1} goto {self.dest}"
        elif self.op == "PRINT":
            return f"    print {self.src1}"
        elif self.op == "ASSIGN":
            return f"    {self.dest} = {self.src1}"
        else: # Binary arithmetic
            return f"    {self.dest} = {self.src1} {self.op} {self.src2}"


class IRGenerator:
    """Translates AST into linear Three-Address Code (TAC)."""

    def __init__(self):
        self.instructions: List[Instruction] = []
        self.temp_counter = 0
        self.label_counter = 0

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"_t{self.temp_counter}"

    def new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def emit(self, op: str, dest: Optional[str] = None, src1: Optional[Union[str, int]] = None, src2: Optional[Union[str, int]] = None):
        inst = Instruction(op=op, dest=dest, src1=src1, src2=src2)
        self.instructions.append(inst)
        return inst

    def generate(self, ast) -> List[Instruction]:
        self.instructions = []
        for stmt in ast.statements:
            self.visit_stmt(stmt)
        return self.instructions

    def visit_stmt(self, node):
        node_type = type(node).__name__
        if node_type == "Assign":
            res = self.visit_expr(node.expr)
            self.emit("ASSIGN", dest=node.name, src1=res)
        elif node_type == "Print":
            res = self.visit_expr(node.expr)
            self.emit("PRINT", src1=res)
        elif node_type == "If":
            cond_res = self.visit_expr(node.cond)
            else_label = self.new_label("else")
            end_label = self.new_label("endif")

            self.emit("JUMP_IF_ZERO", dest=else_label, src1=cond_res)
            for s in node.then_body:
                self.visit_stmt(s)
            self.emit("JUMP", dest=end_label)

            self.emit("LABEL", dest=else_label)
            for s in node.else_body:
                self.visit_stmt(s)
            self.emit("LABEL", dest=end_label)

        elif node_type == "While":
            start_label = self.new_label("loop_start")
            end_label = self.new_label("loop_end")

            self.emit("LABEL", dest=start_label)
            cond_res = self.visit_expr(node.cond)
            self.emit("JUMP_IF_ZERO", dest=end_label, src1=cond_res)
            for s in node.body:
                self.visit_stmt(s)
            self.emit("JUMP", dest=start_label)
            self.emit("LABEL", dest=end_label)

    def visit_expr(self, node) -> Union[str, int]:
        node_type = type(node).__name__
        if node_type == "Number":
            return node.value
        elif node_type == "Variable":
            return node.name
        elif node_type == "BinaryOp":
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.right)
            t = self.new_temp()
            # Map operator symbol to IR op
            op_map = {
                "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
                "==": "EQ", "!=": "NEQ", "<": "LT", ">": "GT", "<=": "LE", ">=": "GE"
            }
            ir_op = op_map.get(node.op, node.op)
            self.emit(ir_op, dest=t, src1=left, src2=right)
            return t
        else:
            raise ValueError(f"Unknown expression node: {node}")

