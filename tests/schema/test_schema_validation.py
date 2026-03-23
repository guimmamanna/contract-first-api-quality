"""
Schema Validation Tests
───────────────────────
Verify that every provider endpoint returns responses conforming to
the agreed-upon JSON schemas.  These tests complement contract tests
by catching structural drift introduced by provider-side refactors.

Run:
    pytest tests/schema/test_schema_validation.py -v
"""

import pytest
from fastapi.testclient import TestClient

from services.provider.app import app, store
from lib.schema_validator import (
    EMPLOYEE_SCHEMA,
    EMPLOYEE_LIST_SCHEMA,
    ERROR_SCHEMA,
    HEALTH_SCHEMA,
    assert_valid_schema,
)
from lib.test_data import employee_payload

API_KEY_HEADER = {"X-API-Key": "contract-testing-key-2024"}


@pytest.fixture(autouse=True)
def reset():
    store.reset()
    yield


@pytest.fixture
def api():
    return TestClient(app)


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealthSchema:
    def test_health_matches_schema(self, api):
        resp = api.get("/health")
        assert resp.status_code == 200
        assert_valid_schema(resp.json(), HEALTH_SCHEMA)


# ── Employee List ────────────────────────────────────────────────────────────

class TestEmployeeListSchema:
    def test_list_employees_matches_schema(self, api):
        resp = api.get("/api/v1/employees", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        assert_valid_schema(resp.json(), EMPLOYEE_LIST_SCHEMA)

    def test_empty_department_filter_matches_schema(self, api):
        resp = api.get(
            "/api/v1/employees",
            params={"department": "Nonexistent"},
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert_valid_schema(data, EMPLOYEE_LIST_SCHEMA)
        assert data["employees"] == []


# ── Single Employee ──────────────────────────────────────────────────────────

class TestEmployeeSchema:
    def test_get_employee_matches_schema(self, api):
        # Create an employee to get a valid ID
        create_resp = api.post(
            "/api/v1/employees",
            json=employee_payload(),
            headers=API_KEY_HEADER,
        )
        emp_id = create_resp.json()["id"]

        resp = api.get(f"/api/v1/employees/{emp_id}", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        assert_valid_schema(resp.json(), EMPLOYEE_SCHEMA)

    def test_create_employee_matches_schema(self, api):
        resp = api.post(
            "/api/v1/employees",
            json=employee_payload(),
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 201
        assert_valid_schema(resp.json(), EMPLOYEE_SCHEMA)

    def test_update_employee_matches_schema(self, api):
        create_resp = api.post(
            "/api/v1/employees",
            json=employee_payload(),
            headers=API_KEY_HEADER,
        )
        emp_id = create_resp.json()["id"]

        resp = api.put(
            f"/api/v1/employees/{emp_id}",
            json={"salary": 150000.0},
            headers=API_KEY_HEADER,
        )
        assert resp.status_code == 200
        assert_valid_schema(resp.json(), EMPLOYEE_SCHEMA)


# ── Error Responses ──────────────────────────────────────────────────────────

class TestErrorSchema:
    def test_not_found_matches_error_schema(self, api):
        resp = api.get("/api/v1/employees/nonexistent-id", headers=API_KEY_HEADER)
        assert resp.status_code == 404
        assert_valid_schema(resp.json(), ERROR_SCHEMA)

    def test_conflict_matches_error_schema(self, api):
        payload = employee_payload(email="duplicate@company.com")
        api.post("/api/v1/employees", json=payload, headers=API_KEY_HEADER)
        resp = api.post("/api/v1/employees", json=payload, headers=API_KEY_HEADER)
        assert resp.status_code == 409
        assert_valid_schema(resp.json(), ERROR_SCHEMA)
