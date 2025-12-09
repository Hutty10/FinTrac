#!/usr/bin/env sh
set -e
# Entry point script for Docker containers

exec uv run fastapi run --host 0.0.0.0 --port 8000