PYTHON ?= python
PIP ?= pip

.DEFAULT_GOAL := help

help: ## Show this help
@grep -E ^[a-zA-Z_-]+:.*?##
