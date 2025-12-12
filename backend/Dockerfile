# ==============================================================================
# FactorTrace API - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimal image size and security
# Base: Python 3.11 slim with WeasyPrint dependencies
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ------------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.3

WORKDIR /app

# Copy dependency files first (for layer caching)
# pyproject.toml and poetry.lock are in parent directory (Scope3Tool/)
# When building from backend/, use: docker build -f Dockerfile ..
# When using docker-compose, context is set to parent
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt (without dev dependencies)
# This allows us to use pip in the final stage for a smaller image
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev 2>/dev/null || \
    poetry export -f requirements.txt --output requirements.txt --without-hashes 2>/dev/null || \
    echo "# No poetry.lock found, dependencies will be installed from pyproject.toml" > requirements.txt

# Install dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt

# Install production extras
RUN pip install --no-cache-dir \
    gunicorn==22.0.0 \
    weasyprint==62.3 \
    slowapi==0.1.9 \
    psutil==5.9.8 \
    python-multipart==0.0.9 \
    reportlab==4.2.0 \
    pyjwt==2.8.0 \
    passlib[bcrypt]==1.7.4 \
    python-jose[cryptography]==3.3.0 \
    alembic==1.13.1 \
    psycopg2-binary==2.9.9 \
    sentry-sdk[fastapi]==1.45.0

# ------------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Labels for container metadata
LABEL maintainer="FactorTrace <support@factortrace.com>" \
    org.opencontainers.image.title="FactorTrace API" \
    org.opencontainers.image.description="ESRS E1 Emissions Compliance Platform" \
    org.opencontainers.image.version="1.0.0"

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    # Default configuration
    ENVIRONMENT=production \
    PORT=8000

# Install runtime dependencies
# WeasyPrint requires: libpango, libcairo, libgdk-pixbuf, libffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libglib2.0-0 \
    # PDF rendering fonts
    fonts-liberation \
    fonts-dejavu-core \
    # PostgreSQL client (for pg_isready health checks)
    libpq5 \
    postgresql-client \
    # Curl for health checks
    curl \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd --gid 1000 factortrace && \
    useradd --uid 1000 --gid factortrace --shell /bin/bash --create-home factortrace

# Set working directory
WORKDIR $APP_HOME

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code (from backend/ subdirectory when context is parent)
COPY --chown=factortrace:factortrace backend/ .

# Create necessary directories with correct permissions
RUN mkdir -p uploads logs temp data && \
    chown -R factortrace:factortrace $APP_HOME

# Switch to non-root user
USER factortrace

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - use gunicorn with uvicorn workers for production
CMD ["gunicorn", "app.main:app", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "50", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--capture-output", \
    "--enable-stdio-inheritance"]
