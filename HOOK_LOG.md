# PA6 — Hook Log

## Hook Implementation

I extended `.claude/hooks/guard_writes.py` and updated `.claude/settings.json` to register a PreToolUse hook for `Write`, `Edit`, `MultiEdit`, and `Bash`.

The hook protects the following paths:

* `utils/errors.py`
* `migrations/`
* `.env`
* `.claude/settings.json`

I also added checks for three categories of dangerous commands:

* Destructive SQL operations: `DROP TABLE` and `TRUNCATE TABLE`
* Recursive forced deletion: `rm -rf`
* Git force pushes: `git push --force`

The hook also blocks hardcoded database connection strings such as `postgresql://` and `sqlite:///` in inspected file content.

When a prohibited operation is detected, the hook prints a `BLOCKED` message and exits with code `2`.

## Bypass Vector 1 — Case-Sensitive Path

**Test input:** Simulated `Edit` tool call targeting `Utils/errors.py` instead of `utils/errors.py`.

**Initially blocked?** Yes.

**Initial result:** Exit code `2`.

**Root cause / explanation:** The existing hook uses `os.path.normcase()` to normalize paths. On Windows, this makes path comparisons case-insensitive, so changing the capitalization did not bypass the protection.

**Fix applied:** No additional fix was necessary because the existing path normalization already handled this case.

**Retest result:** Exit code `2`. The case-variation regression test passed.

**pytest result:** `297 passed in 0.57s`.

## Bypass Vector 2 — Indirect Write Through Bash

**Test input:** Simulated `Bash` tool call containing:

`echo test >> utils/errors.py`

**Initially blocked?** No.

**Initial result:** Exit code `0`.

**Root cause:** The original Bash guard checked for dangerous commands but did not inspect output-redirection destinations. This allowed a shell command to attempt writing to a protected file without using the `Write` or `Edit` tools.

**Fix applied:** I added an `is_protected_bash_write()` function that inspects shell output redirections and checks their destination paths against the existing `BLOCKED_PATHS` list. I updated `main()` to call this function when the tool is `Bash`.

**Retest result:** Exit code `2`, with the following message:

```text
BLOCKED: Bash write to Protected file: utils/errors.py.
```

**Claude Code integration test:** I instructed Claude to attempt `echo test >> utils/errors.py` using the Bash tool, without modifying other files or attempting a workaround.

Claude attempted the Bash operation, but the actual PreToolUse hook rejected it:

```text
PreToolUse:Bash hook error:
[python .claude/hooks/guard_writes.py]:
BLOCKED: Bash write to Protected file: utils/errors.py.
```

Claude reported that the command never executed, `utils/errors.py` was unchanged, and it stopped without attempting another tool or workaround.

This confirmed that the hook was enforced during an actual Claude Code tool call, not just during simulated testing.

**pytest result:** `297 passed in 0.57s`.

## Additional Guard Tests

I tested the hook by passing simulated tool inputs as JSON through PowerShell. These tests checked whether the hook returned the expected exit code without executing dangerous commands or modifying files.

| Test                                     | Expected exit code | Actual exit code | Result |
| ---------------------------------------- | ------------------ | ---------------- | ------ |
| Protected file (`utils/errors.py`)       | 2                  | 2                | PASS   |
| Case variation (`Utils/errors.py`)       | 2                  | 2                | PASS   |
| Protected directory (`migrations/`)      | 2                  | 2                | PASS   |
| `DROP TABLE users`                       | 2                  | 2                | PASS   |
| `TRUNCATE TABLE users`                   | 2                  | 2                | PASS   |
| `rm -rf temp_folder`                     | 2                  | 2                | PASS   |
| `git push --force`                       | 2                  | 2                | PASS   |
| Bash indirect write to `utils/errors.py` | 2                  | 2                | PASS   |
| Hardcoded PostgreSQL connection string   | 2                  | 2                | PASS   |
| Normal Python file content               | 0                  | 0                | PASS   |

**Regression results:** All 10 hook checks passed.

**Final pytest result:** `297 passed in 0.57s`.

## Limitations and Lessons Learned

The hook successfully blocked the tested operations, including an actual Bash write attempt inside Claude Code. However, it does not guarantee protection against every possible indirect file write. For example, commands that modify files through Python scripts, PowerShell utilities, or other mechanisms may not be detected by the current redirection check.

The content guard checks `Write` content and `Edit` replacement text. Additional handling would be needed to inspect every replacement in the `MultiEdit` input structure.

Most new guard patterns were verified using simulated tool calls. The Bash redirection scenario was verified through both simulation and an actual Claude Code tool invocation.

This exercise demonstrated that a hook can enforce restrictions more reliably than prompt instructions alone, but its effectiveness depends on correctly identifying all relevant tools, input formats, and bypass methods. Testing both blocked and allowed operations is important to confirm that the hook works without unnecessarily preventing legitimate development tasks.
