"""
In-memory employee data store for the provider service.
Suitable for testing and demonstration; swap for a real DB in production.
"""

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional


class EmployeeStore:
    def __init__(self):
        self._data: dict[str, dict] = {}
        self._seed()

    def _seed(self):
        seed_employees = [
            {
                "first_name": "Alice",
                "last_name": "Johnson",
                "email": "alice.johnson@company.com",
                "job_title": "Senior Software Engineer",
                "department": "Engineering",
                "salary": 135000.0,
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob.smith@company.com",
                "job_title": "QA Lead",
                "department": "Quality",
                "salary": 115000.0,
            },
            {
                "first_name": "Carol",
                "last_name": "Williams",
                "email": "carol.williams@company.com",
                "job_title": "Product Manager",
                "department": "Product",
                "salary": 125000.0,
            },
        ]
        for emp in seed_employees:
            self.create(emp)

    def create(self, data: dict) -> dict:
        employee_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": employee_id,
            **data,
            "created_at": now,
            "updated_at": now,
        }
        self._data[employee_id] = record
        return deepcopy(record)

    def get(self, employee_id: str) -> Optional[dict]:
        record = self._data.get(employee_id)
        return deepcopy(record) if record else None

    def find_by_email(self, email: str) -> Optional[dict]:
        for record in self._data.values():
            if record["email"] == email:
                return deepcopy(record)
        return None

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        department: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        records = list(self._data.values())
        if department:
            records = [r for r in records if r["department"] == department]
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        return [deepcopy(r) for r in records[start:end]], total

    def update(self, employee_id: str, data: dict) -> Optional[dict]:
        if employee_id not in self._data:
            return None
        record = self._data[employee_id]
        record.update(data)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return deepcopy(record)

    def delete(self, employee_id: str) -> bool:
        return self._data.pop(employee_id, None) is not None

    def reset(self):
        self._data.clear()
        self._seed()
