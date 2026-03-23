# API Specification

## Employee Management API (Provider)

Base URL: `http://localhost:8000`

### Authentication

All `/api/v1/*` endpoints require the `X-API-Key` header.

| Header | Value |
|--------|-------|
| `X-API-Key` | `contract-testing-key-2024` (dev/test) |

---

### Endpoints

#### `GET /health`

Health check (no auth required).

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

---

#### `GET /api/v1/employees`

List employees with pagination and optional department filter.

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page |
| `department` | string | — | Filter by department |

**Response** `200 OK`
```json
{
  "employees": [
    {
      "id": "uuid",
      "first_name": "Alice",
      "last_name": "Johnson",
      "email": "alice.johnson@company.com",
      "job_title": "Senior Software Engineer",
      "department": "Engineering",
      "salary": 135000.0,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

---

#### `GET /api/v1/employees/{employee_id}`

Get a single employee by ID.

**Response** `200 OK` — Employee object (see above)

**Response** `404 Not Found`
```json
{
  "detail": "Employee {employee_id} not found"
}
```

---

#### `POST /api/v1/employees`

Create a new employee.

**Request Body**
```json
{
  "first_name": "string (1-100 chars, required)",
  "last_name": "string (1-100 chars, required)",
  "email": "valid email (required)",
  "job_title": "string (1-200 chars, required)",
  "department": "string (1-100 chars, required)",
  "salary": "number > 0 (required)"
}
```

**Response** `201 Created` — Employee object with generated `id`, `created_at`, `updated_at`

**Response** `409 Conflict` — Email already exists
```json
{
  "detail": "Employee with email {email} already exists"
}
```

**Response** `422 Unprocessable Entity` — Validation error

---

#### `PUT /api/v1/employees/{employee_id}`

Update an existing employee (partial updates supported).

**Request Body** (all fields optional)
```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "valid email",
  "job_title": "string",
  "department": "string",
  "salary": "number > 0"
}
```

**Response** `200 OK` — Updated employee object

**Response** `404 Not Found` — Employee does not exist

---

#### `DELETE /api/v1/employees/{employee_id}`

Delete an employee.

**Response** `204 No Content` — Successfully deleted

**Response** `404 Not Found` — Employee does not exist

---

## HR Dashboard API (Consumer)

Base URL: `http://localhost:8001`

### Endpoints

#### `GET /health`

```json
{
  "status": "healthy",
  "service": "hr-dashboard",
  "version": "1.0.0"
}
```

#### `GET /dashboard/summary`

Aggregated department-level summary.

```json
{
  "total_employees": 3,
  "departments": [
    {
      "department": "Engineering",
      "headcount": 1,
      "avg_salary": 135000.0
    }
  ]
}
```

#### `GET /dashboard/employees/{employee_id}`

Compact employee card.

```json
{
  "id": "uuid",
  "full_name": "Alice Johnson",
  "email": "alice.johnson@company.com",
  "job_title": "Senior Software Engineer",
  "department": "Engineering"
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 401 | Missing API key |
| 403 | Invalid API key |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 422 | Validation error |
