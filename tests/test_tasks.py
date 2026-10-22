import copy
from datetime import datetime, timezone

import pytest

import services.tasks
from services.tasks import (
    TASKS,
    create_task,
    get_overdue_tasks,
    get_task,
    get_tasks_by_user,
    process_order,
)
from utils.errors import NotFoundError, ValidationError

TODAY = "2026-06-15"


@pytest.fixture(autouse=True)
def isolated_state():
    """Snapshot TASKS and restore it after every test."""
    tasks_snapshot = copy.deepcopy(TASKS)
    try:
        yield
    finally:
        TASKS.clear()
        TASKS.update(tasks_snapshot)

@pytest.fixture
def frozen_today(monkeypatch):
    """Pin get_overdue_tasks()'s notion of today to TODAY (UTC)."""
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(services.tasks, "datetime", FrozenDatetime)

def _ids(tasks):
    return [task["id"] for task in tasks]


def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
        get_task(999)

def test_get_tasks_by_user_valid():
    result = get_tasks_by_user(1)
    assert {task["id"] for task in result} == {1, 2}

def test_get_tasks_by_user_no_tasks():
    result = get_tasks_by_user(999)
    assert result == []


# --- process_order -----------------------------------------------------------

def test_process_order_missing_task_raises_not_found():
    before = copy.deepcopy(TASKS)
    with pytest.raises(NotFoundError) as exc_info:
        process_order(999)
    assert str(exc_info.value) == "Task not found"
    assert exc_info.value.status_code == 404
    assert TASKS == before

def test_process_order_persists_and_returns_stored_record():
    result = process_order(2)
    assert result is TASKS[2]
    assert get_task(2)["done"] is True

def test_process_order_already_done_task_is_idempotent():
    before = copy.deepcopy(TASKS[3])
    result = process_order(3)
    assert result == before


# --- get_task ----------------------------------------------------------------

def test_get_task_missing_task_message_and_status():
    with pytest.raises(NotFoundError) as exc_info:
        get_task(999)
    assert str(exc_info.value) == "Task not found"
    assert exc_info.value.status_code == 404


# --- create_task -------------------------------------------------------------

def test_create_task_returns_and_stores_full_record():
    task = create_task("New", 2)
    assert task == {
        "id": 4, "title": "New", "done": False, "user_id": 2, "due_date": None, "priority": 3,
    }
    assert get_task(4) is task
    assert task in get_tasks_by_user(2)

def test_create_task_assigns_id_after_highest_existing_id():
    del TASKS[2]
    assert create_task("New", 1)["id"] == 4

def test_create_task_into_empty_store_starts_at_id_1():
    TASKS.clear()
    assert create_task("First", 1)["id"] == 1

def test_create_task_stores_due_date_string_unchanged():
    assert create_task("New", 1, "2030-01-15")["due_date"] == "2030-01-15"

@pytest.mark.parametrize(
    "bad_due_date",
    ["nope", "2026-02-30", "", 20261020, ["2026-10-20"]],
    ids=["word", "impossible-date", "empty", "int", "list"],
)
def test_create_task_rejects_invalid_due_date_and_stores_nothing(bad_due_date):
    before = copy.deepcopy(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        create_task("New", 1, bad_due_date)
    assert str(exc_info.value) == "Invalid due_date: must be a valid ISO-8601 date string"
    assert exc_info.value.status_code == 422
    assert TASKS == before


# --- get_overdue_tasks -------------------------------------------------------

def test_get_overdue_tasks_seed_data_has_none(frozen_today):
    assert get_overdue_tasks() == []

def test_get_overdue_tasks_includes_only_past_due_open_tasks(frozen_today):
    late = create_task("Late", 1, "2026-06-14")
    create_task("Due today", 1, TODAY)
    create_task("Future", 1, "2026-06-16")
    create_task("No due date", 1)
    done = create_task("Late but done", 1, "2000-01-01")
    process_order(done["id"])
    assert _ids(get_overdue_tasks()) == [late["id"]]

def test_get_overdue_tasks_returns_tasks_in_id_order(frozen_today):
    first = create_task("A", 1, "2026-01-01")
    second = create_task("B", 2, "2000-01-01")
    assert _ids(get_overdue_tasks()) == [first["id"], second["id"]]

def test_get_overdue_tasks_invalid_stored_due_date_raises_validation_error(frozen_today):
    TASKS[1]["due_date"] = "not-a-date"
    with pytest.raises(ValidationError) as exc_info:
        get_overdue_tasks()
    assert str(exc_info.value) == "Invalid due_date: must be a valid ISO-8601 date string"
