# ---------------------------- Stage 1: Build dependencies ---------------------------- #
FROM python:3.12-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_SYNC=1

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    libpq-dev \
    curl

# Install uv
RUN curl -LsSf https://astral.sh/uv/0.5.26/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files from backend folder
COPY backend/pyproject.toml backend/uv.lock ./

# Install runtime dependencies
RUN uv sync --frozen --no-dev

# ---------------------------- Stage 2: Final lightweight image ---------------------------- #
FROM python:3.12-alpine AS production

WORKDIR /app

ENV PYTHONPATH=/app

RUN apk add --no-cache \
    libffi \
    openssl \
    libpq \
    curl

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Copy backend source code (relative to build context ./backend)
# COPY . .

COPY backend /app/backend

# COPY uploads /app/uploads

RUN chown -R appuser:appgroup /app

USER appuser

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_SYSTEM_PYTHON=1

EXPOSE 8000

# Run the FastAPI app (main.py is in backend root)
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
