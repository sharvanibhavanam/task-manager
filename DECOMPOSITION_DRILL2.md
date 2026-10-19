# Week 5 Drill 2 — Manual Subagent Decomposition

## Project Architecture Note

The current Task Manager project has `routes/`, `services/`, `tests/`, and `utils/`, but no `models/` or `migrations/` directories. The existing task storage is an in-memory dictionary. The requested `task_tags` join table therefore does not map directly to the current architecture. Inspect the existing code before implementation and document any required architectural decision; do not claim a database table or migration exists unless it is actually implemented.

### Architectural decision (recorded after execution)

No database table or migration was created. The `task_tags` join table is represented as a module-level `TASK_TAGS: set[tuple[int, str]]` of `(task_id, tag)` pairs in a new `repositories/task_tags.py`. Each pair is one join row, and the set enforces uniqueness of the pair. `TASKS` records are unchanged, so existing task JSON is identical. `CLAUDE.md` names a routes → services → repositories layering, but no `repositories/` directory existed, so SA-1 created a minimal one.

### Contract decisions fixed before implementation

- Tag validation lives in the service layer only: a `str`, non-empty, lowercase, no whitespace, at most 32 characters. Invalid tags are rejected, never normalized.
- Adding a duplicate tag is idempotent: 201 for a new pair, 200 for an existing one.
- A missing task raises `NotFoundError("Task")` (404). Removing a tag the task does not have raises `NotFoundError("Tag")` (404).
- An invalid tag raises the existing `ValidationError`, which returns 422 (the original plan assumed 400; see Divergence).
- A missing, malformed, or non-object JSON body on POST raises `ValidationError("body", "must be a JSON object")` (422).
- `GET /tasks` did not exist, so it was added; with no `tag` it returns all tasks.
- The blueprint is registered with `url_prefix="/api"`, so every real path starts with `/api` (see Divergence).

## SA-1: Data and Storage Layer

- **Subagent #:** 1
- **Input:** `services/tasks.py`, `services/users.py`, `utils/errors.py`, and `CLAUDE.md`.
- **Task:** Determine and implement how task-tag associations will be stored while preserving the requirement for a `task_tags` join-table structure rather than comma-separated tag values.
- **Output:** The exact storage file or files justified by the existing architecture. Actual: created `repositories/__init__.py` (empty) and `repositories/task_tags.py`.
- **Constraint:** Do not modify `routes/`, `tests/`, or `utils/errors.py`. Do not invent a database or migration system without documenting the architectural change.
- **Hand-off:** Provide the storage representation, its operations, validation assumptions, and exact filenames to SA-2. Actual: `TASK_TAGS`, `add_pair(task_id, tag) -> bool`, `remove_pair(task_id, tag) -> bool`, `pair_exists(task_id, tag) -> bool`, `list_tags_for_task(task_id) -> list[str]`, and `list_task_ids_for_tag(tag) -> list[int]`, all in `repositories/task_tags.py`. The store does no validation; that was left to the service layer.
- **Result:** `pytest -q` after SA-1: 6 passed (the baseline before SA-1 was also 6 passed). `ruff check .` passed.

## SA-2: Service Layer

- **Subagent #:** 2
- **Input:** `services/tasks.py`, `services/users.py`, `utils/errors.py`, and the exact storage artifacts produced by SA-1.
- **Task:** Implement service operations to add a tag, remove a tag, and retrieve tasks by tag, using existing `AppError` subclasses for failures and enforcing lowercase, no spaces, and a maximum length of 32 characters.
- **Output:** `services/tasks.py` and any additional service file only if justified by the existing architecture. Actual: modified `services/tasks.py` only. SA-2 added the import `from repositories import task_tags`. The five new functions `_validate_tag`, `add_tag`, `remove_tag`, `get_tags`, and `list_tasks` were proposed by SA-2 and appended by the orchestrating session after review (see Divergence).
- **Constraint:** Do not modify `routes/` or `tests/`. Do not change the storage contract established by SA-1 without coordinating the hand-off.
- **Hand-off:** Provide exact service function names, arguments, return shapes, and error behavior to SA-3. Actual:
  - `add_tag(task_id: int, tag: str) -> tuple[list[str], bool]` returns `(sorted tags, newly_created)`; raises `ValidationError`, then `NotFoundError("Task")`.
  - `remove_tag(task_id: int, tag: str) -> None`; raises `ValidationError`, then `NotFoundError("Task")`, then `NotFoundError("Tag")`.
  - `get_tags(task_id: int) -> list[str]`; raises `NotFoundError("Task")`.
  - `list_tasks(tag: str | None = None) -> list[dict]`; raises `ValidationError` when a tag is given but invalid.
  - The tag is validated before the task is looked up, and `ValidationError` has status 422.
- **Result:** SA-2's first attempt was denied and never ran `pytest`. After the approved edit was applied, `pytest -q` gave 6 passed and `ruff check .` passed. No test or lint run was made in the intermediate state where only the import existed.

## SA-3: API Layer

