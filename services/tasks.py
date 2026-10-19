from datetime import date, datetime, timezone

from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "due_date": None},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "due_date": None},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "due_date": None},
}

def _parse_due_date(due_date: str) -> date:
    """Parse and validate an ISO-8601 due date string.

    Args:
        due_date: The due date as an ISO-8601 string (e.g. "2026-10-20").

    Returns:
        The parsed date.

    Raises:
        ValidationError: If due_date is not a valid ISO-8601 date string.
    """
    try:
        return date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError("due_date", "must be a valid ISO-8601 date string")

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    task = TASKS[task_id]
    task["done"] = True
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def get_tasks_by_user(user_id: int) -> list[dict]:
    """Retrieve all tasks belonging to a given user.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        A list of task records belonging to the user. Empty if none exist.
    """
    return [task for task in TASKS.values() if task["user_id"] == user_id]

def create_task(title: str, user_id: int, due_date: str | None = None) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The unique identifier of the user the task belongs to.
        due_date: The task's due date as an ISO-8601 string, or None if unset.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If due_date is provided but is not a valid ISO-8601 date string.
    """
    if due_date is not None:
        _parse_due_date(due_date)
    new_id = max(TASKS, default=0) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False, "user_id": user_id, "due_date": due_date}
    return TASKS[new_id]

def get_overdue_tasks() -> list[dict]:
    """Retrieve all tasks that are overdue.

    A task is overdue when it has a due_date earlier than today and its
    done status is not True.

    Returns:
        A list of overdue task records. Empty if none exist.

    Raises:
        ValidationError: If a stored due_date is not a valid ISO-8601 date string.
    """
    today = datetime.now(tz=timezone.utc).date()
    return [
        task
        for task in TASKS.values()
        if task["due_date"] is not None
        and _parse_due_date(task["due_date"]) < today
        and not task["done"]
    ]
