from flask import Blueprint, jsonify, request

from services.tasks import (
    add_tag,
    create_task,
    get_overdue_tasks,
    get_task,
    list_tasks,
    remove_tag,
    update_task,
)
from services.users import (
    get_notification_pref,
    get_user,
    list_users,
    update_notification_pref,
)
from utils.errors import AppError, ValidationError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/overdue", methods=["GET"])
def get_overdue_tasks_route():
    return jsonify(get_overdue_tasks())

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    return jsonify(create_task(data["title"], data["user_id"], data.get("due_date"), data.get("priority", 3))), 201

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    tag = request.args.get("tag")
    priority = request.args.get("priority")
    if priority is not None:
        try:
            priority = int(priority)
        except ValueError:
            raise ValidationError("priority", "must be an integer")
    return jsonify(list_tasks(tag, priority))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    """Update a task's priority.

    The body must be a JSON object with a "priority" key; otherwise this
    returns 422 ("Invalid body: must be a JSON object" or "Invalid priority:
    is required"). These checks run before the task is looked up. Any value
    under "priority", including null, is passed to update_task(), which
    validates it.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    if "priority" not in data:
        raise ValidationError("priority", "is required")
    return jsonify(update_task(task_id, data["priority"]))

@api.route("/tasks/<int:task_id>/tags", methods=["POST"])
def add_tag_route(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    tags, created = add_tag(task_id, data.get("tag"))
    return jsonify({"task_id": task_id, "tags": tags}), 201 if created else 200

@api.route("/tasks/<int:task_id>/tags/<tag>", methods=["DELETE"])
def remove_tag_route(task_id, tag):
    remove_tag(task_id, tag)
    return "", 204

@api.route("/users", methods=["GET"])
def list_users_route():
    return jsonify(list_users())

@api.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_notification_pref_route(user_id):
    return jsonify({"user_id": user_id, "notification_pref": get_notification_pref(user_id)})

@api.route("/users/<int:user_id>/notifications", methods=["PATCH"])
def update_notification_pref_route(user_id):
    """Update a user's notification preference.

    The body must be a JSON object with a "notification_pref" key; otherwise
    this returns 422 ("Invalid body: must be a JSON object" or "Invalid
    notification_pref: is required"). These checks run before the user is
    looked up. The value is passed to update_notification_pref(), which
    validates it.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    if "notification_pref" not in data:
        raise ValidationError("notification_pref", "is required")
    user = update_notification_pref(user_id, data["notification_pref"])
    return jsonify({"user_id": user_id, "notification_pref": user["notification_pref"]})
