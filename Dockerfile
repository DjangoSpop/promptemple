# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.prod.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.prod.txt

# Production stage
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=promptcraft.settings.production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/logs /app/staticfiles /app/mediafiles \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run migrations and collect static files
RUN python manage.py migrate --noinput || echo "Migration failed, continuing..." \
    && python manage.py collectstatic --noinput

# Expose port (will be overridden by Railway's PORT env var)
EXPOSE 8000

# Health check using the correct health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Start command with proper error handling
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne promptcraft.asgi:application --bind 0.0.0.0 --port ${PORT:-8000}"]
