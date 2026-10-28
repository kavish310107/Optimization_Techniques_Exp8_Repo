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

