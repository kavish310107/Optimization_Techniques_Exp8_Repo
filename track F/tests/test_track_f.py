"""Unit tests for Track F: Compiler Optimization.

Tests:
1. Lexer and Parser tokenization and AST construction.
2. Syntax error handling on invalid syntax.
3. Constant folding and propagation pass.
4. Strength reduction pass (x*2 -> x+x, x*0 -> 0, x*1 -> x).
5. Common subexpression elimination (CSE) pass.
6. Dead-code elimination (DCE) pass.
7. End-to-end semantic output preservation across unoptimized and optimized code.
8. Register allocation graph coloring correctness (interfering variables never get same register).
"""
import pytest
import sys
import os

TRACK_F_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


class TestFrontend:
    def test_lexer_and_parser_basic(self):
        code = "x = 10 + 20; print(x);"
        ast = parse_code(code)
        assert len(ast.statements) == 2
        assert ast.statements[0].name == "x"

    def test_syntax_error_rejected(self):
        with pytest.raises(SyntaxError):
            parse_code("x = = 10;")


class TestOptimizations:
    def test_constant_folding(self):
        code = "x = 2 * 3 + 4; print(x);"
        ast = parse_code(code)
        ir = IRGenerator().generate(ast)
        opt_ir = ConstantFoldingAndPropagation().run(ir)

        # Before DCE, x = 10 should be explicitly assigned
        assert any(i.op == "ASSIGN" and i.src1 == 10 for i in opt_ir)

        # After DCE and run, output should be 10
        opt_ir = DeadCodeElimination().run(opt_ir)
        vm = TACVirtualMachine(opt_ir)
        out, _, _ = vm.run()
        assert out == [10]

    def test_strength_reduction(self):
        insts = [
            Instruction("MUL", dest="t1", src1="a", src2=2),
            Instruction("MUL", dest="t2", src1="b", src2=1),
            Instruction("MUL", dest="t3", src1="c", src2=0),
        ]
        opt = StrengthReduction().run(insts)
        assert opt[0].op == "ADD" and opt[0].src1 == "a" and opt[0].src2 == "a" # x + x
        assert opt[1].op == "ASSIGN" and opt[1].src1 == "b"                     # x
        assert opt[2].op == "ASSIGN" and opt[2].src1 == 0                       # 0

    def test_common_subexpression_elimination(self):
        code = """
            a = 5;
            b = 6;
            x = a + b;
            y = a + b;
            print(x);
            print(y);
        """
        ast = parse_code(code)
        ir = IRGenerator().generate(ast)
        opt = CommonSubexpressionElimination().run(ir)

        # Count ADD operations
        adds = [i for i in opt if i.op == "ADD"]
        # Exactly one ADD computed, second is reused via assignment
        assert len(adds) == 1

    def test_dead_code_elimination(self):
        code = """
            a = 10;
            b = 20;
            unused = a * b + 100;
            print(a);
        """
        ast = parse_code(code)
        ir = IRGenerator().generate(ast)
        opt = DeadCodeElimination().run(ir)
        # 'unused' destination should be completely eliminated
        assert not any(i.dest == "unused" for i in opt)


class TestRegisterAllocationAndExecution:
    def test_register_allocation_no_clash(self):
        # Variables x, y are alive simultaneously and interfere
        code = """
            x = 10;
            y = 20;
            z = x + y;
            print(z);
        """
        ast = parse_code(code)
        ir = IRGenerator().generate(ast)
        var_list, adj = compute_liveness_and_interference(ir)

        reg_map_greedy = greedy_register_allocation(var_list, adj)
        reg_map_ilp = ilp_register_allocation(var_list, adj)

        # x and y interfere, so they must be assigned different physical registers
        assert reg_map_greedy["x"] != reg_map_greedy["y"]
        assert reg_map_ilp["x"] != reg_map_ilp["y"]

    def test_full_pipeline_output_preservation(self):
        code = """
            n = 5;
            fact = 1;
            i = 1;
            while (i <= n) {
                fact = fact * i;
                i = i + 1;
            }
            print(fact);
        """
        ast = parse_code(code)
        ir = IRGenerator().generate(ast)

        # Execute unoptimized
        vm_unopt = TACVirtualMachine(ir)
        out_unopt, _, _ = vm_unopt.run()

        # Run passes
        opt_ir = ConstantFoldingAndPropagation().run(ir)
        opt_ir = StrengthReduction().run(opt_ir)
        opt_ir = DeadCodeElimination().run(opt_ir)

        var_list, adj = compute_liveness_and_interference(opt_ir)
        reg_ilp = ilp_register_allocation(var_list, adj)

        vm_opt = TACVirtualMachine(opt_ir, register_map=reg_ilp)
        out_opt, _, _ = vm_opt.run()

        # 5! = 120
        assert out_unopt == [120]
        assert out_opt == [120]
        assert out_unopt == out_opt
