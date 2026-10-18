# Task Manager

Python Flask API for managing tasks and users.

## Commands
- Install dependencies with `pip install -r requirements.txt`.
- Run the full test suite with `pytest -v`.
- Run task tests with `pytest tests/test_tasks.py -v`.
- Run the Flask application with `python app.py`.
- Run the linter with `ruff check .`.

## Architecture
- Follow the layered pattern: routes → services → repositories.
- Keep task business logic in `services/tasks.py`, not in `routes/api.py`.
- Use `routes/api.py` as the canonical example for Flask routes and AppError handling.
- Use `services/users.py` as the canonical service-layer pattern.

## Conventions
- Use type hints on functions, following `services/users.py`.
- Use Google-style docstrings for service functions, following `services/users.py`; preserve existing implementation logic and formatting unless the requested change requires otherwise.
- Use `NotFoundError` and `ValidationError` from `utils/errors.py` for expected application errors; `get_task()` must raise `NotFoundError("Task")` when the task ID is missing.
- Follow the error-handling pattern used by `get_user()` in `services/users.py`.
- Keep task data in the existing structures in `services/tasks.py` unless the task requires a data-model change.

## Do not touch
- Do not change function signatures in `services/tasks.py` unless explicitly required.
- Do not replace the AppError hierarchy in `utils/errors.py` with raw `Exception`.
- Do not remove or bypass the `AppError` handler in `routes/api.py`.
- Do not modify existing tests in `tests/test_tasks.py` just to make an implementation pass.
