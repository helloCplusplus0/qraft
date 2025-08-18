PYTHON ?= python
PIP ?= pip

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup dev environment
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements/requirements-stable.txt -c requirements/constraints/3.11.txt

lint: ## Run lint checks
	black .
	isort .
	flake8 . --exclude .venv,dist,build,artifacts,__pycache__,.pytest_cache

mypy: ## Run mypy type checks
	mypy qraft

test: ## Run tests with coverage
	pytest --cov=qraft --cov-report=term-missing

clean: ## Clean build artifacts
	rm -rf .pytest_cache .mypy_cache dist build __pycache__

.PHONY: help setup lint mypy test clean
