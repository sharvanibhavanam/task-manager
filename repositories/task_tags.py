TASK_TAGS: set[tuple[int, str]] = set()

def add_pair(task_id: int, tag: str) -> bool:
    """Add a (task_id, tag) pair to the store.

    Args:
        task_id: The unique identifier of the task.
        tag: The tag to associate with the task.

    Returns:
        True if the pair was newly added, False if it already existed.
    """
    pair = (task_id, tag)
    if pair in TASK_TAGS:
        return False
    TASK_TAGS.add(pair)
    return True

def remove_pair(task_id: int, tag: str) -> bool:
    """Remove a (task_id, tag) pair from the store.

    Args:
        task_id: The unique identifier of the task.
        tag: The tag to disassociate from the task.

    Returns:
        True if the pair existed and was removed, False otherwise.
    """
    pair = (task_id, tag)
    if pair not in TASK_TAGS:
        return False
    TASK_TAGS.remove(pair)
    return True

def pair_exists(task_id: int, tag: str) -> bool:
    """Check whether a (task_id, tag) pair is in the store.

    Args:
        task_id: The unique identifier of the task.
        tag: The tag to look for.

    Returns:
        True if the pair exists, False otherwise.
    """
    return (task_id, tag) in TASK_TAGS

def list_tags_for_task(task_id: int) -> list[str]:
    """List all tags associated with a task.

    Args:
        task_id: The unique identifier of the task.

    Returns:
        The task's tags sorted alphabetically. Empty if none exist.
    """
    return sorted(tag for tid, tag in TASK_TAGS if tid == task_id)

def list_task_ids_for_tag(tag: str) -> list[int]:
    """List all task IDs associated with a tag.

    Args:
        tag: The tag to look up.

    Returns:
        The IDs of tasks having the tag, sorted ascending. Empty if none exist.
    """
    return sorted(tid for tid, t in TASK_TAGS if t == tag)
