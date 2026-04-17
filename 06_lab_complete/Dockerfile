# ============================================================
# Production Dockerfile — Fire Detection
# Python 3.13 | Multi-stage: < 500 MB, non-root, production-ready
# ============================================================

# Stage 1: Builder — install all Python dependencies to /install
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build tools only (no libopencv-dev needed; using headless wheel)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install to a clean prefix so we can copy the whole tree to runtime
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime — lean image
FROM python:3.13-slim AS runtime

# Non-root user for security
RUN groupadd -r agent && useradd -r -g agent -d /app -s /sbin/nologin agent

WORKDIR /app

# curl is needed for the HEALTHCHECK command
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder into the system Python path
COPY --from=builder /install /usr/local

# Copy application code (chown so agent can read)
COPY --chown=agent:agent app/ ./app/

# Copy rest of project files (railway.toml, .env.example, etc.)
COPY --chown=agent:agent . .

# Set permissions
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run application — use $PORT so Railway/Render can inject the port
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
