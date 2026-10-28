# Failure Log & Debugging Records

This document records meaningful AI-generated coding errors, bugs, failed approaches, debugging steps, fixes, and lessons learned throughout the lifecycle of this project.

Entries must follow the format:
- **Timestamp / Phase**
- **Symptom / Error Encountered**
- **Root Cause Analysis**
- **Resolution / Fix Applied**
- **Lesson Learned**

---

### Entry 001: PowerShell Foreach Variable Interpolation Syntax Error
- **Timestamp / Phase**: Setup Phase (Directory Initialization)
- **Symptom / Error Encountered**:
  PowerShell script execution failed with:
  `Missing variable name after foreach.`
  `Unexpected token ')' in expression or statement.`
- **Root Cause Analysis**:
  A multi-line PowerShell string passed directly to the shell without single quotes caused variable interpolation expansion issues during subshell invocation, stripping `$d` to empty text before PowerShell parsed the loop.
- **Resolution / Fix Applied**:
  Replaced the interpolated script block with a direct single-line command using native comma-separated paths:
  `New-Item -ItemType Directory -Force -Path ...`
- **Lesson Learned**:
  When driving Windows PowerShell via CLI tools, pass clean command arrays or single-quoted script blocks to avoid shell variable stripping.

---

### Entry 002: Over-aggressive Step Size Divergence in Accelerated Gradient (NAG)
- **Timestamp / Phase**: Track A Implementation (Benchmark 1 - Strongly Convex Quadratic)
- **Symptom / Error Encountered**:
  During benchmark execution on a quadratic function with Lipschitz constant $L = \lambda_{max}(Q) = 20.0$, Nesterov Accelerated Gradient (NAG) exploded with objective loss $2.76 \times 10^{32}$ at $\text{lr}=0.08$.
- **Root Cause Analysis**:
  For standard GD, stability requires $\eta < 2/L = 0.10$. However, accelerated momentum methods (NAG) have tighter stability bounds $\eta \le \frac{2(1-\beta)}{L(1+\beta)}$ to avoid resonance oscillations along high-curvature eigenspaces. At $\eta=0.08, \beta=0.8$, the amplification factor exceeded unity along the dominant eigenvector.
- **Resolution / Fix Applied**:
  Adjusted step size $\eta$ to $0.04$ ($< 1/L$), respecting acceleration stability limits, and refined NAG formulation to Sutskever's standard lookahead velocity representation. NAG then converged cleanly in 89 iterations to within $4.95 \times 10^{-7}$ of the optimum.
- **Lesson Learned**:
  Accelerated first-order methods require strictly smaller step sizes than unaccelerated GD when ill-conditioned curvature exists, emphasizing the necessity of step-size tuning.

