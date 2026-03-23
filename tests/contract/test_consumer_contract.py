"""
Pact Consumer Contract Tests
─────────────────────────────
These tests define the contract from the **consumer's** perspective.

Each test sets up an expected interaction (request → response) on a Pact
mock server, then exercises the consumer's EmployeeAPIClient against that
mock.  The resulting Pact file (JSON) is written to ``./pacts/`` and can be
published to a Pact Broker or verified directly by the provider.

Run:
    pytest tests/contract/test_consumer_contract.py -v
"""

import os
import atexit
import pytest
from pact import Consumer, Provider

from services.consumer.employee_client import EmployeeAPIClient, EmployeeAPIError

# ── Pact Setup ───────────────────────────────────────────────────────────────

PACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "pacts")
PACT_MOCK_HOST = "localhost"
PACT_MOCK_PORT = 1234

pact = Consumer("HRDashboardConsumer").has_pact_with(
    Provider("EmployeeManagementProvider"),
    host_name=PACT_MOCK_HOST,
    port=PACT_MOCK_PORT,
    pact_dir=PACT_DIR,
    log_dir=os.path.join(PACT_DIR, "logs"),
)

pact.start_service()
atexit.register(pact.stop_service)


@pytest.fixture
def client() -> EmployeeAPIClient:
    return EmployeeAPIClient(
        base_url=f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}",
        api_key="contract-testing-key-2024",
    )


# ── Expected response fragments ─────────────────────────────────────────────

EMPLOYEE_BODY = {
    "id": "e1b2c3d4-0000-0000-0000-000000000001",
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice.johnson@company.com",
    "job_title": "Senior Software Engineer",
    "department": "Engineering",
    "salary": 135000.0,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00",
}

EMPLOYEE_LIST_BODY = {
    "employees": [EMPLOYEE_BODY],
    "total": 1,
    "page": 1,
    "per_page": 20,
}


# ── Contract Tests ───────────────────────────────────────────────────────────

class TestListEmployees:
    def test_returns_employee_list(self, client: EmployeeAPIClient):
        (
            pact.given("employees exist")
            .upon_receiving("a request to list employees")
            .with_request("GET", "/api/v1/employees", query={"page": "1", "per_page": "20"})
            .will_respond_with(200, body=EMPLOYEE_LIST_BODY)
        )

        with pact:
            result = client.list_employees(page=1, per_page=20)

        assert result["total"] == 1
        assert len(result["employees"]) == 1
        assert result["employees"][0]["first_name"] == "Alice"

    def test_filter_by_department(self, client: EmployeeAPIClient):
        (
            pact.given("employees exist in Engineering")
            .upon_receiving("a request to list employees filtered by department")
            .with_request(
                "GET",
                "/api/v1/employees",
                query={"page": "1", "per_page": "20", "department": "Engineering"},
            )
            .will_respond_with(200, body=EMPLOYEE_LIST_BODY)
        )

        with pact:
            result = client.list_employees(department="Engineering")

        assert result["employees"][0]["department"] == "Engineering"


class TestGetEmployee:
    def test_returns_single_employee(self, client: EmployeeAPIClient):
        employee_id = "e1b2c3d4-0000-0000-0000-000000000001"
        (
            pact.given("employee e1b2c3d4-0000-0000-0000-000000000001 exists")
            .upon_receiving("a request to get an employee by id")
            .with_request("GET", f"/api/v1/employees/{employee_id}")
            .will_respond_with(200, body=EMPLOYEE_BODY)
        )

        with pact:
            result = client.get_employee(employee_id)

        assert result["id"] == employee_id
        assert result["email"] == "alice.johnson@company.com"

    def test_employee_not_found(self, client: EmployeeAPIClient):
        (
            pact.given("no employee with id not-found-id exists")
            .upon_receiving("a request for a non-existent employee")
            .with_request("GET", "/api/v1/employees/not-found-id")
            .will_respond_with(404, body={"detail": "Employee not-found-id not found"})
        )

        with pact:
            with pytest.raises(EmployeeAPIError) as exc_info:
                client.get_employee("not-found-id")
            assert exc_info.value.status_code == 404


class TestCreateEmployee:
    def test_creates_employee_successfully(self, client: EmployeeAPIClient):
        create_body = {
            "first_name": "Dave",
            "last_name": "Brown",
            "email": "dave.brown@company.com",
            "job_title": "DevOps Engineer",
            "department": "Infrastructure",
            "salary": 120000.0,
        }
        expected_response = {
            **create_body,
            "id": "new-employee-id-001",
            "created_at": "2024-03-01T09:00:00",
            "updated_at": "2024-03-01T09:00:00",
        }

        (
            pact.given("no employee with email dave.brown@company.com exists")
            .upon_receiving("a request to create an employee")
            .with_request("POST", "/api/v1/employees", body=create_body)
            .will_respond_with(201, body=expected_response)
        )

        with pact:
            result = client.create_employee(**create_body)

        assert result["first_name"] == "Dave"
        assert result["id"] == "new-employee-id-001"

    def test_duplicate_email_conflict(self, client: EmployeeAPIClient):
        create_body = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@company.com",
            "job_title": "Engineer",
            "department": "Engineering",
            "salary": 100000.0,
        }
        (
            pact.given("employee with email alice.johnson@company.com already exists")
            .upon_receiving("a request to create a duplicate employee")
            .with_request("POST", "/api/v1/employees", body=create_body)
            .will_respond_with(
                409,
                body={"detail": "Employee with email alice.johnson@company.com already exists"},
            )
        )

        with pact:
            with pytest.raises(EmployeeAPIError) as exc_info:
                client.create_employee(**create_body)
            assert exc_info.value.status_code == 409


class TestUpdateEmployee:
    def test_updates_employee_salary(self, client: EmployeeAPIClient):
        employee_id = "e1b2c3d4-0000-0000-0000-000000000001"
        updated = {**EMPLOYEE_BODY, "salary": 145000.0, "updated_at": "2024-06-01T12:00:00"}

        (
            pact.given("employee e1b2c3d4-0000-0000-0000-000000000001 exists")
            .upon_receiving("a request to update an employee salary")
            .with_request(
                "PUT",
                f"/api/v1/employees/{employee_id}",
                body={"salary": 145000.0},
            )
            .will_respond_with(200, body=updated)
        )

        with pact:
            result = client.update_employee(employee_id, salary=145000.0)

        assert result["salary"] == 145000.0


class TestDeleteEmployee:
    def test_deletes_employee(self, client: EmployeeAPIClient):
        employee_id = "e1b2c3d4-0000-0000-0000-000000000001"

        (
            pact.given("employee e1b2c3d4-0000-0000-0000-000000000001 exists")
            .upon_receiving("a request to delete an employee")
            .with_request("DELETE", f"/api/v1/employees/{employee_id}")
            .will_respond_with(204)
        )

        with pact:
            result = client.delete_employee(employee_id)

        assert result == {}
