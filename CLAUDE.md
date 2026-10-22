# Task Manager

Python Flask API for managing tasks and users.

## Commands
- Install dependencies with `pip install -r requirements.txt`.
- Run the full test suite with `pytest -v`.
- Run task tests with `pytest tests/test_tasks.py -v`.
- Run the Flask application with `python app.py`.
- Run the linter with `ruff check .`.
- If `pytest` or `ruff` is not on PATH, use `.\.venv\Scripts\python.exe -m pytest -q` and `.\.venv\Scripts\python.exe -m ruff check .` (the gate run after each Task 2 subagent).

### Claude Code Slash Commands
- `/audit-errors <file>` — Audit a service file for missing AppError handling, fix identified issues within scope, and run tests.
- `/scaffold-endpoint <resource> <method>` — Create an API endpoint using the existing route-service architecture, avoiding duplicate endpoints and verifying HTTP responses.
- `/fill-tests <module>` — Identify missing test coverage and add pytest tests without modifying production code.

## Architecture
- Follow the layered pattern: routes → services → repositories.
- Keep task business logic in `services/tasks.py`, not in `routes/api.py`.
- Use `routes/api.py` as the canonical example for Flask routes and AppError handling.
- Use `services/users.py` as the canonical service-layer pattern.
- Routes in `routes/api.py` only parse the request, check the body shape (non-object body, missing key) and shape the response; value validation and lookups that raise `NotFoundError` or `ValidationError` belong in `services/`, following `services/users.py` (for example, `update_notification_pref()` validates `notification_pref`, not `update_notification_pref_route`).

## Conventions
- Use type hints on functions, following `services/users.py`.
- Use Google-style docstrings for service functions, following `services/users.py`; preserve existing implementation logic and formatting unless the requested change requires otherwise.
- Use `NotFoundError` and `ValidationError` from `utils/errors.py` for expected application errors; `get_task()` must raise `NotFoundError("Task")` when the task ID is missing.
- Follow the error-handling pattern used by `get_user()` in `services/users.py`.
- Keep task data in the existing structures in `services/tasks.py` unless the task requires a data-model change.

## Hooks
The PreToolUse hook in `.claude/hooks/guard_writes.py` enforces restrictions on Write, Edit, MultiEdit, and Bash operations through `.claude/settings.json`.
It blocks direct edits to `utils/errors.py`, `migrations/`, `.env`, and `.claude/settings.json`.
It also checks for destructive SQL operations, `rm -rf`, `git push --force`, hardcoded database connection strings, and direct Bash output redirection to protected paths.
To add a new restriction, update the hook's protected paths or command patterns, then test both blocked and allowed operations.
These checks cover the implemented patterns but do not guarantee protection against every possible indirect write.

## Do not touch
- Do not change function signatures in `services/tasks.py` unless explicitly required.
- Do not remove or bypass the `AppError` handler in `routes/api.py`.
- Do not modify existing tests in `tests/test_tasks.py` just to make an implementation pass.
- Do not edit `DECOMPOSITION.md` or `PLAN_LOG.md` in a session that runs a subagent prompt (SA-1 `services/users.py`, SA-2 `routes/api.py`, SA-3 `tests/test_notifications.py`); record Hand-off (actual) and Result in a separate session.
- Do not edit `tests/test_tags.py` or `tests/test_priority.py` unless the approved plan names the exact change.
- When adding user routes, do not change existing task routes, imports or the `AppError` handler in `routes/api.py`, and do not validate field values there; only extend the `services.users` import and add routes.
- When writing `tests/test_notifications.py`, do not modify `services/users.py`, `routes/api.py` or `services/tasks.py`; report application bugs instead.
