# contract-first-api-quality

A senior SDET-grade platform for **API quality assurance** and **consumer-driven contract testing**, demonstrating how contract-first workflows reduce integration defects and accelerate release confidence.

---

## Architecture

```
┌────────────────────┐          contract          ┌───────────────────────┐
│  HR Dashboard      │  ──────────────────────▶   │  Employee Management  │
│  (Consumer)        │     Pact JSON file         │  (Provider)           │
│  FastAPI :8001     │  ◀──────────────────────   │  FastAPI :8000        │
└────────────────────┘        verification        └───────────────────────┘
         │                                                   │
         └────────── both tested independently ──────────────┘
```

| Service | Role | Port | Description |
|---------|------|------|-------------|
| **Provider** — Employee Management API | Data owner | 8000 | CRUD for employees with auth, validation, logging |
| **Consumer** — HR Dashboard | Data consumer | 8001 | Aggregates employee data into dashboard views |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Services | Python 3.12 · FastAPI · Pydantic v2 |
| Contract Testing | Pact (Python) — consumer-driven contracts |
| Schema Validation | jsonschema · Pydantic model validation |
| HTTP Client | requests with retry + logging wrapper |
| Test Framework | pytest with markers, fixtures, parametrize |
| Containerization | Docker · Docker Compose |
| CI/CD | GitHub Actions (multi-job pipeline) |
| External Target | OrangeHRM demo instance |

---

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/<your-org>/contract-first-api-quality.git
cd contract-first-api-quality

# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Start provider
uvicorn services.provider.app:app --port 8000 --reload

# Start consumer (separate terminal)
PROVIDER_BASE_URL=http://localhost:8000 uvicorn services.consumer.app:app --port 8001 --reload
```

### Docker Compose

```bash
docker compose up --build
# Provider → http://localhost:8000
# Consumer → http://localhost:8001

# Run test suite in container
docker compose run test-runner
```

---

## Test Suites

### 1. Schema Validation Tests

```bash
pytest tests/schema/ -v
```

Validates every provider endpoint response against JSON Schema definitions. Catches structural drift before it reaches consumers.

### 2. API Negative & Auth Tests

```bash
pytest tests/api/ -v
```

Covers:
- Missing/invalid API key → 401/403
- Malformed payloads → 422
- Nonexistent resources → 404
- Duplicate email conflicts → 409
- Pagination edge cases

### 3. Consumer Contract Tests (Pact)

```bash
pytest tests/contract/test_consumer_contract.py -v
```

Generates a Pact contract (`pacts/*.json`) from the consumer's perspective. Each test defines an expected interaction that the provider must satisfy.

### 4. Provider Verification

```bash
pytest tests/contract/test_provider_verification.py -v
```

Starts the real provider and replays every Pact interaction against it. Verifies the provider still honours the consumer's contract.

### 5. End-to-End Integration

```bash
pytest tests/integration/test_e2e.py -v
```

Full CRUD lifecycle test against the real provider, validating schema on every response.

### 6. OrangeHRM Integration

```bash
pytest tests/integration/test_orangehrm.py -v --run-integration
```

Tests against the live [OrangeHRM demo](https://opensource-demo.orangehrmlive.com/web/index.php/auth/login) — login reachability, auth flows, response timing.

---

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/contract-testing.yml`) runs on every push/PR:

```
lint → api-tests ─────────────────────┐
    → consumer-contracts              │
         → provider-verification      ▼
              → integration-tests
    → docker-build (parallel)
```

| Job | Purpose |
|-----|---------|
| **Lint & Type Check** | ruff + mypy static analysis |
| **Schema & API Tests** | JSON Schema validation + negative/auth tests |
| **Consumer Contracts** | Generate Pact files, upload as artifacts |
| **Provider Verification** | Download Pact artifacts, verify against real provider |
| **Integration Tests** | E2E lifecycle + OrangeHRM smoke tests |
| **Docker Build** | Build images, compose up, smoke test endpoints |

A nightly cron workflow re-verifies contracts and external integrations.

---

## Project Structure

```
contract-first-api-quality/
├── services/
│   ├── provider/           # Employee Management API
│   │   ├── app.py          # FastAPI application
│   │   ├── auth.py         # API key authentication
│   │   ├── database.py     # In-memory data store
│   │   ├── middleware.py   # Request/response logging
│   │   └── provider_states.py  # Pact state handler
│   └── consumer/           # HR Dashboard Service
│       ├── app.py          # FastAPI application
│       └── employee_client.py  # HTTP client for provider
├── lib/
│   ├── api_client.py       # Reusable HTTP client wrapper
│   ├── schema_validator.py # JSON Schema definitions + helpers
│   └── test_data.py        # Test data factories
├── tests/
│   ├── contract/           # Pact consumer & provider tests
│   ├── schema/             # Schema validation tests
│   ├── api/                # Negative cases & auth tests
│   └── integration/        # E2E and OrangeHRM tests
├── pacts/                  # Generated Pact JSON contracts
├── docs/                   # Architecture & strategy docs
├── .github/workflows/      # CI pipelines
├── docker-compose.yml
├── Dockerfile.provider
├── Dockerfile.consumer
├── requirements.txt
└── requirements-dev.txt
```

---

## Documentation

| Document | Content |
|----------|---------|
| [Contract Testing Strategy](docs/CONTRACT_TESTING_STRATEGY.md) | How contract testing reduces integration defects |
| [API Specification](docs/API_SPECIFICATION.md) | Full endpoint reference |
| [Test Architecture](docs/TEST_ARCHITECTURE.md) | Test pyramid, categories, trade-offs |

---

## License

MIT
