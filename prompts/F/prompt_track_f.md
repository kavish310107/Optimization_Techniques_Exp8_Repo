# Track F Prompt Record: Compiler Optimization

- **Track**: Track F (Compiler Optimization)
- **Date**: 2026-10-31
- **AI Tool**: Gemini (Antigravity Assistant)
- **Kind of Work**: Mini-compiler architecture, Lexer, Parser, AST, Intermediate Representation (3-Address Code / CFG), Optimization passes (Constant Folding & Propagation, Dead-Code Elimination, Common Subexpression Elimination, Strength Reduction), Chapter 6 Optimization Formulation (ILP/Greedy Register Allocation via Graph Coloring), Virtual Machine execution engine, tests, benchmarking, and documentation.

## User Prompt Excerpt:
> Implement **Track F: Compiler Optimization** in the existing `track F/` folder of my Optimization Techniques assignment.
> 1. Inspect assignment requirements: Mini-compiler (lexer, parser, IR, code generator/VM). Implement at least 2 optimizations (4 for full credit: Constant Folding/Propagation, Dead-Code Elimination, Common Subexpression Elimination, Strength Reduction). Formulate at least one compiler decision as an optimization problem solved with a Chapter 6 method (e.g. Graph Coloring Register Allocation via ILP / Greedy). Measure instruction count, runtime, code size, compile time; optimized programs must produce identical output.
> 2. Design the compiler: Support variables, assignments, arithmetic, conditionals, loops, print statements.
> 3. Execution / VM: 3-address code IR interpreter to execute before and after optimizations.
> 4. Verification: Independent test suite testing parsing, transformations, equivalence of output.
> 5. Results & shared updates: CHECKLIST.md, README.md, requirements.txt, failure_log.md, tool_comparison.md, REPORT.md.

