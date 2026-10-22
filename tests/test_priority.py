import copy

import pytest

from app import app as flask_app
from repositories import task_tags
from services.tasks import (
    TASKS,
    add_tag,
    create_task,
    get_task,
    get_tasks_by_user,
    list_tasks,
    process_order,
    update_task,
)
from utils.errors import NotFoundError, ValidationError

PAST = "2000-01-01"
FUTURE = "2999-01-01"

INT_ERROR = "Invalid priority: must be an integer"
RANGE_ERROR = "Invalid priority: must be between 1 and 5"

BAD_PRIORITIES = [
    (0, RANGE_ERROR),
    (6, RANGE_ERROR),
    (-1, RANGE_ERROR),
    ("high", INT_ERROR),
    ("3", INT_ERROR),
    (2.5, INT_ERROR),
    (True, INT_ERROR),
    (None, INT_ERROR),
    ([], INT_ERROR),
]
BAD_PRIORITY_IDS = [
    "zero", "six", "negative", "word", "numeric-string", "float", "bool", "null", "list",
]
# list_tasks treats None as "no filter", so it is not an invalid filter value.
BAD_FILTER_PRIORITIES = [(value, message) for value, message in BAD_PRIORITIES if value is not None]
BAD_FILTER_IDS = [name for name in BAD_PRIORITY_IDS if name != "null"]


@pytest.fixture(autouse=True)
def isolated_state():
    """Snapshot TASKS and TASK_TAGS, start with no tags, restore both afterwards."""
    tasks_snapshot = copy.deepcopy(TASKS)
    tags_snapshot = set(task_tags.TASK_TAGS)
    task_tags.TASK_TAGS.clear()
    try:
        yield
    finally:
        task_tags.TASK_TAGS.clear()
        task_tags.TASK_TAGS.update(tags_snapshot)
        TASKS.clear()
        TASKS.update(tasks_snapshot)

@pytest.fixture
def client():
    return flask_app.test_client()

def _ids(tasks):
    return [task["id"] for task in tasks]

def _create(client, **fields):
    body = {"title": "T", "user_id": 1, **fields}
    return client.post("/api/tasks", json=body).get_json()


# --- Service layer: create_task --------------------------------------------

def test_create_task_defaults_priority_to_3():
    task = create_task("T", 1)
    assert task["priority"] == 3
    assert TASKS[task["id"]] is task

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_create_task_stores_priority(priority):
    assert create_task("T", 1, None, priority)["priority"] == priority

@pytest.mark.parametrize("bad, message", BAD_PRIORITIES, ids=BAD_PRIORITY_IDS)
def test_create_task_rejects_invalid_priority(bad, message):
    before = dict(TASKS)
    with pytest.raises(ValidationError) as exc_info:
        create_task("T", 1, None, bad)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == message
    assert TASKS == before

def test_create_task_checks_due_date_before_priority():
    with pytest.raises(ValidationError) as exc_info:
        create_task("T", 1, "nope", 99)
    assert str(exc_info.value).startswith("Invalid due_date:")


# --- Service layer: update_task --------------------------------------------

def test_update_task_changes_priority_in_place():
    task = update_task(2, 1)
    assert task is TASKS[2]
    assert task["priority"] == 1

@pytest.mark.parametrize("bad, message", BAD_PRIORITIES, ids=BAD_PRIORITY_IDS)
def test_update_task_rejects_invalid_priority_and_leaves_task_unchanged(bad, message):
    before = TASKS[2]["priority"]
    with pytest.raises(ValidationError) as exc_info:
        update_task(2, bad)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == message
    assert TASKS[2]["priority"] == before

def test_update_task_missing_task_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        update_task(999, 1)
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "Task not found"

def test_update_task_looks_up_task_before_validating_priority():
    with pytest.raises(NotFoundError):
        update_task(999, 99)


# --- Service layer: list_tasks ---------------------------------------------

def test_list_tasks_filters_by_priority():
    update_task(1, 1)
    update_task(2, 5)
    assert _ids(list_tasks(priority=1)) == [1]
    assert _ids(list_tasks(priority=5)) == [2]
    assert _ids(list_tasks(priority=3)) == [3]
    assert list_tasks(priority=4) == []

