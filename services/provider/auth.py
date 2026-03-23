"""
Authentication utilities for the provider service.
Uses API key header authentication for service-to-service communication.
"""

import os
import secrets
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In production this would be stored securely; here we allow env override.
_VALID_API_KEYS: set[str] = {
    os.environ.get("PROVIDER_API_KEY", "contract-testing-key-2024"),
}


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """Dependency that validates the X-API-Key header."""
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    if api_key not in _VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key


def create_api_key_header(api_key: Optional[str] = None) -> dict[str, str]:
    """Build the header dict for authenticated requests."""
    key = api_key or os.environ.get("PROVIDER_API_KEY", "contract-testing-key-2024")
    return {"X-API-Key": key}
