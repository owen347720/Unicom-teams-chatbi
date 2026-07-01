#!/bin/bash
# backend/entrypoint.sh

set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h postgres -p 5432 -U text2sql; do
  sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
