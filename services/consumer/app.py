"""
Consumer Service — HR Dashboard Backend

Consumes the Employee Management API (provider) to build
aggregated views for an internal HR dashboard.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from .employee_client import EmployeeAPIClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HR Dashboard Service",
    description="Consumer service that aggregates employee data from the provider",
    version="1.0.0",
)

_client: Optional[EmployeeAPIClient] = None


def get_client() -> EmployeeAPIClient:
    global _client
    if _client is None:
        _client = EmployeeAPIClient()
    return _client


# ── Response Models ──────────────────────────────────────────────────────────

class DepartmentSummary(BaseModel):
    department: str
    headcount: int
    avg_salary: float


class DashboardResponse(BaseModel):
    total_employees: int
    departments: list[DepartmentSummary]


class EmployeeCard(BaseModel):
    id: str
    full_name: str
    email: str
    job_title: str
    department: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "hr-dashboard", "version": "1.0.0"}


@app.get("/dashboard/summary", response_model=DashboardResponse)
async def dashboard_summary():
    """Aggregate employee data into a department-level summary."""
    client = get_client()
    data = client.list_employees(per_page=200)

    dept_map: dict[str, list[dict]] = {}
    for emp in data["employees"]:
        dept_map.setdefault(emp["department"], []).append(emp)

    departments = [
        DepartmentSummary(
            department=dept,
            headcount=len(emps),
            avg_salary=round(sum(e["salary"] for e in emps) / len(emps), 2),
        )
        for dept, emps in sorted(dept_map.items())
    ]
    return DashboardResponse(total_employees=data["total"], departments=departments)


@app.get("/dashboard/employees/{employee_id}", response_model=EmployeeCard)
async def employee_card(employee_id: str):
    """Return a compact employee card view."""
    client = get_client()
    emp = client.get_employee(employee_id)
    return EmployeeCard(
        id=emp["id"],
        full_name=f"{emp['first_name']} {emp['last_name']}",
        email=emp["email"],
        job_title=emp["job_title"],
        department=emp["department"],
    )


@app.post("/dashboard/employees", response_model=EmployeeCard, status_code=201)
async def create_employee_card(
    first_name: str,
    last_name: str,
    email: str,
    job_title: str,
    department: str,
    salary: float,
):
    """Create an employee through the provider and return a card view."""
    client = get_client()
    emp = client.create_employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        job_title=job_title,
        department=department,
        salary=salary,
    )
    return EmployeeCard(
        id=emp["id"],
        full_name=f"{emp['first_name']} {emp['last_name']}",
        email=emp["email"],
        job_title=emp["job_title"],
        department=emp["department"],
    )
