from datetime import date, datetime, timezone

from repositories import task_tags
from utils.errors import NotFoundError, ValidationError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1, "due_date": None, "priority": 3},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1, "due_date": None, "priority": 3},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2, "due_date": None, "priority": 3},
}

def _parse_due_date(due_date: str) -> date:
    """Parse and validate an ISO-8601 due date string.

    Args:
        due_date: The due date as an ISO-8601 string (e.g. "2026-10-20").

    Returns:
        The parsed date.

    Raises:
        ValidationError: If due_date is not a string or is not a valid ISO-8601
            date string.
    """
    try:
        return date.fromisoformat(due_date)
    except (TypeError, ValueError):
        raise ValidationError("due_date", "must be a valid ISO-8601 date string")

def _validate_priority(priority: int) -> int:
    """Validate a task priority.

    A valid priority is an integer from 1 (urgent) to 5 (low). Priorities are
    rejected, never coerced.

    Args:
        priority: The priority to validate.

    Returns:
        The priority, unchanged.

    Raises:
        ValidationError: If priority is not an integer or is outside 1-5.
    """
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError("priority", "must be an integer")
    if not 1 <= priority <= 5:
        raise ValidationError("priority", "must be between 1 and 5")
    return priority

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

def create_task(title: str, user_id: int, due_date: str | None = None, priority: int = 3) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The unique identifier of the user the task belongs to.
        due_date: The task's due date as an ISO-8601 string, or None if unset.
        priority: The task's priority from 1 (urgent) to 5 (low). Defaults to 3.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If due_date is provided but is not a valid ISO-8601 date string,
            or if priority is not an integer between 1 and 5.
    """
    if due_date is not None:
        _parse_due_date(due_date)
    _validate_priority(priority)
    new_id = max(TASKS, default=0) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False, "user_id": user_id, "due_date": due_date, "priority": priority}
    return TASKS[new_id]

def update_task(task_id: int, priority: int) -> dict:
    """Update a task's priority.

    The task is looked up before the priority is validated, so a missing task
    raises NotFoundError even if the priority is also invalid.

    Args:
        task_id: The ID of the task to update.
        priority: The new priority from 1 (urgent) to 5 (low).

    Returns:
        The updated task dictionary.

    Raises:
        NotFoundError: If the task does not exist.
        ValidationError: If priority is not an integer between 1 and 5.
    """
    task = get_task(task_id)
    _validate_priority(priority)
    task["priority"] = priority
    return task

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

def _validate_tag(tag: str) -> str:
    """Validate a tag string.

    A valid tag is a non-empty string, already lowercase, containing no
    whitespace, and at most 32 characters. Tags are rejected, never normalized.

    Args:
        tag: The tag to validate.

    Returns:
        The tag, unchanged.

    Raises:
        ValidationError: If tag is not a string, is empty, is not lowercase,
            contains whitespace, or is longer than 32 characters.
    """
    if not isinstance(tag, str):
        raise ValidationError("tag", "must be a string")
    if not tag:
        raise ValidationError("tag", "cannot be empty")
    if any(ch.isspace() for ch in tag):
        raise ValidationError("tag", "cannot contain whitespace")
    if tag != tag.lower():
        raise ValidationError("tag", "must be lowercase")
    if len(tag) > 32:
        raise ValidationError("tag", "must be at most 32 characters")
    return tag

def add_tag(task_id: int, tag: str) -> tuple[list[str], bool]:
    """Add a tag to a task. Adding an existing tag is idempotent.

    The tag is validated before the task is looked up.

    Args:
        task_id: The unique identifier for the task.
        tag: The tag to add.

    Returns:
        A tuple of the task's sorted tags and a flag that is True if the tag
        was newly added, False if the task already had it.

    Raises:
        ValidationError: If the tag is invalid.
        NotFoundError: If no task exists with the given ID.
    """
    _validate_tag(tag)
    get_task(task_id)
    created = task_tags.add_pair(task_id, tag)
    return task_tags.list_tags_for_task(task_id), created

def remove_tag(task_id: int, tag: str) -> None:
    """Remove a tag from a task.

    The tag is validated before the task is looked up.

    Args:
        task_id: The unique identifier for the task.
        tag: The tag to remove.

    Raises:
        ValidationError: If the tag is invalid.
        NotFoundError: If no task exists with the given ID, or the task does
            not have the tag.
    """
    _validate_tag(tag)
    get_task(task_id)
    if not task_tags.pair_exists(task_id, tag):
        raise NotFoundError("Tag")
    task_tags.remove_pair(task_id, tag)

def get_tags(task_id: int) -> list[str]:
    """Retrieve the tags of a task.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task's tags sorted alphabetically. Empty if none exist.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    get_task(task_id)
    return task_tags.list_tags_for_task(task_id)

def list_tasks(tag: str | None = None, priority: int | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by tag and/or priority.

    Args:
        tag: If provided, only tasks having this tag are returned. It is
            validated before filtering.
        priority: If provided, only tasks with this priority are returned. It
            is validated before filtering.

    Returns:
        A list of task records, ordered by task ID when filtering. Empty if
        none match.

    Raises:
        ValidationError: If tag or priority is provided but invalid.
    """
    if priority is not None:
        _validate_priority(priority)
    if tag is None:
        tasks = list(TASKS.values())
    else:
        _validate_tag(tag)
        tasks = [
            TASKS[task_id]
            for task_id in task_tags.list_task_ids_for_tag(tag)
            if task_id in TASKS
        ]
    if priority is None:
        return tasks
    return [task for task in tasks if task["priority"] == priority]
