FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app/exchange
COPY exchange-service/pyproject.toml exchange-service/README.md exchange-service/rates.py /app/exchange-service/
COPY exchange/pyproject.toml exchange/uv.lock exchange/README.md exchange/main.py ./
ENV UV_PYTHON_DOWNLOADS=never
RUN uv sync --locked --no-dev --no-editable

CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
