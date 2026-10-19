from flask import Blueprint, jsonify, request

from services.tasks import (
    add_tag,
    create_task,
    get_overdue_tasks,
    get_task,
    list_tasks,
    remove_tag,
)
from services.users import get_user
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
    return jsonify(create_task(data["title"], data["user_id"], data.get("due_date"))), 201

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    tag = request.args.get("tag")
    return jsonify(list_tasks(tag))

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
