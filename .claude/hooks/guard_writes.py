
#!/usr/bin/env python3
"""PreToolUse hook: block writes to protected files and directories."""

import json
import os
import sys
import re

BLOCKED_PATHS = [
    "utils/errors.py",
    "migrations/",
    ".env",
    ".claude/settings.json",
]

BLOCKED_COMMANDS = [
    (r"\b(?:DROP|TRUNCATE)\s+TABLE\b", "Destructive SQL table operation"),
    (r"(?<!\w)rm\s+-[rf]*r[rf]*(?!\w)", "Recursive forced deletion"),
    (r"\bgit\s+push\s+--force\b", "Force push"),
]

def is_dangerous_command(command: str) -> tuple[bool, str]:
    """Check shell commands for prohibited operations."""
    for pattern, reason in BLOCKED_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason

    return False, ""


def is_blocked(file_path: str) -> tuple[bool, str]:
    """Return whether the file path is protected."""
    project_root = os.path.abspath(".")
    target = os.path.normcase(os.path.abspath(file_path))

    for pattern in BLOCKED_PATHS:
        protected = os.path.normcase(
            os.path.abspath(os.path.join(project_root, pattern))
        )

        if target == protected:
            return True, f"Protected file: {pattern}"

        if pattern.endswith("/") and (
            target == protected
            or target.startswith(protected + os.sep)
        ):
            return True, f"Protected directory: {pattern}"

    return False, ""

def is_blocked_content(content: str) -> tuple[bool, str]:
    """Detect hardcoded database connection strings."""
    blocked_patterns = [
        r"postgresql://",
        r"sqlite:///",
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True, f"Hardcoded database connection string: {pattern}"

    return False, ""

def is_protected_bash_write(command: str) -> tuple[bool, str]:
    """Block shell commands that redirect output to protected paths."""
    pattern = r"(?:>>|>|1>|2>|1>>|2>>)\s*['\"]?([^\s'\";&|]+)"

    for match in re.finditer(pattern, command):
        file_path = match.group(1)
        blocked, reason = is_blocked(file_path)

        if blocked:
            return True, f"Bash write to {reason}"

    return False, ""

def main():
    payload = json.loads(sys.stdin.read())
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Check Bash commands
    if tool == "Bash":
        command = tool_input.get("command", "")

        blocked, reason = is_dangerous_command(command)
        if blocked:
            print(f"BLOCKED: {reason}.", file=sys.stderr)
            sys.exit(2)

        blocked, reason = is_protected_bash_write(command)
        if blocked:
            print(f"BLOCKED: {reason}.", file=sys.stderr)
            sys.exit(2)

        sys.exit(0)

    # Check file-writing tools
    if tool not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    blocked, reason = is_blocked(file_path)
    if blocked:
        print(
            f"BLOCKED: {reason}. This file is protected by project policy.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Check for hardcoded database connection strings
    content = tool_input.get("content", "")

    if tool == "Edit":
        content = tool_input.get("new_string", "")

    blocked, reason = is_blocked_content(content)
    if blocked:
        print(f"BLOCKED: {reason}.", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)
if __name__ == "__main__":
    main()