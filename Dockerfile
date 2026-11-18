FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app/Exchange
COPY services/Exchange-service/pyproject.toml services/Exchange-service/README.md services/Exchange-service/rates.py /app/Exchange-service/
COPY services/Exchange/pyproject.toml services/Exchange/uv.lock services/Exchange/README.md services/Exchange/main.py ./
ENV UV_PYTHON_DOWNLOADS=never
RUN uv sync --locked --no-dev --no-editable

CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