- **Subagent #:** 3
- **Input:** `routes/api.py`, `services/tasks.py`, `CLAUDE.md`, and the exact service contract from SA-2.
- **Task:** Add `POST /tasks/{id}/tags`, `DELETE /tasks/{id}/tags/{tag}`, and the `tag` filter on `GET /tasks`. Added requirement: compare the Flask route registrations before and after to confirm the existing routes are unaffected.
- **Output:** `routes/api.py`. Actual: modified `routes/api.py` only. The `services.tasks` imports were consolidated into one `from services.tasks import (...)` statement, `ValidationError` was added to the `utils.errors` import, and three routes were appended: `list_tasks_route`, `add_tag_route`, and `remove_tag_route`. SA-3 captured the before listing and proposed the routes; the orchestrating session applied the edits after review, with the JSON-body handling revised per the reviewer.
- **Constraint:** Do not modify `services/`, `tests/`, or the storage implementation. Route handlers must use the service functions from SA-2 rather than implementing tag logic directly.
- **Hand-off:** Document endpoint request formats, response formats, and error behavior for SA-4. Actual (all paths under `/api`):

  | Endpoint (endpoint name) | Request | Success | Errors |
  |---|---|---|---|
  | `GET /api/tasks` (`api.list_tasks_route`) | optional `?tag=x` | 200, list (`[]` if no match) | 422 invalid or empty tag |
  | `POST /api/tasks/<id>/tags` (`api.add_tag_route`) | JSON `{"tag": "<str>"}` | 201 new, 200 duplicate; `{"task_id", "tags"}` | 422 invalid, missing, or non-string tag, or non-object, missing, or malformed body; 404 Task |
  | `DELETE /api/tasks/<id>/tags/<tag>` (`api.remove_tag_route`) | none | 204, empty body | 422 invalid tag; 404 Task; 404 Tag |

  Route registrations before and after: the four existing application rules (`POST /api/tasks`, `GET /api/tasks/<int:task_id>`, `GET /api/tasks/overdue`, `GET /api/users/<int:user_id>`) are identical in path, methods, endpoint name, and view function. Three rules were added.
- **Result:** `pytest -q` after SA-3: 6 passed; `ruff check .` passed. SA-3's own gate never ran because its writes were denied, so these results come from the orchestrating session after the edits were applied.

## SA-4: Tests

- **Subagent #:** 4
- **Input:** `tests/test_tasks.py`, `routes/api.py`, `services/tasks.py`, and the documented API/service contracts from SA-2 and SA-3.
- **Task:** Add tests covering tag addition, removal, filtering, and invalid tag values, then ensure the test suite passes. Added requirement: regression tests for the existing routes and a route-registration test checking the exact path, method set, and endpoint name of each rule.
- **Output:** `tests/test_tasks.py` and any separate test file only if justified. Actual: created `tests/test_tags.py` (58 tests). `tests/test_tasks.py` was left unmodified, so the existing tests stayed untouched and the new work could be reviewed on its own.
- **Constraint:** Do not modify application code. Report failures to the responsible subagent rather than silently changing service or route implementations.
- **Hand-off:** Provide test results, including the exact `pytest -q` outcome, and list any unresolved failures. Actual: 64 passed (6 existing plus 58 new). `ruff check .` passed. There are no unresolved failures, and the tests exposed no application bugs.
- **Result:** `pytest -q` after SA-4: 64 passed. SA-4's own write was denied; the orchestrating session wrote the file from a draft it had dry-run from the scratchpad (64 passed) before approval.

## Divergence

**Did the boundaries hold?** Partly. In terms of files, yes: no layer modified a file outside its listed output. SA-1 created exactly its two files. `utils/errors.py`, `app.py`, `tests/test_tasks.py`, and `CLAUDE.md` were not touched. The existing routes, the `AppError` handler, and all existing function signatures are unchanged. In terms of who did the work, the isolation did not hold. Write permission was denied to SA-2, SA-3, and SA-4 in their own sessions, so the orchestrating session applied SA-2's reviewed code, applied SA-3's routes with revisions, and wrote SA-4's test file itself. SA-3 and SA-4 never ran their own `pytest -q` gates; the orchestrator ran them after each change. SA-2 also left the repo half-applied for a while, with the new import present and the functions that use it not yet appended, and no test run in that state.

**Did any output break a downstream assumption?** Yes, four times:

1. **Status code.** The plan said invalid tags return 400. SA-2 found that `ValidationError` in `utils/errors.py` returns 422, and `utils/errors.py` was off-limits. The contract was changed to 422, and SA-3 and SA-4 were briefed with the new value.
2. **URL prefix.** The plan and the SA-3 and SA-4 briefs used paths such as `/tasks/{id}/tags`. SA-3's before listing showed the blueprint is registered under `url_prefix="/api"`, so every real path starts with `/api`. SA-4's paths and registration test had to use the prefixed paths.
3. **JSON body handling.** SA-3's first routes called `request.get_json()` directly, so a malformed body or wrong content type would have produced Flask's own 400 or 415 instead of the project's `AppError` response. This was revised to `get_json(silent=True)` with `ValidationError("body", "must be a JSON object")`, which required importing `ValidationError` into `routes/api.py`.
4. **Repository layer.** `CLAUDE.md` describes routes → services → repositories, but no repository layer existed. SA-1 created a new `repositories/` package, which the original architecture note did not anticipate. The decision is recorded in the architecture note above.

**What should change next time:**

- Read `utils/errors.py` and `app.py` before writing the contract, so the status codes and URL prefix are known before any subagent is briefed.
- Settle write permissions for each subagent before launching it, or have subagents write drafts to a scratchpad by default and let the orchestrator apply them. This avoids discovering denials mid-run.
- Require each subagent to leave the repo consistent, applying an import and the code that uses it in one edit, so no intermediate state fails lint or tests.
- Keep edits and test commands separate, which is what finally worked, and have each subagent report its own `pytest -q` result rather than relying on the orchestrator to run it.
- Have the orchestrator record exactly which edits it authored or revised, so the hand-off log shows who wrote what.
