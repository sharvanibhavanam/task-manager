import copy

import pytest

from app import app as flask_app
from services.users import (
    NOTIFICATION_PREFS,
    USERS,
    create_user,
    get_notification_pref,
    get_user,
    list_users,
    update_notification_pref,
)
from utils.errors import NotFoundError, ValidationError

VALID_PREFS = ["email", "sms", "none"]

PREF_ERROR = "Invalid notification_pref: must be one of email, sms, none"
REQUIRED_ERROR = "Invalid notification_pref: is required"
BODY_ERROR = "Invalid body: must be a JSON object"
USER_NOT_FOUND = "User not found"

BAD_PREFS = [
    None, 1, 1.5, True, False, [], ["email"], {},
    "EMAIL", "Email", " sms", "sms ", "", "push",
]
BAD_PREF_IDS = [
    "null", "int", "float", "true", "false", "empty-list", "list", "object",
    "uppercase", "capitalized", "leading-space", "trailing-space", "empty-string", "unknown",
]

ALICE = {"id": 1, "name": "Alice", "email": "alice@example.com", "notification_pref": "none"}
BOB = {"id": 2, "name": "Bob", "email": "bob@example.com", "notification_pref": "none"}


@pytest.fixture(autouse=True)
def isolated_users():
    """Snapshot USERS and restore it afterwards."""
    users_snapshot = copy.deepcopy(USERS)
    try:
        yield
    finally:
        USERS.clear()
        USERS.update(users_snapshot)

@pytest.fixture
def client():
    return flask_app.test_client()

def _ids(users):
    return [user["id"] for user in users]


# --- Default and storage ---------------------------------------------------

def test_notification_prefs_are_email_sms_none():
    assert NOTIFICATION_PREFS == ("email", "sms", "none")

def test_seed_users_default_to_none():
    assert USERS[1] == ALICE
    assert USERS[2] == BOB

def test_create_user_defaults_to_none():
    user = create_user("Carol", "carol@example.com")
    assert user == {
        "id": 3,
        "name": "Carol",
        "email": "carol@example.com",
        "notification_pref": "none",
    }
    assert USERS[3] is user

def test_no_user_record_stores_none():
    create_user("Carol", "carol@example.com")
    for user in USERS.values():
        assert user["notification_pref"] is not None
        assert user["notification_pref"] in NOTIFICATION_PREFS


# --- Service layer: get_notification_pref / update_notification_pref -------

def test_get_notification_pref_returns_default():
    assert get_notification_pref(1) == "none"

@pytest.mark.parametrize("pref", VALID_PREFS)
def test_update_notification_pref_accepts_and_persists(pref):
    user = update_notification_pref(1, pref)
    assert user is USERS[1]
    assert user["notification_pref"] == pref
    assert get_notification_pref(1) == pref
    assert get_user(1)["notification_pref"] == pref

def test_update_notification_pref_only_changes_target_user():
    update_notification_pref(1, "email")
    assert USERS[1] == {**ALICE, "notification_pref": "email"}
    assert USERS[2] == BOB

@pytest.mark.parametrize("bad", BAD_PREFS, ids=BAD_PREF_IDS)
def test_update_notification_pref_rejects_invalid_value_and_leaves_user_unchanged(bad):
    update_notification_pref(1, "sms")
    before = copy.deepcopy(USERS[1])
    with pytest.raises(ValidationError) as exc_info:
        update_notification_pref(1, bad)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == PREF_ERROR
    assert USERS[1] == before

def test_get_notification_pref_missing_user_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        get_notification_pref(999)
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == USER_NOT_FOUND

def test_update_notification_pref_missing_user_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        update_notification_pref(999, "email")
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == USER_NOT_FOUND
    assert 999 not in USERS

@pytest.mark.parametrize("bad", BAD_PREFS, ids=BAD_PREF_IDS)
def test_update_notification_pref_looks_up_user_before_validating(bad):
    with pytest.raises(NotFoundError) as exc_info:
        update_notification_pref(999, bad)
    assert str(exc_info.value) == USER_NOT_FOUND


# --- Service layer: list_users ---------------------------------------------

def test_list_users_returns_all_users_with_notification_pref():
    create_user("Carol", "carol@example.com")
    users = list_users()
    assert _ids(users) == [1, 2, 3]
    assert all(user["notification_pref"] == "none" for user in users)

