"""
Negative-Path & Authentication Tests
─────────────────────────────────────
Coverage for error paths, boundary conditions, and auth enforcement.
These are the edge-case tests a senior SDET would write to guard against
regressions that contract tests alone don't cover.

Run:
    pytest tests/api/test_negative_and_auth.py -v
"""

import pytest
from fastapi.testclient import TestClient

from services.provider.app import app, store
from lib.test_data import employee_payload

VALID_HEADER = {"X-API-Key": "contract-testing-key-2024"}


@pytest.fixture(autouse=True)
def reset():
    store.reset()
    yield


@pytest.fixture
def api():
    return TestClient(app)


# ── Authentication ───────────────────────────────────────────────────────────

class TestAuthentication:
    """Verify that all protected endpoints enforce API key auth."""

    @pytest.mark.parametrize(
        "method, path",
        [
            ("GET", "/api/v1/employees"),
            ("GET", "/api/v1/employees/some-id"),
            ("POST", "/api/v1/employees"),
            ("PUT", "/api/v1/employees/some-id"),
            ("DELETE", "/api/v1/employees/some-id"),
        ],
    )
    def test_missing_api_key_returns_401(self, api, method, path):
        resp = api.request(method, path)
        assert resp.status_code == 401
        assert "Missing API key" in resp.json()["detail"]

    @pytest.mark.parametrize(
        "method, path",
        [
            ("GET", "/api/v1/employees"),
            ("GET", "/api/v1/employees/some-id"),
            ("POST", "/api/v1/employees"),
            ("PUT", "/api/v1/employees/some-id"),
            ("DELETE", "/api/v1/employees/some-id"),
        ],
    )
    def test_invalid_api_key_returns_403(self, api, method, path):
        resp = api.request(method, path, headers={"X-API-Key": "bad-key"})
        assert resp.status_code == 403
        assert "Invalid API key" in resp.json()["detail"]

    def test_health_endpoint_does_not_require_auth(self, api):
        resp = api.get("/health")
        assert resp.status_code == 200


# ── Input Validation / Negative Cases ────────────────────────────────────────

class TestInputValidation:
    """Boundary and malformed-input scenarios."""

    def test_create_employee_missing_required_fields(self, api):
        resp = api.post("/api/v1/employees", json={}, headers=VALID_HEADER)
        assert resp.status_code == 422  # Pydantic validation error

    def test_create_employee_invalid_email(self, api):
        payload = employee_payload(email="not-an-email")
        resp = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp.status_code == 422

    def test_create_employee_negative_salary(self, api):
        payload = employee_payload(salary=-50000)
        resp = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp.status_code == 422

    def test_create_employee_zero_salary(self, api):
        payload = employee_payload(salary=0)
        resp = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp.status_code == 422

    def test_create_employee_empty_first_name(self, api):
        payload = employee_payload(first_name="")
        resp = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp.status_code == 422

    def test_update_nonexistent_employee(self, api):
        resp = api.put(
            "/api/v1/employees/does-not-exist",
            json={"salary": 200000},
            headers=VALID_HEADER,
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_employee(self, api):
        resp = api.delete("/api/v1/employees/does-not-exist", headers=VALID_HEADER)
        assert resp.status_code == 404


# ── Idempotency & Conflict ──────────────────────────────────────────────────

class TestConflictAndIdempotency:
    def test_duplicate_email_returns_409(self, api):
        payload = employee_payload(email="unique@test.com")
        resp1 = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp1.status_code == 201

        resp2 = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        assert resp2.status_code == 409

    def test_delete_is_idempotent_on_second_call(self, api):
        payload = employee_payload()
        create_resp = api.post("/api/v1/employees", json=payload, headers=VALID_HEADER)
        emp_id = create_resp.json()["id"]

        resp1 = api.delete(f"/api/v1/employees/{emp_id}", headers=VALID_HEADER)
        assert resp1.status_code == 204

        resp2 = api.delete(f"/api/v1/employees/{emp_id}", headers=VALID_HEADER)
        assert resp2.status_code == 404


# ── Pagination Edge Cases ────────────────────────────────────────────────────

class TestPagination:
    def test_page_beyond_total_returns_empty_list(self, api):
        resp = api.get(
            "/api/v1/employees",
            params={"page": 999, "per_page": 10},
            headers=VALID_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()["employees"] == []

    def test_per_page_one_returns_single_item(self, api):
        resp = api.get(
            "/api/v1/employees",
            params={"page": 1, "per_page": 1},
            headers=VALID_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["employees"]) == 1
        assert data["total"] >= 1
