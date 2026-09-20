BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
BACKEND = cd backend && uv run
FRONTEND = cd frontend && npm

.PHONY: install dev backend frontend test lint format check api clean

install:
	cd backend && uv sync
	cd frontend && npm install

dev:
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait

backend:
	$(BACKEND) uvicorn app.main:create_app --factory --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && API_PROXY_TARGET=http://127.0.0.1:$(BACKEND_PORT) npm run dev -- --port $(FRONTEND_PORT)

test:
	$(BACKEND) pytest
	$(FRONTEND) run typecheck

lint:
	$(BACKEND) ruff format --check .
	$(BACKEND) ruff check .
	$(FRONTEND) run lint

format:
	$(BACKEND) ruff format .
	$(BACKEND) ruff check --fix .

check: lint test
	$(FRONTEND) run build

api:
	cd backend && PYTHONPATH=. uv run python scripts/export_openapi.py
	$(FRONTEND) run api:types

clean:
	rm -rf frontend/dist
	find backend -name __pycache__ -prune -exec rm -rf {} +