def test_list_users_orders_by_id():
    USERS[5] = {"id": 5, "name": "Eve", "email": "eve@example.com", "notification_pref": "sms"}
    USERS[4] = {"id": 4, "name": "Dan", "email": "dan@example.com", "notification_pref": "email"}
    assert _ids(list_users()) == [1, 2, 4, 5]


# --- API: GET /api/users/<id>/notifications --------------------------------

def test_api_get_notification_pref_returns_default(client):
    response = client.get("/api/users/1/notifications")
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": "none"}

def test_api_get_notification_pref_unknown_user_returns_404(client):
    response = client.get("/api/users/999/notifications")
    assert response.status_code == 404
    assert response.get_json() == {"error": USER_NOT_FOUND}


# --- API: PATCH /api/users/<id>/notifications ------------------------------

@pytest.mark.parametrize("pref", VALID_PREFS)
def test_api_patch_accepts_and_persists(client, pref):
    response = client.patch("/api/users/2/notifications", json={"notification_pref": pref})
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 2, "notification_pref": pref}
    assert client.get("/api/users/2/notifications").get_json() == {
        "user_id": 2,
        "notification_pref": pref,
    }
    assert client.get("/api/users/2").get_json()["notification_pref"] == pref
    assert USERS[2]["notification_pref"] == pref

@pytest.mark.parametrize("bad", BAD_PREFS, ids=BAD_PREF_IDS)
def test_api_patch_rejects_invalid_value_and_leaves_user_unchanged(client, bad):
    client.patch("/api/users/2/notifications", json={"notification_pref": "sms"})
    before = client.get("/api/users/2").get_json()
    response = client.patch("/api/users/2/notifications", json={"notification_pref": bad})
    assert response.status_code == 422
    assert response.get_json() == {"error": PREF_ERROR}
    assert client.get("/api/users/2").get_json() == before

