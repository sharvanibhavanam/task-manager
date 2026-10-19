\# Iteration Log



\## Session 1 — Error Handling for get\_task



\### Prompt



> Add error handling to the get\_task function in @services/tasks.py. Do not change the function signature. Follow the existing project patterns. Run pytest -v when done.



\### What Claude Did



Claude inspected the existing task service and user service patterns. It added `NotFoundError` from `utils/errors.py` to `services/tasks.py`, updated `get\_task()` so that a missing task ID raises `NotFoundError("Task")`, and added a Google-style docstring. The function signature remained unchanged. Claude ran `pytest -v`, and all 4 existing tests passed.



\### Observation



Claude correctly followed the error-handling pattern already used by `get\_user()` in `services/users.py`. However, the initial CLAUDE.md instructions did not explicitly say what `get\_task()` should raise for a missing task. I updated the Conventions section to make this requirement explicit.



\### CLAUDE.md Update



Added a project-specific rule requiring `get\_task()` to raise `NotFoundError("Task")` when the task ID is missing.



\---



\## Session 2 — Refactor create\_task



\### Prompt



> Refactor create\_task in @services/tasks.py to match the style of get\_user in @services/users.py exactly. Preserve the existing function signature and behavior. Run pytest -v when done.



\### What Claude Did



Claude read both `services/tasks.py` and `services/users.py`. It added a Google-style docstring to `create\_task()` and kept the existing function signature and behavior unchanged. Claude ran `pytest -v`, and all 4 tests passed.



\### Observation



Claude followed the requested service-layer style and preserved the implementation logic. This showed that the existing `services/users.py` rule was useful as a concrete canonical example. I updated the Conventions section to make it clearer that style changes should not unnecessarily alter existing implementation logic or formatting.



\### CLAUDE.md Update



Updated the Google-style docstring rule to require preservation of existing implementation logic and formatting unless the requested change requires otherwise.



\---



\## Session 3 — Add get\_tasks\_by\_user



\### Prompt



> Add a new function to @services/tasks.py that returns all tasks for a given user\_id. Follow the same service-layer pattern used in @services/users.py. Add appropriate tests in @tests/test\_tasks.py. Run pytest -v when done.



\### What Claude Did



Claude added `get\_tasks\_by\_user(user\_id: int)` to `services/tasks.py`. The function uses a type hint and Google-style docstring and returns all tasks whose `user\_id` matches the requested user. Claude also added two tests to `tests/test\_tasks.py`: one for a user with tasks and one for a user with no tasks. The test suite increased from 4 to 6 tests, and all 6 passed.



\### Observation



Claude followed the existing service-layer conventions without requiring corrections. The new tests covered both the normal case and the empty-result case, which gave me confidence that the instructions were specific enough to guide a new feature.



\---



\## Final Validation



After the three Claude sessions, I added Ruff as a project linting tool and verified the final project state. The first `ruff check .` exposed six existing lint issues. Ruff automatically fixed four import-formatting issues, and I configured Ruff to ignore the existing `B017` warnings for the project's broad exception assertions. The final lint command passed.



Final validation:



\* `ruff check .` — All checks passed.

\* `pytest -v` — 6 tests passed.

\* `CLAUDE\_v1.md` preserved the original instructions.

\* `CLAUDE.md` contains the two iterations made during the Claude sessions plus the final lint command.




---

## Week 5 Drill 1 — Phase 3: Reject and Revise Plan

### Prompt

> Refactor the task repository so every method catches database exceptions and raises the appropriate AppError subclass instead. Follow the pattern in services/users.py. Follow CLAUDE.md.

### What Claude Did

Claude inspected the project and identified that it has no database or repository layer. Tasks are stored in an in-memory `TASKS` dictionary, and the existing error hierarchy contains `NotFoundError` and `ValidationError`. I explicitly rejected adding a new `DatabaseError` because it would unnecessarily expand the scope.

Claude's initial plan proposed changes to `process_order()`, `get_overdue_tasks()`, and `create_task()`, but it did not explicitly require running `pytest -q` after each method. I rejected that plan and required four constraints: modify only `services/tasks.py`, handle errors in the service methods, create no new files, and run `pytest -q` after each method was updated. Claude's revised plan respected these constraints.

