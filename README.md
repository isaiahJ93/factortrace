# FactorTrace

**Multi-Regime Regulatory Compliance Engine for Tier 1 & 2 Suppliers**

FactorTrace is a production-ready SaaS platform that automates regulatory compliance reporting across multiple sustainability frameworks. Suppliers plug in once and receive audit-grade outputs for CSRD/ESRS, CBAM, EUDR, ISSB, and future regimes.

---

## Key Features

- **4 Regulatory Regimes**: CSRD/ESRS (Scope 3), CBAM (Carbon Border), EUDR (Deforestation), ISSB (Climate Disclosures)
- **100+ API Endpoints**: Full REST API with OpenAPI documentation
- **9,704 Emission Factors**: EXIOBASE 2020, DEFRA 2024, EPA 2024, CBAM defaults
- **Multi-Tenant Architecture**: Secure tenant isolation with JWT authentication
- **5 Export Formats**: XHTML, PDF, CSV, JSON, iXBRL
- **206 Tests Passing**: Comprehensive test coverage including security tests

---

## Platform Stats

| Metric | Value |
|--------|-------|
| Models | 30+ |
| API Endpoints | 100+ |
| Tests | 206 |
| Emission Factors | 9,704 |
| Regimes | 4 |
| Export Formats | 5 |

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/factortrace.git
cd factortrace

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Local Development

```bash
cd backend

# Install dependencies
poetry install

# Set up database
export DATABASE_URL="sqlite:///./factortrace.db"
poetry run alembic upgrade head

# Seed emission factors
poetry run python scripts/seed_master_factors.py

# Start server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest -v
```

---

## Architecture

```
factortrace/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # FastAPI routes
│   │   ├── models/              # SQLAlchemy ORM
│   │   ├── schemas/             # Pydantic v2 schemas
│   │   └── services/            # Business logic
│   ├── docs/
│   │   ├── api/                 # API contracts
│   │   └── regimes/             # Regime specifications
│   ├── data/                    # Emission factor datasets
│   └── tests/                   # Test suite
├── frontend/                    # Next.js UI (in development)
└── docker-compose.yml
```

### Regime Modules

| Regime | Endpoints | Description |
|--------|-----------|-------------|
| CSRD | `/api/v1/emissions/` | EU Corporate Sustainability Reporting (ESRS E1) |
| CBAM | `/api/v1/cbam/` | Carbon Border Adjustment Mechanism |
| EUDR | `/api/v1/eudr/` | EU Deforestation Regulation |
| ISSB | `/api/v1/issb/` | IFRS Climate-Related Disclosures |

---

## API Overview

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### CBAM Products
```bash
curl http://localhost:8000/api/v1/cbam/products
```

### EUDR Commodities
```bash
curl http://localhost:8000/api/v1/eudr/commodities
```

### Emission Factors
```bash
curl "http://localhost:8000/api/v1/emission-factors?dataset=DEFRA_2024&limit=10"
```

Full API documentation available at `/docs` (Swagger UI) or `/redoc`.

---

## Emission Factor Datasets

| Dataset | Factors | Coverage |
|---------|---------|----------|
| EXIOBASE 2020 | 8,361 | Spend-based Scope 3 (multi-region) |
| DEFRA 2024 | 1,262 | UK GHG conversion factors |
| EPA 2024 | 58 | US stationary combustion |
| CBAM Default | 23 | EU carbon border factors |

---

## Documentation

- **[CLAUDE.md](backend/CLAUDE.md)** - Project architecture and AI agent instructions
- **[CONTRIBUTING.md](backend/CONTRIBUTING.md)** - Contribution guide for humans and AI
- **[DECISIONS.md](backend/DECISIONS.md)** - Architecture decision records
- **[plan.md](backend/plan.md)** - Current development plan

### Regime Specifications
- [CSRD/ESRS](backend/docs/regimes/csrd.md)
- [CBAM](backend/docs/regimes/cbam.md)
- [EUDR](backend/docs/regimes/eudr.md)
- [ISSB](backend/docs/regimes/issb.md)

---

## Deployment

### Docker

```bash
# Build image
docker build -t factortrace/api:latest -f backend/Dockerfile .

# Run with environment
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET=your-secret \
  factortrace/api:latest
```

### CI/CD

GitHub Actions workflows included:
- **CI**: Lint, test, build, security scan
- **Deploy**: GHCR push, staging/production deployment

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic v2
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis
- **Reports**: WeasyPrint (PDF), Jinja2 (XHTML/iXBRL)
- **Frontend**: Next.js 14, React, TypeScript (in development)

---

## License

Proprietary - All rights reserved.

---

## Contact

For enterprise licensing and support inquiries, contact the development team.
