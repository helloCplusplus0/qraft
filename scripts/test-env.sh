#!/usr/bin/env bash
set -euo pipefail
pytest --cov=qraft --cov-report=term-missing --cov-fail-under=80