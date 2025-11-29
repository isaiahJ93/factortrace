# /dockerize

You help me generate production-grade deployment artifacts for FactorTrace.

When I run this command:

1. **Assume:**
   - FastAPI backend at `app.main:app`
   - Postgres in production
   - Alembic for migrations

2. **Generate or refine:**
   - A Dockerfile for the backend
   - A docker-compose.yml (or similar) with:
     - Backend service
     - Postgres service
     - Optional migration/init service

3. **Ensure:**
   - Environment variables like `DATABASE_URL`, `ENVIRONMENT`, `CORS_ORIGINS` are used.
   - A simple healthcheck route is configured for orchestrators.
   - Startup includes `alembic upgrade head` in a safe way.

Keep configs as simple and readable as possible, but production-ready.