The implementation added a `NotFoundError("Task")` check to `process_order()`, used `_parse_due_date()` in `get_overdue_tasks()` so malformed dates raise `ValidationError`, and changed task ID generation in `create_task()` to `max(TASKS, default=0) + 1`.

### Observation

The revised plan was more specific about file boundaries, the location of error handling, and test timing. The project did not have the database or repository layer assumed by the original prompt, so the implementation stayed within the existing in-memory service architecture. The final checks confirmed the expected error handling and empty-store behavior.

### Final Validation

- `pytest -q` — 6 passed.
- `pytest -v` — 6 passed.
- `ruff check .` — All checks passed.
- `process_order(999)` — Raised `NotFoundError` with status 404.
- Invalid stored due date — Raised `ValidationError` with status 422.
- Empty task store — `create_task()` assigned ID 1.
- Phase 3 implementation changes — Limited to `services/tasks.py`; earlier uncommitted `due_date` changes from Phase 1 remained in that file.

---

## Week 5 Drill 2 — Subagent Decomposition

### Prompt

> Add a tagging system. A task has zero or more tags (lowercase, max 32 chars, no spaces, stored in a join table called task_tags). Endpoints: POST /tasks/{id}/tags, DELETE /tasks/{id}/tags/{tag}, GET /tasks?tag={tag}. Decompose the feature into discrete subagent tasks before writing code.

### What Claude Did

I required exactly four subagents matching the project layers: SA-1 data/storage, SA-2 service, SA-3 API/routes, and SA-4 tests. Each had a stated Input, Task, Output, Constraint, and Hand-off, and `pytest -q` was required after each one. The full decomposition is in `DECOMPOSITION_DRILL2.md`.

- **SA-1** created `repositories/__init__.py` and `repositories/task_tags.py`. The `task_tags` join table is a module-level `TASK_TAGS` set of `(task_id, tag)` pairs, because the project has only an in-memory `TASKS` dictionary and no database. SA-1 ran its own gate: `pytest -q` was 6 passed before and after.
- **SA-2** proposed the tag functions, but its writes were denied. Its first attempt was fully denied. On a retry it added the import line to `services/tasks.py`, then the append of the functions was denied. After I reviewed the code, the orchestrating session applied the five functions (`_validate_tag`, `add_tag`, `remove_tag`, `get_tags`, `list_tasks`) in `services/tasks.py`.
- **SA-3** captured the before listing of route registrations and proposed the routes, but its edits to `routes/api.py` were denied. After review and revisions, the orchestrating session applied the three routes and the consolidated imports, then compared the registrations before and after. The four existing application routes were unchanged.
- **SA-4** drafted the tests, but its write was denied. The orchestrating session wrote the suite, dry-ran it from a scratchpad file (64 passed), and then created `tests/test_tags.py` with 58 tests after approval.

### Observation

Only SA-1 completed its own write and test gate. SA-2, SA-3, and SA-4 did not independently complete theirs: the orchestrating session applied or wrote their code and ran `pytest -q` and `ruff check .` itself, so the subagents were isolated by file boundaries but not by who did the work. SA-2 also left `services/tasks.py` with an import and no functions using it for a while, with no test run in that state.

Key divergences from the plan:

- **422, not 400.** The plan assumed invalid tags return 400, but the existing `ValidationError` returns 422. I kept `utils/errors.py` unchanged and the contract, API, and tests use 422.
- **`/api` prefix.** The blueprint is registered with `url_prefix="/api"`, so every real path starts with `/api`. The plan and subagent briefs omitted it, and the tests use the prefixed paths.
- **Malformed JSON handling.** The first routes called `request.get_json()` directly, so a bad body would give Flask's own 400 or 415. I revised `add_tag_route` to use `get_json(silent=True)` and raise `ValidationError("body", "must be a JSON object")`, which returns 422 through the existing `AppError` handler.
- **No repository layer.** `CLAUDE.md` describes routes → services → repositories, but no repository layer existed. SA-1 created a new `repositories/` package.

### Final Validation

- `pytest -q` — 64 passed (58 new, 6 existing).
- `ruff check .` — All checks passed.
- Route registrations — the four existing application rules are identical before and after; three rules were added.
- Files created or modified — `repositories/__init__.py`, `repositories/task_tags.py`, `services/tasks.py`, `routes/api.py`, `tests/test_tags.py`. `tests/test_tasks.py`, `utils/errors.py`, and `app.py` were not changed.
- Nothing was staged or committed.
