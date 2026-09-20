BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
BACKEND = cd backend && uv run
FRONTEND = cd frontend && yarn

.PHONY: install dev backend frontend test lint format check api clean

install:
	cd backend && uv sync
	cd frontend && yarn install --frozen-lockfile

dev:
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait

backend:
	$(BACKEND) uvicorn app.main:create_app --factory --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && API_PROXY_TARGET=http://127.0.0.1:$(BACKEND_PORT) yarn dev --port $(FRONTEND_PORT)

test:
	$(BACKEND) pytest
	$(FRONTEND) typecheck

lint:
	$(BACKEND) ruff format --check .
	$(BACKEND) ruff check .
	$(FRONTEND) lint

format:
	$(BACKEND) ruff format .
	$(BACKEND) ruff check --fix .

check: lint test
	$(FRONTEND) build

api:
	cd backend && PYTHONPATH=. uv run python scripts/export_openapi.py
	$(FRONTEND) api:types

clean:
	rm -rf frontend/dist
	find backend -name __pycache__ -prune -exec rm -rf {} +
