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



