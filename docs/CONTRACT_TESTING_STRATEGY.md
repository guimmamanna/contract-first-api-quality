# Contract Testing Strategy

## Why Contract Testing?

Traditional integration testing requires **all services running simultaneously** in a shared environment. This creates:

- **Environment bottlenecks** — teams wait for a stable integration env.
- **Flaky tests** — network issues, data pollution, timing races.
- **Slow feedback** — defects found late in the pipeline are expensive.
- **Coupling** — test suites break when unrelated services change.

**Contract testing decouples** consumer and provider verification. Each side is tested independently against an agreed-upon contract, eliminating the need for both services to be running at the same time.

---

## How It Works

### Consumer-Driven Contracts (CDC)

```
  Consumer Test Suite                Pact Broker / Artifact Store
  ┌──────────────────┐              ┌──────────────────────────┐
  │ 1. Define expected│   publish   │                          │
  │    interactions   │ ──────────▶ │  Contract (Pact JSON)    │
  │ 2. Test against   │             │                          │
  │    mock provider  │             └──────────┬───────────────┘
  └──────────────────┘                         │  download
                                               ▼
                                  ┌──────────────────────┐
                                  │ Provider Test Suite    │
                                  │ 3. Replay interactions │
                                  │    against real service │
                                  │ 4. Report pass/fail    │
                                  └──────────────────────┘
```

1. **Consumer writes tests** that describe what it *expects* from the provider (method, path, headers, body shape).
2. A **Pact file** (JSON) is generated — this is the contract.
3. The **provider replays** each interaction against its real implementation.
4. If every interaction passes, the contract is **verified** and the services are safe to deploy together.

### Key Principle

> **The consumer defines the contract, the provider verifies it.**

This makes contract drift immediately visible. If the provider changes a field name or removes an endpoint, verification fails *before* deployment.

---

## Where It Fits in the Release Pipeline

```
┌─────────────┐
│  Unit Tests  │  ← Individual functions/classes
├─────────────┤
│  Contract    │  ← Interface agreements between services
│  Tests       │     (this project's core focus)
├─────────────┤
│  Integration │  ← Full service interactions (real HTTP)
│  Tests       │
├─────────────┤
│  E2E Tests   │  ← Business workflow validation
└─────────────┘
```

Contract tests sit **between unit and integration tests** in the test pyramid:

| Level | Speed | Confidence | Environment Needs |
|-------|-------|------------|-------------------|
| Unit | ⚡ Fastest | Low (internal only) | None |
| **Contract** | ⚡ Fast | **High (interface level)** | **None (mock-based)** |
| Integration | 🐢 Slow | High | Partial |
| E2E | 🐌 Slowest | Highest | Full |

### Benefits in CI/CD

| Scenario | Without Contracts | With Contracts |
|----------|-------------------|----------------|
| Provider changes response shape | Discovered in staging/prod | **Blocked in provider's PR** |
| Consumer expects new field | Works locally, breaks in integration | **Visible before merge** |
| Service deployed independently | Requires coordinated releases | **Safe independent deployment** |
| Integration env down | Entire pipeline blocked | **Contract tests still pass** |

---

## Reducing Integration Defects

Contract testing eliminates the most common integration defect categories:

### 1. Schema Drift
**Problem:** Provider renames `firstName` → `first_name` without telling consumers.
**Solution:** Consumer contract specifies `first_name`; provider verification catches the rename.

### 2. Missing Endpoints
**Problem:** Provider deprecates an endpoint the consumer still uses.
**Solution:** Contract verification fails when the endpoint is removed.

### 3. Behavioural Changes
**Problem:** Provider changes 404 response body from `{"error": "..."}` to `{"detail": "..."}`.
**Solution:** Consumer contract specifies expected error shape; verification catches the change.

### 4. Auth Requirement Changes
**Problem:** Provider adds required auth header that consumer doesn't send.
**Solution:** Contract includes auth headers; verification uses real auth middleware.

---

## Contract Testing vs. Other Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **Shared Swagger/OpenAPI** | Single source of truth | Doesn't verify runtime behaviour |
| **Integration tests** | High confidence | Slow, environment-dependent, flaky |
| **Contract tests (Pact)** | Fast, independent, catches drift | Requires adoption by both teams |
| **E2E tests** | Full business flow coverage | Slowest, most brittle |

**Best practice:** Use contract tests as the primary inter-service validation, supplemented by a small number of E2E smoke tests.

---

## Implementation in This Project

| Component | File | Purpose |
|-----------|------|---------|
| Consumer contract tests | `tests/contract/test_consumer_contract.py` | Define expected interactions |
| Provider verification | `tests/contract/test_provider_verification.py` | Verify provider honours contracts |
| Provider state handler | `services/provider/provider_states.py` | Set up data for Pact "given" states |
| Schema validation | `tests/schema/test_schema_validation.py` | Structural conformance checks |
| Pact artifacts | `pacts/` | Generated contract files |
| CI pipeline | `.github/workflows/contract-testing.yml` | Automated publish → verify workflow |

---

## Recommended Reading

- [Pact Documentation](https://docs.pact.io/)
- [Consumer-Driven Contracts (Martin Fowler)](https://martinfowler.com/articles/consumerDrivenContracts.html)
- [Testing Strategies in a Microservice Architecture](https://martinfowler.com/articles/microservice-testing/)
