"""
FactorTrace backend root package.

Important:
- Do NOT import app.db or create tables at import time.
- Tools like pytest, alembic, uvicorn etc. may import this package
  just to discover settings. Heavy side-effects here will break them.
"""
# Intentionally empty – keep imports inside scripts / app.startup instead.
