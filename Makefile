.PHONY: help install install-dev lint format typecheck test test-cov clean run-gui

PYTHON := python3
UV := uv
VENV := .venv
VENV_BIN := $(VENV)/bin

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies with uv
	$(UV) pip install -r requirements-uv.txt

install-dev:  ## Install all dependencies including dev
	$(UV) pip install -r requirements-uv.txt -r requirements-dev.txt
	$(UV) pip install -e .

lint:  ## Run ruff linter
	ruff check app/ tests/

format:  ## Format code with ruff + black
	ruff check --fix app/ tests/
	black app/ tests/

typecheck:  ## Run mypy type checking
	mypy app/

test:  ## Run tests
	pytest tests/ -v --tb=short

test-cov:  ## Run tests with coverage report
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

clean:  ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info

run-gui:  ## Launch Streamlit GUI
	streamlit run app/gui/streamlit_app.py

run-cli:  ## Show CLI help
	python -m app.cli.main --help

atlas-list:  ## List available atlases
	python -m app.cli.main atlas list

setup-macos:  ## Run macOS setup script
	bash scripts/setup_macos.sh

setup-linux:  ## Run Linux setup script
	bash scripts/setup_linux.sh
