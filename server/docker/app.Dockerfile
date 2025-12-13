FROM ghcr.io/astral-sh/uv:debian-slim

WORKDIR /app

COPY ../pyproject.toml ../uv.lock /app/

RUN uv sync --locked

COPY .. /app/

EXPOSE 8000

CMD [ "../scripts/docker-entrypoint.sh" ]

