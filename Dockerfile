FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY .dockerignore ./
COPY app ./app
COPY db ./db
COPY docs ./docs
COPY openapi ./openapi
COPY scripts ./scripts
COPY tests ./tests
COPY .env.example ./
COPY Makefile ./

RUN pip install --no-cache-dir -e '.[dev]'

CMD ["sh", "-c", "python scripts/wait_for_db.py && python scripts/migrate.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
