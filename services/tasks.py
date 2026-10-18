from utils.errors import NotFoundError

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries",  "done": False, "user_id": 1},
    2: {"id": 2, "title": "Write report",   "done": False, "user_id": 1},
    3: {"id": 3, "title": "Call dentist",   "done": True,  "user_id": 2},
}

def process_order(task_id: int) -> dict:
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

def create_task(title: str, user_id: int) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The unique identifier of the user the task belongs to.

    Returns:
        The newly created task record.
    """
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {"id": new_id, "title": title, "done": False, "user_id": user_id}
    return TASKS[new_id]
