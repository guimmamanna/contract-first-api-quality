"""
Generic HTTP client wrapper with logging, retries, and response introspection.

Used across test suites and services to avoid duplicating HTTP boilerplate.
"""

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIResponse:
    """Thin wrapper around requests.Response for convenient assertions."""

    def __init__(self, response: requests.Response, elapsed_ms: float):
        self._response = response
        self.status_code = response.status_code
        self.elapsed_ms = elapsed_ms
        self.headers = dict(response.headers)

    def json(self) -> Any:
        return self._response.json()

    @property
    def text(self) -> str:
        return self._response.text

    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def assert_status(self, expected: int) -> "APIResponse":
        assert self.status_code == expected, (
            f"Expected {expected}, got {self.status_code}: {self.text}"
        )
        return self

    def assert_json_key(self, key: str) -> "APIResponse":
        data = self.json()
        assert key in data, f"Key '{key}' not found in response: {list(data.keys())}"
        return self

    def __repr__(self) -> str:
        return f"<APIResponse status={self.status_code} elapsed={self.elapsed_ms:.0f}ms>"


class BaseAPIClient:
    """
    Configurable HTTP client with retries, default headers, and request logging.
    Extend or instantiate directly for any service.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        retry = Retry(total=max_retries, backoff_factor=0.3, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        if headers:
            self.session.headers.update(headers)

    def request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        **kwargs,
    ) -> APIResponse:
        url = f"{self.base_url}{path}"
        start = time.perf_counter()
        resp = self.session.request(
            method,
            url,
            params=params,
            json=json,
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        api_resp = APIResponse(resp, elapsed_ms)
        logger.info("%s %s → %s", method.upper(), url, api_resp)
        return api_resp

    def get(self, path: str, **kwargs) -> APIResponse:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> APIResponse:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> APIResponse:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> APIResponse:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> APIResponse:
        return self.request("DELETE", path, **kwargs)
