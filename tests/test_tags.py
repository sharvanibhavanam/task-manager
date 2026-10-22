import copy

import pytest

from app import app as flask_app
from repositories import task_tags
from services.tasks import (
    TASKS,
    add_tag,
    get_tags,
    list_tasks,
    remove_tag,
)
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def isolated_state():
    """Reset TASK_TAGS and restore TASKS around every test."""
    tasks_snapshot = copy.deepcopy(TASKS)
    task_tags.TASK_TAGS.clear()
    yield
    task_tags.TASK_TAGS.clear()
    TASKS.clear()
    TASKS.update(tasks_snapshot)

@pytest.fixture
def client():
    return flask_app.test_client()

def _ids(tasks):
    return [task["id"] for task in tasks]


# --- Service layer ---------------------------------------------------------

def test_add_tag_new_tag_is_created():
    tags, created = add_tag(2, "urgent")
    assert tags == ["urgent"]
    assert created is True
    assert get_tags(2) == ["urgent"]

def test_add_tag_duplicate_is_idempotent():
    add_tag(2, "urgent")
    tags, created = add_tag(2, "urgent")
    assert tags == ["urgent"]
    assert created is False
    assert len(task_tags.TASK_TAGS) == 1

def test_add_tag_returns_sorted_tags():
    add_tag(2, "beta")
    tags, _ = add_tag(2, "alpha")
    assert tags == ["alpha", "beta"]

def test_add_tag_accepts_32_character_tag():
    tag = "a" * 32
    tags, created = add_tag(2, tag)
    assert tags == [tag]
    assert created is True

@pytest.mark.parametrize(
    "bad_tag",
    ["", "Urgent", "two words", "tab\ttag", "a" * 33, 123, None, True],
    ids=["empty", "uppercase", "space", "tab", "33-chars", "int", "none", "bool"],
)
def test_add_tag_rejects_invalid_tag(bad_tag):
    with pytest.raises(ValidationError) as exc_info:
        add_tag(2, bad_tag)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value).startswith("Invalid tag:")
    assert task_tags.TASK_TAGS == set()

def test_add_tag_missing_task_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        add_tag(999, "urgent")
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "Task not found"

def test_add_tag_validates_tag_before_looking_up_task():
    with pytest.raises(ValidationError):
        add_tag(999, "BAD")

def test_remove_tag_existing_tag():
    add_tag(2, "urgent")
    remove_tag(2, "urgent")
    assert get_tags(2) == []

def test_remove_tag_missing_tag_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        remove_tag(2, "urgent")
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == "Tag not found"

def test_remove_tag_missing_task_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        remove_tag(999, "urgent")
    assert str(exc_info.value) == "Task not found"

def test_remove_tag_invalid_tag_raises_validation_error():
    with pytest.raises(ValidationError):
        remove_tag(2, "Urgent")

def test_get_tags_without_tags_is_empty():
    assert get_tags(2) == []

def test_get_tags_missing_task_raises_not_found():
    with pytest.raises(NotFoundError):
        get_tags(999)

def test_list_tasks_unfiltered_returns_all_tasks():
    assert _ids(list_tasks()) == [1, 2, 3]
    assert list_tasks() == list(TASKS.values())

def test_list_tasks_filtered_hit():
    add_tag(1, "work")
    add_tag(2, "work")
    add_tag(3, "home")
    assert _ids(list_tasks("work")) == [1, 2]

def test_list_tasks_filtered_miss_is_empty():
    add_tag(1, "work")
    assert list_tasks("home") == []

def test_list_tasks_invalid_tag_raises_validation_error():
    with pytest.raises(ValidationError):
        list_tasks("Work")

def test_list_tasks_skips_task_ids_missing_from_tasks():
    task_tags.TASK_TAGS.add((999, "ghost"))
    assert list_tasks("ghost") == []


# --- API: POST /api/tasks/<id>/tags ----------------------------------------

def test_api_add_tag_new_returns_201(client):
    response = client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    assert response.status_code == 201
    assert response.get_json() == {"task_id": 2, "tags": ["urgent"]}

def test_api_add_tag_duplicate_returns_200(client):
    client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    response = client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    assert response.status_code == 200
    assert response.get_json() == {"task_id": 2, "tags": ["urgent"]}

def test_api_add_tag_invalid_tag_returns_422(client):
    response = client.post("/api/tasks/2/tags", json={"tag": "Urgent"})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be lowercase"}

def test_api_add_tag_too_long_returns_422(client):
    response = client.post("/api/tasks/2/tags", json={"tag": "a" * 33})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be at most 32 characters"}

def test_api_add_tag_missing_tag_key_returns_422(client):
    response = client.post("/api/tasks/2/tags", json={})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be a string"}

def test_api_add_tag_non_string_tag_returns_422(client):
    response = client.post("/api/tasks/2/tags", json={"tag": 5})
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be a string"}

