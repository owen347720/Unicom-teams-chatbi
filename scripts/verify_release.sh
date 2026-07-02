#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.release.yml}"
ENV_FILE="${ENV_FILE:-.env}"

command -v docker >/dev/null 2>&1 || {
  echo "docker is required" >&2
  exit 1
}

docker compose version >/dev/null

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config >/dev/null

echo "Release configuration looks valid."
echo "After startup, check:"
echo "- Frontend: http://localhost:${FRONTEND_PORT:-3000}/health"
echo "- Backend:  http://localhost:${BACKEND_PORT:-8000}/health"
echo "- Vanna:    http://localhost:${VANNA_PORT:-8001}/health"
