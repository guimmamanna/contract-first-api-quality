"""
Typed HTTP client for the Employee Management API (provider).

This is the integration boundary that consumer contract tests verify.
Every method maps to a single provider endpoint and returns raw dicts
so consuming code is decoupled from transport details.
"""

import logging
import os
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10  # seconds


class EmployeeAPIError(Exception):
    """Raised when the provider returns a non-success status."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class EmployeeAPIClient:
    """Reusable HTTP client for the Employee Management provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        self.base_url = (base_url or os.environ.get("PROVIDER_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.api_key = api_key or os.environ.get("PROVIDER_API_KEY", "contract-testing-key-2024")
        self.timeout = timeout
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        return session

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        logger.info(
            "%s %s → %d (%.0fms)",
            response.request.method,
            response.request.url,
            response.status_code,
            response.elapsed.total_seconds() * 1000,
        )
        if response.status_code >= 400:
            detail = response.json().get("detail", response.text) if response.content else response.reason
            raise EmployeeAPIError(response.status_code, detail)
        if response.status_code == 204:
            return {}
        return response.json()

    # ── CRUD Operations ──────────────────────────────────────────────────────

    def list_employees(
        self,
        page: int = 1,
        per_page: int = 20,
        department: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if department:
            params["department"] = department
        resp = self.session.get(self._url("/api/v1/employees"), params=params, timeout=self.timeout)
        return self._handle_response(resp)

    def get_employee(self, employee_id: str) -> dict[str, Any]:
        resp = self.session.get(self._url(f"/api/v1/employees/{employee_id}"), timeout=self.timeout)
        return self._handle_response(resp)

    def create_employee(
        self,
        first_name: str,
        last_name: str,
        email: str,
        job_title: str,
        department: str,
        salary: float,
    ) -> dict[str, Any]:
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "job_title": job_title,
            "department": department,
            "salary": salary,
        }
        resp = self.session.post(self._url("/api/v1/employees"), json=payload, timeout=self.timeout)
        return self._handle_response(resp)

    def update_employee(self, employee_id: str, **fields) -> dict[str, Any]:
        resp = self.session.put(
            self._url(f"/api/v1/employees/{employee_id}"),
            json=fields,
            timeout=self.timeout,
        )
        return self._handle_response(resp)

    def delete_employee(self, employee_id: str) -> dict[str, Any]:
        resp = self.session.delete(self._url(f"/api/v1/employees/{employee_id}"), timeout=self.timeout)
        return self._handle_response(resp)

    def health(self) -> dict[str, Any]:
        resp = self.session.get(self._url("/health"), timeout=self.timeout)
        return self._handle_response(resp)