@pytest.mark.parametrize(
    "body",
    [{}, {"name": "Bob"}, {"pref": "email"}, {"Notification_pref": "email"}],
    ids=["empty", "other-field", "wrong-key", "wrong-case-key"],
)
def test_api_patch_missing_key_returns_422(client, body):
    before = client.get("/api/users/2").get_json()
    response = client.patch("/api/users/2/notifications", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": REQUIRED_ERROR}
    assert client.get("/api/users/2").get_json() == before

@pytest.mark.parametrize(
    "body",
    [["email"], "email", 5, True],
    ids=["list", "string", "number", "bool"],
)
def test_api_patch_non_object_body_returns_422(client, body):
    response = client.patch("/api/users/2/notifications", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": BODY_ERROR}

def test_api_patch_json_null_body_returns_422(client):
    response = client.patch(
        "/api/users/2/notifications",
        data="null",
        content_type="application/json",
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": BODY_ERROR}

def test_api_patch_without_body_returns_422(client):
    response = client.patch("/api/users/2/notifications")
    assert response.status_code == 422
    assert response.get_json() == {"error": BODY_ERROR}

def test_api_patch_malformed_json_returns_422(client):
    response = client.patch(
        "/api/users/2/notifications",
        data="{not valid json",
        content_type="application/json",
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": BODY_ERROR}

def test_api_patch_unknown_user_returns_404(client):
    response = client.patch("/api/users/999/notifications", json={"notification_pref": "email"})
    assert response.status_code == 404
    assert response.get_json() == {"error": USER_NOT_FOUND}
    assert 999 not in USERS

@pytest.mark.parametrize("bad", BAD_PREFS, ids=BAD_PREF_IDS)
def test_api_patch_unknown_user_is_404_before_value_validation(client, bad):
    response = client.patch("/api/users/999/notifications", json={"notification_pref": bad})
    assert response.status_code == 404
    assert response.get_json() == {"error": USER_NOT_FOUND}

def test_api_patch_checks_body_before_looking_up_user(client):
    missing_key = client.patch("/api/users/999/notifications", json={})
    assert missing_key.status_code == 422
    assert missing_key.get_json() == {"error": REQUIRED_ERROR}
    non_object = client.patch("/api/users/999/notifications", json=[1])
    assert non_object.status_code == 422
    assert non_object.get_json() == {"error": BODY_ERROR}
    no_body = client.patch("/api/users/999/notifications")
    assert no_body.status_code == 422
    assert no_body.get_json() == {"error": BODY_ERROR}


# --- API: user responses include notification_pref -------------------------

def test_api_list_users_includes_notification_pref(client):
    create_user("Carol", "carol@example.com")
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.get_json() == [
        ALICE,
        BOB,
        {"id": 3, "name": "Carol", "email": "carol@example.com", "notification_pref": "none"},
    ]

def test_api_list_users_reflects_updates(client):
    client.patch("/api/users/1/notifications", json={"notification_pref": "email"})
    client.patch("/api/users/2/notifications", json={"notification_pref": "sms"})
    users = client.get("/api/users").get_json()
    assert [user["notification_pref"] for user in users] == ["email", "sms"]

def test_api_get_user_includes_notification_pref(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.get_json() == ALICE
    client.patch("/api/users/1/notifications", json={"notification_pref": "email"})
    assert client.get("/api/users/1").get_json() == {**ALICE, "notification_pref": "email"}


# --- Regression: existing user behavior is unchanged -----------------------

def test_regression_get_user_returns_record():
    assert get_user(1) == ALICE
    assert get_user(1) is USERS[1]

def test_regression_get_user_unknown_id_raises_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        get_user(999)
    assert exc_info.value.status_code == 404
    assert str(exc_info.value) == USER_NOT_FOUND

def test_regression_api_get_user_unknown_id_returns_404(client):
    response = client.get("/api/users/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": USER_NOT_FOUND}

@pytest.mark.parametrize(
    "name, email, message",
    [
        ("", "carol@example.com", "Invalid name: cannot be empty"),
        ("   ", "carol@example.com", "Invalid name: cannot be empty"),
        ("Carol", "", "Invalid email: must be a valid email address"),
        ("Carol", "carol.example.com", "Invalid email: must be a valid email address"),
    ],
    ids=["empty-name", "blank-name", "empty-email", "email-without-at"],
)
def test_regression_create_user_rejects_invalid_input(name, email, message):
    before = copy.deepcopy(USERS)
    with pytest.raises(ValidationError) as exc_info:
        create_user(name, email)
    assert exc_info.value.status_code == 422
    assert str(exc_info.value) == message
    assert USERS == before

def test_regression_create_user_checks_name_before_email():
    with pytest.raises(ValidationError) as exc_info:
        create_user("", "bad")
    assert str(exc_info.value) == "Invalid name: cannot be empty"

def test_regression_create_user_assigns_sequential_ids():
    assert create_user("Carol", "carol@example.com")["id"] == 3
    assert create_user("Dan", "dan@example.com")["id"] == 4


# --- Route registration ----------------------------------------------------

EXPECTED_USER_ROUTES = [
    ("/api/users", {"GET"}, "api.list_users_route"),
    ("/api/users/<int:user_id>", {"GET"}, "api.get_user_route"),
    ("/api/users/<int:user_id>/notifications", {"GET"}, "api.get_notification_pref_route"),
    ("/api/users/<int:user_id>/notifications", {"PATCH"}, "api.update_notification_pref_route"),
]

def _registered_routes():
    return {
        (rule.rule, frozenset(rule.methods - {"HEAD", "OPTIONS"})): rule.endpoint
        for rule in flask_app.url_map.iter_rules()
    }

@pytest.mark.parametrize(
    "path, methods, endpoint",
    EXPECTED_USER_ROUTES,
    ids=[f"{'/'.join(sorted(m))} {p}" for p, m, _ in EXPECTED_USER_ROUTES],
)
def test_user_route_registration(path, methods, endpoint):
    routes = _registered_routes()
    assert routes.get((path, frozenset(methods))) == endpoint
    assert flask_app.view_functions[endpoint].__name__ == endpoint.split(".")[1]

def test_user_routes_are_exactly_the_expected_set():
    user_routes = {
        key: endpoint
        for key, endpoint in _registered_routes().items()
        if key[0].startswith("/api/users")
    }
    assert user_routes == {
        (path, frozenset(methods)): endpoint
        for path, methods, endpoint in EXPECTED_USER_ROUTES
    }
