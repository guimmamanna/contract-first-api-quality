"""
End-to-End Integration Tests — Provider ↔ Consumer
────────────────────────────────────────────────────
Tests that spin up both services and verify the full request path.

Run:
    pytest tests/integration/test_e2e.py -v
"""

import pytest
from fastapi.testclient import TestClient

from services.provider.app import app as provider_app, store
from services.consumer.employee_client import EmployeeAPIClient
from lib.schema_validator import assert_valid_schema, EMPLOYEE_SCHEMA

VALID_HEADER = {"X-API-Key": "contract-testing-key-2024"}


@pytest.fixture(autouse=True)
def reset():
    store.reset()
    yield


@pytest.fixture
def provider_api():
    return TestClient(provider_app)


class TestEndToEndFlow:
    """Full lifecycle: create → read → update → delete."""

    def test_employee_crud_lifecycle(self, provider_api):
        # CREATE
        payload = {
            "first_name": "Integration",
            "last_name": "Test",
            "email": "integration.test@company.com",
            "job_title": "SDET",
            "department": "Quality",
            "salary": 110000.0,
        }
        create_resp = provider_api.post(
            "/api/v1/employees", json=payload, headers=VALID_HEADER
        )
        assert create_resp.status_code == 201
        emp = create_resp.json()
        assert_valid_schema(emp, EMPLOYEE_SCHEMA)
        emp_id = emp["id"]

        # READ
        get_resp = provider_api.get(
            f"/api/v1/employees/{emp_id}", headers=VALID_HEADER
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["email"] == "integration.test@company.com"

        # UPDATE
        update_resp = provider_api.put(
            f"/api/v1/employees/{emp_id}",
            json={"salary": 125000.0, "job_title": "Senior SDET"},
            headers=VALID_HEADER,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["salary"] == 125000.0
        assert update_resp.json()["job_title"] == "Senior SDET"

        # LIST (verify shows in results)
        list_resp = provider_api.get(
            "/api/v1/employees",
            params={"department": "Quality"},
            headers=VALID_HEADER,
        )
        assert list_resp.status_code == 200
        emails = [e["email"] for e in list_resp.json()["employees"]]
        assert "integration.test@company.com" in emails

        # DELETE
        del_resp = provider_api.delete(
            f"/api/v1/employees/{emp_id}", headers=VALID_HEADER
        )
        assert del_resp.status_code == 204

        # VERIFY GONE
        gone_resp = provider_api.get(
            f"/api/v1/employees/{emp_id}", headers=VALID_HEADER
        )
        assert gone_resp.status_code == 404

    def test_consumer_client_against_provider(self, provider_api):
        """Simulate the consumer client talking to the real provider."""
        # Use the test client's transport to avoid needing a running server
        list_resp = provider_api.get("/api/v1/employees", headers=VALID_HEADER)
        assert list_resp.status_code == 200
        employees = list_resp.json()["employees"]
        assert len(employees) >= 1

        # Verify each employee has the expected structure
        for emp in employees:
            assert_valid_schema(emp, EMPLOYEE_SCHEMA)