def test_list_tasks_without_priority_is_unchanged():
    assert list_tasks() == list(TASKS.values())
    assert list_tasks(priority=None) == list(TASKS.values())

def test_list_tasks_combines_tag_and_priority():
    add_tag(1, "work")
    add_tag(2, "work")
    update_task(1, 1)
    assert _ids(list_tasks("work")) == [1, 2]
    assert _ids(list_tasks("work", 1)) == [1]
    assert _ids(list_tasks("work", 3)) == [2]
    assert list_tasks("work", 5) == []
    assert list_tasks("home", 1) == []

@pytest.mark.parametrize("bad, message", BAD_FILTER_PRIORITIES, ids=BAD_FILTER_IDS)
def test_list_tasks_rejects_invalid_priority(bad, message):
    with pytest.raises(ValidationError) as exc_info:
        list_tasks(priority=bad)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == message

def test_list_tasks_validates_priority_before_tag():
    with pytest.raises(ValidationError) as exc_info:
        list_tasks("Bad", 0)
    assert str(exc_info.value) == RANGE_ERROR
    with pytest.raises(ValidationError) as exc_info:
        list_tasks("Bad", 3)
    assert str(exc_info.value) == "Invalid tag: must be lowercase"


# --- API: POST /api/tasks --------------------------------------------------

