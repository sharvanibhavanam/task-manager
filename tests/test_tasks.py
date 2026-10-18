import pytest

from services.tasks import get_task, get_tasks_by_user, process_order


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
