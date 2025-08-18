# Debug Report: Bridge Communication Syntax Error

## Issue Summary
The `ai-team connect` command fails with a Python SyntaxError when attempting to establish bridges between AI teams.

## Root Cause Analysis

### The Problem
```
SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' on line 43
```

This error occurs when running:
```bash
ai-team connect bsnes-plus snes-modder "context"
```

### Key Findings

1. **Mixed Language Execution**
   - `ai-team` is a **Python script** (`#!/usr/bin/env python3`)
   - `ai-bridge` is a **Bash script** (`#!/bin/bash`)
   - The Python script incorrectly tries to execute the Bash script using Python interpreter

2. **Incorrect Execution Method**
   ```python
   # In ai-team (line found in grep):
   cmd = [sys.executable, CONNECT_SCRIPT, "create"] + sys.argv[2:]
   subprocess.run(cmd, check=True)
   ```
   - `sys.executable` points to the Python interpreter
   - `CONNECT_SCRIPT` points to `/Users/ship/.local/bin/ai-bridge` (a Bash script)
   - This causes Python to try parsing Bash syntax as Python code

3. **Bash Syntax Triggering Python Error**
   - Line 43 of ai-bridge: `if [ $# -eq 0 ] || [ "$1" = "help" ] || ...`
   - Python interprets `[` as list literal opening
   - Python expects `]` to close the list but finds `)` from the case statement

## File Types Confirmed
```bash
/Users/ship/.local/bin/ai-team: Python script (#!/usr/bin/env python3)
/Users/ship/.local/bin/ai-bridge: Bash script (#!/bin/bash)
```

## The Fix Required
The `ai-team` Python script needs to execute `ai-bridge` as a shell script, not with Python:

**Current (Broken):**
```python
cmd = [sys.executable, CONNECT_SCRIPT, "create"] + sys.argv[2:]
```

**Should Be:**
```python
cmd = [CONNECT_SCRIPT, "create"] + sys.argv[2:]
# Or explicitly:
cmd = ["bash", CONNECT_SCRIPT, "create"] + sys.argv[2:]
```

## Workaround Options

1. **Direct Bridge Command**
   ```bash
   /Users/ship/.local/bin/ai-bridge connect bsnes-plus snes-modder "context"
   ```

2. **Manual Bridge Creation**
   - Use legacy bridge commands if available
   - Use `send-to-peer` for direct communication

3. **Fix the Script**
   - Edit `/Users/ship/.local/bin/ai-team` to remove `sys.executable` from the subprocess call

## Impact on Team Coordination
- Bridge establishment between `bsnes-plus` and `snes-modder` teams is blocked
- Teams can still work independently
- Manual coordination through orchestrator messages is still functional

## Current Bridge Status
```bash
$ ai-bridge list
Active Bridges (0): None
```

## Alternative Communication Methods Working
- `send-claude-message.sh` - Internal team communication ✅
- Individual team operations ✅
- MCP server access ✅

## Files Analyzed
- `/Users/ship/.local/bin/ai-team` (Python orchestration wrapper)
- `/Users/ship/.local/bin/ai-bridge` (Bash bridge management script)
- `/Users/ship/.local/bin/send-claude-message.sh` (Team messaging)

## Recommendation
The script maintainer should update `ai-team` to properly execute shell scripts using subprocess without forcing Python interpretation. This is a simple one-line fix that would restore full multi-team coordination capabilities.
