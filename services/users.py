from utils.errors import NotFoundError, ValidationError

USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com", "notification_pref": "none"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com", "notification_pref": "none"},
}

NOTIFICATION_PREFS: tuple[str, ...] = ("email", "sms", "none")

def _validate_notification_pref(pref: str) -> str:
    """Validate a notification preference.

    A valid preference is a string exactly equal to one of NOTIFICATION_PREFS.
    Preferences are rejected, never normalized.

    Args:
        pref: The notification preference to validate.

    Returns:
        The preference, unchanged.

    Raises:
        ValidationError: If pref is not a string or is not one of email, sms, none.
    """
    if not isinstance(pref, str) or pref not in NOTIFICATION_PREFS:
        raise ValidationError("notification_pref", "must be one of email, sms, none")
    return pref

def get_user(user_id: int) -> dict:
    """Retrieve a user by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user record as a dictionary.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    if user_id not in USERS:
        raise NotFoundError("User")
    return USERS[user_id]

def create_user(name: str, email: str) -> dict:
    """Create a new user.

    Args:
        name: The user's display name.
        email: The user's email address.

    Returns:
        The newly created user record.

    Raises:
        ValidationError: If name or email is not a string, or is empty.
    """
    if not isinstance(name, str):
        raise ValidationError("name", "must be a string")
    if not name or not name.strip():
        raise ValidationError("name", "cannot be empty")
    if not isinstance(email, str):
        raise ValidationError("email", "must be a string")
    if not email or "@" not in email:
        raise ValidationError("email", "must be a valid email address")
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {"id": new_id, "name": name, "email": email, "notification_pref": "none"}
    return USERS[new_id]

def list_users() -> list[dict]:
    """Retrieve all users.

    Returns:
        A list of all user records, ordered by user ID. Empty if none exist.
    """
    return [USERS[user_id] for user_id in sorted(USERS)]

def get_notification_pref(user_id: int) -> str:
    """Retrieve a user's notification preference.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user's notification preference: "email", "sms" or "none".

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    return get_user(user_id)["notification_pref"]

def update_notification_pref(user_id: int, pref: str) -> dict:
    """Update a user's notification preference.

    The user is looked up before the preference is validated, so a missing
    user raises NotFoundError even if the preference is also invalid.

    Args:
        user_id: The unique identifier for the user.
        pref: The new notification preference: "email", "sms" or "none".

    Returns:
        The updated user record.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If pref is not one of email, sms, none.
    """
    user = get_user(user_id)
    _validate_notification_pref(pref)
    user["notification_pref"] = pref
    return user