def test_api_add_tag_missing_task_returns_404(client):
    response = client.post("/api/tasks/999/tags", json={"tag": "urgent"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_add_tag_without_body_returns_422(client):
    response = client.post("/api/tasks/2/tags")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

def test_api_add_tag_malformed_json_returns_422(client):
    response = client.post(
        "/api/tasks/2/tags",
        data="{not valid json",
        content_type="application/json",
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}

def test_api_add_tag_non_object_json_returns_422(client):
    response = client.post("/api/tasks/2/tags", json=["urgent"])
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid body: must be a JSON object"}


# --- API: DELETE /api/tasks/<id>/tags/<tag> --------------------------------

def test_api_remove_tag_returns_204_and_removes_tag(client):
    client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    response = client.delete("/api/tasks/2/tags/urgent")
    assert response.status_code == 204
    assert response.data == b""
    assert get_tags(2) == []

def test_api_remove_tag_missing_tag_returns_404(client):
    response = client.delete("/api/tasks/2/tags/urgent")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Tag not found"}

def test_api_remove_tag_missing_task_returns_404(client):
    response = client.delete("/api/tasks/999/tags/urgent")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_remove_tag_invalid_tag_returns_422(client):
    response = client.delete("/api/tasks/2/tags/Urgent")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be lowercase"}


# --- API: GET /api/tasks and GET /api/tasks?tag= ---------------------------

def test_api_list_tasks_unfiltered_returns_all_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [1, 2, 3]

def test_api_list_tasks_filtered_hit(client):
    client.post("/api/tasks/1/tags", json={"tag": "work"})
    client.post("/api/tasks/3/tags", json={"tag": "work"})
    client.post("/api/tasks/2/tags", json={"tag": "home"})
    response = client.get("/api/tasks?tag=work")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [1, 3]

def test_api_list_tasks_filtered_miss_returns_empty_list(client):
    response = client.get("/api/tasks?tag=nothing")
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_list_tasks_invalid_tag_returns_422(client):
    response = client.get("/api/tasks?tag=Bad")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: must be lowercase"}

def test_api_list_tasks_empty_tag_param_returns_422(client):
    response = client.get("/api/tasks?tag=")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: cannot be empty"}

def test_api_removed_tag_no_longer_filters_task(client):
    client.post("/api/tasks/2/tags", json={"tag": "urgent"})
    client.delete("/api/tasks/2/tags/urgent")
    response = client.get("/api/tasks?tag=urgent")
    assert response.status_code == 200
    assert response.get_json() == []


# --- Regression: existing routes are unchanged -----------------------------

def test_regression_get_task_returns_record(client):
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

def test_regression_create_task_without_due_date(client):
    response = client.post("/api/tasks", json={"title": "New task", "user_id": 1})
    assert response.status_code == 201
    assert response.get_json() == {
        "id": 4,
        "title": "New task",
        "done": False,
        "user_id": 1,
        "due_date": None,
        "priority": 3,
    }

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

def test_regression_overdue_route_is_not_captured_by_task_id_route(client):
    response = client.get("/api/tasks/overdue")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_regression_overdue_route_returns_only_overdue_tasks(client):
    client.post("/api/tasks", json={"title": "Late", "user_id": 1, "due_date": "2000-01-01"})
    client.post("/api/tasks", json={"title": "Later", "user_id": 1, "due_date": "2999-01-01"})
    response = client.get("/api/tasks/overdue")
    assert response.status_code == 200
    assert _ids(response.get_json()) == [4]


# --- Route registration ----------------------------------------------------

EXPECTED_ROUTES = [
    ("/api/tasks", {"GET"}, "api.list_tasks_route"),
    ("/api/tasks", {"POST"}, "api.create_task_route"),
    ("/api/tasks/<int:task_id>", {"GET"}, "api.get_task_route"),
    ("/api/tasks/overdue", {"GET"}, "api.get_overdue_tasks_route"),
    ("/api/users/<int:user_id>", {"GET"}, "api.get_user_route"),
    ("/api/tasks/<int:task_id>/tags", {"POST"}, "api.add_tag_route"),
    ("/api/tasks/<int:task_id>/tags/<tag>", {"DELETE"}, "api.remove_tag_route"),
]

def _registered_routes():
    return {
        (rule.rule, frozenset(rule.methods - {"HEAD", "OPTIONS"})): rule.endpoint
        for rule in flask_app.url_map.iter_rules()
    }

@pytest.mark.parametrize(
    "path, methods, endpoint",
    EXPECTED_ROUTES,
    ids=[f"{'/'.join(sorted(m))} {p}" for p, m, _ in EXPECTED_ROUTES],
)
def test_route_registration(path, methods, endpoint):
    routes = _registered_routes()
    assert routes.get((path, frozenset(methods))) == endpoint
    assert flask_app.view_functions[endpoint].__name__ == endpoint.split(".")[1]
