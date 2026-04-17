# ============================================================
# Production Dockerfile — Fire Detection
# Python 3.13 | Multi-stage: < 1GB, non-root, production-ready
# ============================================================

# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.13-slim AS runtime

# Non-root user for security
RUN groupadd -r agent && useradd -r -g agent -d /app agent

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/agent/.local

# Copy application code
COPY app/ ./app/
COPY utils/ ./utils/
COPY --chown=agent:agent . .

# Set permissions
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Environment variables
ENV PATH=/home/agent/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Health check - Fire detection API
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
