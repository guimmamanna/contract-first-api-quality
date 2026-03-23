# Makefile — contract-first-api-quality
# Common commands for development and CI.

.PHONY: install test test-schema test-api test-contract test-e2e test-integration lint typecheck docker-up docker-down clean

install:
	pip install -r requirements.txt -r requirements-dev.txt

# ── Test Suites ──────────────────────────────────────────────────────────────

test:
	pytest tests/ -v

test-schema:
	pytest tests/schema/ -v

test-api:
	pytest tests/api/ -v

test-contract-consumer:
	pytest tests/contract/test_consumer_contract.py -v

test-contract-provider:
	pytest tests/contract/test_provider_verification.py -v

test-contract: test-contract-consumer test-contract-provider

test-e2e:
	pytest tests/integration/test_e2e.py -v

test-integration:
	pytest tests/integration/test_orangehrm.py -v --run-integration

test-all: test test-integration

# ── Code Quality ─────────────────────────────────────────────────────────────

lint:
	ruff check .

typecheck:
	mypy services/ lib/ --ignore-missing-imports

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

docker-test:
	docker compose run test-runner

# ── Services ─────────────────────────────────────────────────────────────────

run-provider:
	uvicorn services.provider.app:app --port 8000 --reload

run-consumer:
	PROVIDER_BASE_URL=http://localhost:8000 uvicorn services.consumer.app:app --port 8001 --reload

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache reports/ htmlcov/ .coverage
