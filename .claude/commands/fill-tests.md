

\# Use this command to find and fill missing test coverage for an existing Python module. Do not use it to implement new features or refactor production code.



\## Goal

Audit $ARGUMENTS for missing test coverage and add pytest tests for uncovered behavior.



\## Context

\- Follow the existing test conventions in tests/.

\- Use pytest and the project's current fixtures.

\- Refer to CLAUDE.md for architectural and testing rules.

\- Review the target module before writing tests.



\## Constraints

\- Do not modify production code.

\- Do not modify utils/errors.py, migrations/, or .env.

\- Do not rewrite existing tests unnecessarily.

\- Do not duplicate tests that already cover the same behavior.

\- Preserve the current project architecture.

\- Add tests only for behavior supported by the existing implementation.



\## Verification

Run pytest -q after adding tests.

All existing and new tests must pass.

Report the test results, new test cases, and files changed.
