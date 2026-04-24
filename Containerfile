FROM python:3.11.15-alpine3.23

ARG SERVICE_NAME

WORKDIR /app

ENV UV_PYTHON_DOWNLOADS=0
ENV UV_NO_DEV=1
ENV UV_LINK_MODE=copy

RUN --mount=from=ghcr.io/astral-sh/uv:0.11.7,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --package ${SERVICE_NAME}

COPY ${SERVICE_NAME}/app /app

WORKDIR /

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

CMD ["uvicorn", "app.main:app", "--host", "", "--port", "80"]
