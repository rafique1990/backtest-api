.PHONY: help install install-dev build up down stop logs clean-docker test lint format type-check generate clean clean-data dev

help:
	@echo "Available targets:"
	@echo "  install      - Install core dependencies with UV"
	@echo "  install-dev  - Install development dependencies with UV"
	@echo "  build        - Build Docker image (tagged bitacore-backtest:latest)"
	@echo "  up           - Build and start Docker services (runs 'docker compose up --build -d')"
	@echo "  down         - Stop and remove containers and networks for the project"
	@echo "  stop         - Only stop running containers (preserves state)"
	@echo "  logs         - Stream logs from the 'api' service"
	@echo "  clean-docker - Stop, remove containers, networks, volumes, and images for a clean restart ✨"
	@echo "  generate     - Generate sample Parquet data"
	@echo "  test         - Run pytest with coverage"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Format code with ruff"
	@echo "  type-check   - Run mypy type checking"
	@echo "  clean        - Clean pycache, coverage files, and the .venv folder"
	@echo "  clean-data   - Remove generated parquet files from the 'data' directory"
	@echo "  dev          - Run the application locally with uvicorn in watch mode"

install:
	uv sync

install-dev:
	uv sync --extra dev

build:
	docker build -t bitacore-backtest:latest .

up:
	docker compose up --build -d

down:
	docker compose down

stop:
	docker compose stop

clean-docker:
	@echo "Stopping and removing all project-related containers, networks, volumes, and images..."
	docker compose down -v --rmi all

generate:
	uv run python scripts/generate_parquets.py

test:
	uv run pytest -v --cov=app --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy .

clean:
	# Removes cache, coverage files, and the virtual environment
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov .venv
	# Removes __pycache__ directories
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	# Removes .pyc files
	find . -type f -name "*.pyc" -delete

clean-data:
	rm -rf data/*.parquet

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

logs:
	docker compose logs -f api