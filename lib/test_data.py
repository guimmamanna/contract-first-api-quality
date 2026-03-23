"""
Test data factories for deterministic, readable test fixtures.
"""

import uuid
from datetime import datetime
from typing import Any


def employee_payload(**overrides: Any) -> dict[str, Any]:
    """Return a valid employee creation payload, with optional overrides."""
    base = {
        "first_name": "Test",
        "last_name": "Employee",
        "email": f"test.employee.{uuid.uuid4().hex[:8]}@company.com",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "salary": 100000.0,
    }
    base.update(overrides)
    return base


def employee_response(**overrides: Any) -> dict[str, Any]:
    """Return a realistic employee response dict for mocking."""
    now = datetime.utcnow().isoformat()
    base = {
        "id": str(uuid.uuid4()),
        "first_name": "Test",
        "last_name": "Employee",
        "email": "test.employee@company.com",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "salary": 100000.0,
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    return base


def employee_list_response(count: int = 3, **overrides: Any) -> dict[str, Any]:
    """Return a realistic list-employees response."""
    employees = [employee_response() for _ in range(count)]
    base = {
        "employees": employees,
        "total": count,
        "page": 1,
        "per_page": 20,
    }
    base.update(overrides)
    return base
