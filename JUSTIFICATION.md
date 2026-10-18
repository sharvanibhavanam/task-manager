\# CLAUDE.md Justification



\## Commands



The Commands section gives Claude exact commands that work for this task-manager project instead of generic instructions. The project uses `pip install -r requirements.txt` for its dependencies, `pytest -v` for the test suite, and `ruff check .` for linting. During the final validation, `ruff check .` initially found six issues, including import formatting, an unused import, and broad exception assertions; after the automatic fixes and Ruff configuration, the command passed successfully. Including these concrete commands makes the instructions directly useful to Claude and provides a repeatable way to verify changes.



\## Architecture



The Architecture section tells Claude to keep the project organized around routes, services, and repositories while identifying actual project files as concrete patterns. In particular, `services/tasks.py` is where task business logic belongs, while `routes/api.py` is the canonical example for Flask routes and `AppError` handling. The `services/users.py` file provides an existing service-layer example that Claude successfully followed in all three sessions. This specificity helped prevent Claude from moving task logic into the API layer when making changes to `services/tasks.py`.



\## Conventions



The Conventions section focuses on patterns that were demonstrated by the existing code and tested during the Claude sessions. Type hints and Google-style docstrings are tied directly to `services/users.py`, while the error-handling rule specifies that `get\_task()` must raise `NotFoundError("Task")` for a missing task. Session 1 showed why this specificity was useful: after Claude followed the existing `get\_user()` pattern, I made the rule more explicit so the expected exception behavior was documented in `CLAUDE.md`. Session 2 also showed that Claude could apply the documented service style while preserving the existing `create\_task()` behavior.



\## Do Not Touch



The Do not touch section protects project-specific behavior that should not be changed casually. Function signatures in `services/tasks.py`, the `AppError` hierarchy in `utils/errors.py`, the error handler in `routes/api.py`, and the existing task tests are all explicitly protected. These rules are important because the assignment asks Claude to make targeted changes rather than redesign the project. They also reinforce the observation from Session 2 that requested style improvements should not unnecessarily change implementation logic.



\## Solo/Team Comparison



Working individually made it possible to observe exactly how each change to `CLAUDE.md` affected my own Claude Code sessions. I could compare the results from the first two sessions and make targeted updates based on what I actually observed rather than relying on a teammate's interpretation. The main benefit of the team approach would be having multiple people test the same instructions and identify additional edge cases. My individual process instead emphasized concrete project files, commands, and behaviors, resulting in instructions that became more specific after each session.



