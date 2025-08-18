PYTHON ?= python
PIP ?= pip
# Detect current Python major.minor version for constraints selection
PYVER := $(shell $(PYTHON) -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
CONSTRAINTS_DIR := requirements/constraints

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup dev environment
	$(PYTHON) -m pip install --upgrade pip
	CF=$(CONSTRAINTS_DIR)/$(PYVER).txt; if [ ! -f "$$CF" ]; then echo "[warn] constraints for $(PYVER) not found, fallback to 3.11"; CF=$(CONSTRAINTS_DIR)/3.11.txt; fi; \
	$(PIP) install -r requirements/requirements-stable.txt -c $$CF

setup-candidate: ## Setup dev environment (candidate channel)
	$(PYTHON) -m pip install --upgrade pip
	CF=$(CONSTRAINTS_DIR)/$(PYVER).txt; if [ ! -f "$$CF" ]; then echo "[warn] constraints for $(PYVER) not found, fallback to 3.11"; CF=$(CONSTRAINTS_DIR)/3.11.txt; fi; \
	$(PIP) install -r requirements/requirements-candidate.txt -c $$CF

lint: ## Run lint checks
	black .
	isort .
	flake8 . --exclude .venv,dist,build,artifacts,__pycache__,.pytest_cache

mypy: ## Run mypy type checks
	mypy qraft

test: ## Run tests with coverage
	pytest --cov=qraft --cov-report=term-missing --cov-fail-under=80

dev: ## Start Docker dev environment
	./scripts/dev-env.sh

clean: ## Clean build artifacts
	rm -rf .pytest_cache .mypy_cache dist build __pycache__

.PHONY: help setup setup-candidate lint mypy test dev clean