def test_api_create_task_defaults_priority_to_3(client):
    response = client.post("/api/tasks", json={"title": "New", "user_id": 2})
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 4,
        "title": "New",
        "done": False,
        "user_id": 2,
        "due_date": None,
        "priority": 3,
    }

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_api_create_task_accepts_priority(client, priority):
    response = client.post(
        "/api/tasks", json={"title": "T", "user_id": 1, "priority": priority}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["priority"] == priority
    assert client.get(f"/api/tasks/{body['id']}").get_json()["priority"] == priority

@pytest.mark.parametrize("bad, message", BAD_PRIORITIES, ids=BAD_PRIORITY_IDS)
def test_api_create_task_rejects_invalid_priority(client, bad, message):
    before = len(TASKS)
    response = client.post("/api/tasks", json={"title": "T", "user_id": 1, "priority": bad})
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert len(TASKS) == before


# --- API: GET /api/tasks?priority= -----------------------------------------

def test_api_filter_by_priority_returns_only_matching_tasks(client):
    client.patch("/api/tasks/1", json={"priority": 1})
    client.patch("/api/tasks/2", json={"priority": 5})
    urgent = client.get("/api/tasks?priority=1")
    low = client.get("/api/tasks?priority=5")
    assert urgent.status_code == 200
    assert _ids(urgent.get_json()) == [1]
    assert _ids(low.get_json()) == [2]
    assert all(task["priority"] == 1 for task in urgent.get_json())

def test_api_filter_by_default_priority_returns_seed_tasks(client):
    response = client.get("/api/tasks?priority=3")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [1, 2, 3]

def test_api_filter_by_priority_with_no_match_returns_empty_list(client):
    response = client.get("/api/tasks?priority=4")
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_list_without_priority_returns_all_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [1, 2, 3]

def test_api_filter_by_tag_and_priority_applies_both(client):
    client.post("/api/tasks/1/tags", json={"tag": "work"})
    client.post("/api/tasks/2/tags", json={"tag": "work"})
    client.patch("/api/tasks/1", json={"priority": 1})
    assert _ids(client.get("/api/tasks?tag=work").get_json()) == [1, 2]
    assert _ids(client.get("/api/tasks?tag=work&priority=1").get_json()) == [1]
    assert _ids(client.get("/api/tasks?tag=work&priority=3").get_json()) == [2]
    assert client.get("/api/tasks?tag=work&priority=5").get_json() == []

@pytest.mark.parametrize(
    "value, message",
    [
        ("abc", INT_ERROR),
        ("2.5", INT_ERROR),
        ("", INT_ERROR),
        ("0", RANGE_ERROR),
        ("6", RANGE_ERROR),
        ("-1", RANGE_ERROR),
        ("99", RANGE_ERROR),
    ],
    ids=["word", "float", "empty", "zero", "six", "negative", "large"],
)
def test_api_filter_by_invalid_priority_returns_422(client, value, message):
    response = client.get("/api/tasks", query_string={"priority": value})
    assert response.status_code == 422
    assert response.get_json() == {"error": message}

def test_api_filter_by_tag_with_invalid_priority_returns_422(client):
    response = client.get("/api/tasks?tag=work&priority=0")
    assert response.status_code == 422
    assert response.get_json() == {"error": RANGE_ERROR}


# --- API: PATCH /api/tasks/<id> --------------------------------------------

def test_patch_route_registration():
    rules = [
        rule
        for rule in flask_app.url_map.iter_rules()
        if rule.endpoint == "api.update_task_route"
    ]
    assert len(rules) == 1
    assert rules[0].rule == "/api/tasks/<int:task_id>"
    assert rules[0].methods - {"HEAD", "OPTIONS"} == {"PATCH"}

def test_api_patch_updates_priority_and_persists(client):
    response = client.patch("/api/tasks/2", json={"priority": 1})
    assert response.status_code == 200
    assert response.get_json()["priority"] == 1
    assert client.get("/api/tasks/2").get_json()["priority"] == 1

def test_api_patch_returns_the_full_task(client):
    response = client.patch("/api/tasks/2", json={"priority": 5})
    assert response.status_code == 200
    assert response.get_json() == {
        "id": 2,
        "title": "Write report",
        "done": False,
        "user_id": 1,
        "due_date": None,
        "priority": 5,
    }

@pytest.mark.parametrize(
    "bad, message",
    BAD_PRIORITIES + [({}, INT_ERROR)],
    ids=BAD_PRIORITY_IDS + ["object"],
)
def test_api_patch_rejects_invalid_priority_and_leaves_task_unchanged(client, bad, message):
    before = client.get("/api/tasks/2").get_json()
    response = client.patch("/api/tasks/2", json={"priority": bad})
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert client.get("/api/tasks/2").get_json() == before

@pytest.mark.parametrize("body", [{}, {"title": "Renamed"}, {"done": True}])
def test_api_patch_missing_priority_key_returns_422(client, body):
    before = client.get("/api/tasks/2").get_json()
    response = client.patch("/api/tasks/2", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: is required"}
    assert client.get("/api/tasks/2").get_json() == before

@pytest.mark.parametrize("body", [[1, 2], "text", 5], ids=["list", "string", "number"])
def test_api_patch_non_object_body_returns_422(client, body):
    response = client.patch("/api/tasks/2", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

def test_api_patch_without_body_returns_422(client):
    response = client.patch("/api/tasks/2")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

def test_api_patch_malformed_json_returns_422(client):
    response = client.patch(
        "/api/tasks/2",
        data="{not valid json",
        content_type="application/json",
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

def test_api_patch_missing_task_returns_404(client):
    response = client.patch("/api/tasks/999", json={"priority": 2})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_patch_missing_task_is_404_before_priority_validation(client):
    response = client.patch("/api/tasks/999", json={"priority": 99})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_patch_checks_body_before_looking_up_task(client):
    response = client.patch("/api/tasks/999", json={})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid priority: is required"}

def test_api_patch_preserves_due_date_and_tags(client):
    task = _create(client, due_date=PAST)
    client.post(f"/api/tasks/{task['id']}/tags", json={"tag": "work"})
    patched = client.patch(f"/api/tasks/{task['id']}", json={"priority": 2}).get_json()
    assert patched["due_date"] == PAST
    assert _ids(client.get("/api/tasks?tag=work").get_json()) == [task["id"]]

def test_api_patch_does_not_change_overdue_membership(client):
    late = _create(client, due_date=PAST)
    before = _ids(client.get("/api/tasks/overdue").get_json())
    client.patch(f"/api/tasks/{late['id']}", json={"priority": 1})
    after = client.get("/api/tasks/overdue").get_json()
    assert _ids(after) == before == [late["id"]]
    assert after[0]["priority"] == 1


# --- Regression: existing behavior is unchanged ----------------------------

def test_regression_get_task_returns_record_with_default_priority(client):
    response = client.get("/api/tasks/2")
    assert response.status_code == 200
    assert response.get_json() == {
        "id": 2,
        "title": "Write report",
        "done": False,
        "user_id": 1,
        "due_date": None,
        "priority": 3,
    }

def test_regression_get_task_unknown_id_returns_404(client):
    response = client.get("/api/tasks/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_regression_service_retrieval_is_unchanged():
    assert get_task(2)["title"] == "Write report"
    assert {task["id"] for task in get_tasks_by_user(1)} == {1, 2}
    assert get_tasks_by_user(999) == []
    with pytest.raises(NotFoundError):
        get_task(999)

def test_regression_process_order_marks_done_and_keeps_priority():
    task = process_order(2)
    assert task["done"] is True
    assert task["priority"] == 3

def test_regression_create_task_with_due_date(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Dated task", "user_id": 1, "due_date": "2030-01-15"},
    )
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 4,
        "title": "Dated task",
        "done": False,
        "user_id": 1,
        "due_date": "2030-01-15",
        "priority": 3,
    }

def test_regression_due_date_and_priority_coexist(client):
    task = _create(client, due_date="2030-01-15", priority=1)
    assert task["due_date"] == "2030-01-15"
    assert task["priority"] == 1
    assert client.get(f"/api/tasks/{task['id']}").get_json() == task

def test_regression_invalid_due_date_returns_422(client):
    before = len(TASKS)
    response = client.post(
        "/api/tasks", json={"title": "T", "user_id": 1, "due_date": "nope"}
    )
    assert response.status_code == 422
    assert response.get_json() == {
        "error": "Invalid due_date: must be a valid ISO-8601 date string"
    }
    assert len(TASKS) == before

def test_regression_overdue_returns_only_overdue_tasks_with_priority(client):
    late = _create(client, due_date=PAST, priority=2)
    _create(client, due_date=FUTURE)
    done = _create(client, due_date=PAST)
    process_order(done["id"])
    response = client.get("/api/tasks/overdue")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [late["id"]]
    assert response.get_json()[0]["priority"] == 2

def test_regression_tagging_is_unchanged(client):
    first = client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    again = client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    assert first.status_code == 201
    assert first.get_json() == {"task_id": 2, "tags": ["urgent"]}
    assert again.status_code == 200
    assert _ids(client.get("/api/tasks?tag=urgent").get_json()) == [2]
    assert client.delete("/api/tasks/2/tags/urgent").status_code == 204
    assert client.get("/api/tasks?tag=urgent").get_json() == []
    invalid = client.post("/api/tasks/2/tags", json={"tag": "Urgent"})
    assert invalid.status_code == 422
    assert invalid.get_json() == {"error": "Invalid tag: must be lowercase"}


# --- Every endpoint that returns a task includes a valid priority ----------

def _tagged_list(client, query):
    client.post("/api/tasks/1/tags", json={"tag": "work"})
    return client.get(query).get_json()

def _late_overdue(client):
    _create(client, due_date=PAST)
    return client.get("/api/tasks/overdue").get_json()

TASK_ENDPOINTS = {
    "get_task": lambda c: [c.get("/api/tasks/2").get_json()],
    "post_task": lambda c: [c.post("/api/tasks", json={"title": "T", "user_id": 1}).get_json()],
    "patch_task": lambda c: [c.patch("/api/tasks/2", json={"priority": 4}).get_json()],
    "list_all": lambda c: c.get("/api/tasks").get_json(),
    "list_by_priority": lambda c: c.get("/api/tasks?priority=3").get_json(),
    "list_by_tag": lambda c: _tagged_list(c, "/api/tasks?tag=work"),
    "list_by_tag_and_priority": lambda c: _tagged_list(c, "/api/tasks?tag=work&priority=3"),
    "overdue": _late_overdue,
}

@pytest.mark.parametrize("name", list(TASK_ENDPOINTS))
def test_every_task_response_includes_valid_priority(client, name):
    tasks = TASK_ENDPOINTS[name](client)
    assert tasks, "endpoint returned no tasks to check"
    for task in tasks:
        assert "priority" in task
        assert isinstance(task["priority"], int)
        assert not isinstance(task["priority"], bool)
        assert 1 <= task["priority"] <= 5

def test_service_task_records_include_priority():
    assert all("priority" in task for task in list_tasks())
    assert all("priority" in task for task in get_tasks_by_user(1))
