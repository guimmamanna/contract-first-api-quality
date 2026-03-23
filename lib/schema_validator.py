"""
JSON Schema validation helpers.

Provides reusable schema definitions for API contracts and a validation
function used in both contract and integration tests.
"""

from jsonschema import validate, ValidationError

# ── Shared Schemas ───────────────────────────────────────────────────────────

EMPLOYEE_SCHEMA = {
    "type": "object",
    "required": [
        "id",
        "first_name",
        "last_name",
        "email",
        "job_title",
        "department",
        "salary",
        "created_at",
        "updated_at",
    ],
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "first_name": {"type": "string", "minLength": 1},
        "last_name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "job_title": {"type": "string"},
        "department": {"type": "string"},
        "salary": {"type": "number", "exclusiveMinimum": 0},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
    },
    "additionalProperties": False,
}

EMPLOYEE_LIST_SCHEMA = {
    "type": "object",
    "required": ["employees", "total", "page", "per_page"],
    "properties": {
        "employees": {"type": "array", "items": EMPLOYEE_SCHEMA},
        "total": {"type": "integer", "minimum": 0},
        "page": {"type": "integer", "minimum": 1},
        "per_page": {"type": "integer", "minimum": 1},
    },
    "additionalProperties": False,
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {"type": "string"},
    },
}

HEALTH_SCHEMA = {
    "type": "object",
    "required": ["status", "version", "timestamp"],
    "properties": {
        "status": {"type": "string"},
        "version": {"type": "string"},
        "timestamp": {"type": "string"},
    },
    "additionalProperties": False,
}


def validate_schema(instance: dict, schema: dict) -> list[str]:
    """
    Validate ``instance`` against ``schema``.
    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as exc:
        errors.append(str(exc.message))
    return errors


def assert_valid_schema(instance: dict, schema: dict) -> None:
    """Raise AssertionError if the instance does not match the schema."""
    errors = validate_schema(instance, schema)
    assert not errors, f"Schema validation failed: {errors}"
