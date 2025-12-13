#!/usr/bin/env sh
set -e
# Entry point script for Docker containers

uv run alembic upgrade head

exec uv run fastapi run --host 0.0.0.0 --port 8000