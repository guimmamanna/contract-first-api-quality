# Test Architecture

## Test Pyramid

This project follows the **Test Pyramid** strategy, with contract tests providing the best cost-to-confidence ratio for service integration:

```
           ╱ ╲
          ╱ E2E╲           Few — business-critical flows
         ╱───────╲
        ╱Integration╲      Service-to-service validation
       ╱─────────────╲
      ╱  Contract Tests ╲  ★ Core focus — interface agreements
     ╱───────────────────╲
    ╱  Schema Validation   ╲  Structural conformance
   ╱─────────────────────────╲
  ╱     API / Negative Tests   ╲  Edge cases, auth, error paths
 ╱─────────────────────────────────╲
╱         Unit Tests (implicit)      ╲  Built into Pydantic models
```

---

## Test Categories

### 1. Contract Tests (`tests/contract/`)

**Purpose:** Verify the consumer-provider interface agreement.

| File | Scope | Runs Against |
|------|-------|-------------|
| `test_consumer_contract.py` | Consumer expectations | Pact mock server |
| `test_provider_verification.py` | Provider conformance | Real provider instance |

**Key characteristics:**
- Fast (mock-based on consumer side)
- No shared environment needed
- Catches schema drift, missing endpoints, behaviour changes
- Produces Pact JSON artifacts for CI pipeline

### 2. Schema Validation Tests (`tests/schema/`)

**Purpose:** Ensure every response structurally matches the agreed schema.

Uses `jsonschema` with shared schema definitions from `lib/schema_validator.py`. Tests run against the provider's `TestClient` (no HTTP, pure ASGI).

### 3. API / Negative / Auth Tests (`tests/api/`)

**Purpose:** Cover error paths the happy-path contracts don't exercise.

| Category | Examples |
|----------|----------|
| Auth enforcement | Missing key → 401, bad key → 403 |
| Input validation | Empty fields → 422, negative salary → 422 |
| Not found | Non-existent ID → 404 |
| Conflicts | Duplicate email → 409 |
| Pagination | Page beyond total, per_page=1 |

### 4. Integration Tests (`tests/integration/`)

**Purpose:** Validate full request paths and external service behaviour.

| File | Target |
|------|--------|
| `test_e2e.py` | Full CRUD lifecycle against provider |
| `test_orangehrm.py` | Live tests against OrangeHRM demo |

### 5. OrangeHRM Tests

Gated behind `--run-integration` flag. Tests:
- Login page accessibility
- Unauthenticated API rejection
- Response timing thresholds
- Invalid credential handling

---

## Fixtures & Utilities

| Module | Purpose |
|--------|---------|
| `lib/api_client.py` | `BaseAPIClient` with retries, logging, `APIResponse` wrapper |
| `lib/schema_validator.py` | Shared JSON Schema definitions + `assert_valid_schema()` |
| `lib/test_data.py` | Factories: `employee_payload()`, `employee_response()` |
| `conftest.py` | `--run-integration` flag, logging setup |

---

## Test Execution Matrix

| Suite | Command | Speed | External Deps |
|-------|---------|-------|---------------|
| Schema | `pytest tests/schema/` | ⚡ <1s | None |
| Negative/Auth | `pytest tests/api/` | ⚡ <1s | None |
| Consumer contracts | `pytest tests/contract/test_consumer_contract.py` | ⚡ <2s | None |
| Provider verification | `pytest tests/contract/test_provider_verification.py` | 🔄 ~5s | Provider process |
| E2E | `pytest tests/integration/test_e2e.py` | 🔄 ~2s | None |
| OrangeHRM | `pytest tests/integration/test_orangehrm.py --run-integration` | 🌐 ~10s | Internet |
| **Full suite** | `pytest` | 🔄 ~15s | Provider + Internet |

---

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| In-memory store vs. real DB | Simplifies setup; tests are deterministic |
| Module-level Pact mock | Avoids port conflicts; `atexit` cleanup |
| `TestClient` for schema/API tests | No network overhead; tests run in-process |
| Separate Dockerfiles | Independent scaling; clear build contexts |
| `--run-integration` gate | CI can skip flaky external tests |

---

## Adding New Tests

### New contract interaction

1. Add a test to `test_consumer_contract.py` with a `pact.given()` state.
2. If needed, add state setup logic to `provider_states.py`.
3. Re-run consumer tests to regenerate the Pact file.
4. Run provider verification to confirm the provider satisfies the new interaction.

### New schema check

1. Define the schema in `lib/schema_validator.py`.
2. Write a test in `tests/schema/` using `assert_valid_schema()`.

### New negative case

1. Add a parametrized test to `tests/api/test_negative_and_auth.py`.
