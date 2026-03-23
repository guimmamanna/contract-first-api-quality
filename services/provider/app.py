"""
Provider Service — Employee Management API

A FastAPI-based microservice that provides employee management endpoints.
This service acts as the "provider" in our contract testing workflow.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .middleware import RequestResponseLoggingMiddleware
from .auth import verify_api_key, create_api_key_header
from .database import EmployeeStore
from .provider_states import init_provider_states

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Employee Management API",
    description="Provider service for contract-first API quality platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestResponseLoggingMiddleware)

store = EmployeeStore()

# Register Pact provider-state handler (used during contract verification)
app.include_router(init_provider_states(store))


# ── Request / Response Models ────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    job_title: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=100)
    salary: float = Field(..., gt=0)


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    salary: Optional[float] = Field(None, gt=0)


class EmployeeResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    job_title: str
    department: str
    salary: float
    created_at: str
    updated_at: str


class EmployeeListResponse(BaseModel):
    employees: list[EmployeeResponse]
    total: int
    page: int
    per_page: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get(
    "/api/v1/employees",
    response_model=EmployeeListResponse,
    tags=["Employees"],
)
async def list_employees(
    page: int = 1,
    per_page: int = 20,
    department: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
):
    employees, total = store.list(page=page, per_page=per_page, department=department)
    return EmployeeListResponse(
        employees=[_to_response(e) for e in employees],
        total=total,
        page=page,
        per_page=per_page,
    )


@app.get(
    "/api/v1/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
async def get_employee(employee_id: str, api_key: str = Depends(verify_api_key)):
    emp = store.get(employee_id)
    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )
    return _to_response(emp)


@app.post(
    "/api/v1/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Employees"],
)
async def create_employee(body: EmployeeCreate, api_key: str = Depends(verify_api_key)):
    if store.find_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with email {body.email} already exists",
        )
    emp = store.create(body.model_dump())
    return _to_response(emp)


@app.put(
    "/api/v1/employees/{employee_id}",
    response_model=EmployeeResponse,
    tags=["Employees"],
)
async def update_employee(
    employee_id: str,
    body: EmployeeUpdate,
    api_key: str = Depends(verify_api_key),
):
    emp = store.update(employee_id, body.model_dump(exclude_unset=True))
    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )
    return _to_response(emp)


@app.delete(
    "/api/v1/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Employees"],
)
async def delete_employee(employee_id: str, api_key: str = Depends(verify_api_key)):
    deleted = store.delete(employee_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _to_response(emp: dict) -> EmployeeResponse:
    return EmployeeResponse(**emp)
