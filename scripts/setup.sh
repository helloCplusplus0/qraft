#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
pip install -r requirements/requirements-stable.txt -c requirements/constraints/3.11.txt