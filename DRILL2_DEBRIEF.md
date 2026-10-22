\# Drill 2 — Debrief



\*\*Q1. In Phase 3, did Claude attempt to work around the block? What does that behavior tell you about how hooks and prompts interact?\*\*



No. After the hook blocked the edit to `utils/errors.py`, Claude reported the error and stopped. This shows that CLAUDE.md rules are advisory, while PreToolUse hooks can enforce restrictions before a tool executes. The hook returned exit code 2, preventing the modification.



\*\*Q2. Compare maintaining a CLAUDE.md Do-not-touch rule versus maintaining BLOCKED\_PATHS in guard\_writes.py. Which is harder to keep accurate over time, and why?\*\*



CLAUDE.md rules are easier to write but harder to enforce consistently because Claude may interpret or overlook them. BLOCKED\_PATHS requires more initial setup but is easier to verify because the hook either blocks the operation or allows it. During testing, I discovered that my hook initially allowed absolute Windows paths, so I updated the path normalization and confirmed that protected files were blocked.



\*\*Q3. Name one protection that file-level blocking cannot provide and explain how you would implement it.\*\*



File-level blocking cannot detect dangerous commands such as `rm -rf` or `DROP TABLE`. I would extend the PreToolUse hook to inspect `tool\_input.command` when Claude uses Bash. If the command matches a prohibited pattern, the hook would print an error and exit with code 2 to block execution.
