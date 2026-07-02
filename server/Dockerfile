FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencies layer (cached) ──
FROM base AS deps

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# ── App layer ──
FROM deps AS app

COPY . .

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
