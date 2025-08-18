#!/usr/bin/env bash
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Please install Docker and Docker Compose." >&2
  exit 1
fi
# Build and start dev container
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d --build qraft-dev
  docker-compose exec qraft-dev bash
else
  docker compose up -d --build qraft-dev
  docker compose exec qraft-dev bash
fi