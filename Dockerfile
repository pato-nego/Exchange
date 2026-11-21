FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

WORKDIR /app/exchange
COPY pyproject.toml uv.lock README.md ./
ENV UV_PYTHON_DOWNLOADS=never
RUN uv sync --locked --no-dev
COPY main.py rates.py ./

CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
