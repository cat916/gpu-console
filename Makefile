BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
DNS_PORT ?= 1053
DNS_ZONE ?= gpu.internal
BACKEND = cd backend && uv run
FRONTEND = cd frontend && yarn
DNS = cd dns && cargo

.PHONY: install dev backend frontend dns test lint format check api clean

install:
	cd backend && uv sync
	cd frontend && yarn install --frozen-lockfile
	$(DNS) fetch

dev:
	$(MAKE) backend & \
	$(MAKE) dns & \
	$(MAKE) frontend & \
	wait

backend:
	$(BACKEND) uvicorn app.main:create_app --factory --reload --port $(BACKEND_PORT)

dns:
	cd dns && DNS_PORT=$(DNS_PORT) DNS_ZONE=$(DNS_ZONE) DNS_RECORDS_URL=http://127.0.0.1:$(BACKEND_PORT)/api/dns/records cargo run --quiet

frontend:
	cd frontend && API_PROXY_TARGET=http://127.0.0.1:$(BACKEND_PORT) yarn dev --port $(FRONTEND_PORT)

test:
	$(BACKEND) pytest
	$(FRONTEND) typecheck
	$(FRONTEND) test
	$(DNS) test --quiet

lint:
	$(BACKEND) ruff format --check .
	$(BACKEND) ruff check .
	$(FRONTEND) lint
	$(DNS) fmt --check
	$(DNS) clippy --quiet --all-targets

format:
	$(BACKEND) ruff format .
	$(BACKEND) ruff check --fix .
	$(DNS) fmt

check: lint test
	$(FRONTEND) build

api:
	cd backend && PYTHONPATH=. uv run python scripts/export_openapi.py
	$(FRONTEND) api:types

clean:
	rm -rf frontend/dist
	$(DNS) clean
	find backend -name __pycache__ -prune -exec rm -rf {} +
