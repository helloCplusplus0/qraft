#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
PYVER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
CF=requirements/constraints/${PYVER}.txt
if [ ! -f "$CF" ]; then
  echo "[warn] constraints for ${PYVER} not found, fallback to 3.11"
  CF=requirements/constraints/3.11.txt
fi
pip install -r requirements/requirements-stable.txt -c "$CF"