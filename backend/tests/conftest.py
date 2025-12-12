# tests/conftest.py
"""
Pytest fixtures for FactorTrace multi-tenant testing.

Provides:
- Test database with fresh schema per test
- Multi-tenant fixtures (tenant_a, tenant_b)
- Authenticated test clients for different tenants
- Helper functions for cross-tenant isolation testing
"""

import pytest
from typing import Generator, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# App imports
from app.main import app
from app.core.database import Base, get_db as get_db_core
from app.db.session import get_db as get_db_session
from app.core.auth import create_access_token
from app.models.tenant import Tenant
from app.models.user import User
from app.models.emission import Emission, EmissionScope
from app.models.voucher import Voucher
from app.models.payment import Payment
from app.models.evidence_document import EvidenceDocument
from app.models.data_quality import DataQualityScore


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a fresh test database engine for each test function."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_app(db_session: Session) -> FastAPI:
    """
    Create a test app with database dependency override.

    Note: We override both get_db functions since different modules
    import from different locations.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override both db dependencies
    app.dependency_overrides[get_db_core] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> TestClient:
    """Create a test client without authentication."""
    return TestClient(test_app)


# =============================================================================
# MULTI-TENANT FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def tenant_a(db_session: Session) -> Tenant:
    """Create Tenant A for testing."""
    tenant = Tenant(
        id=f"tenant-a-{uuid4()}",
        name="Test Company Alpha",
        slug="alpha",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture(scope="function")
def tenant_b(db_session: Session) -> Tenant:
    """Create Tenant B for testing."""
    tenant = Tenant(
        id=f"tenant-b-{uuid4()}",
        name="Test Company Beta",
        slug="beta",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture(scope="function")
def user_a(db_session: Session, tenant_a: Tenant) -> User:
    """Create a user belonging to Tenant A."""
    user = User(
        # id is auto-generated as Integer
        tenant_id=tenant_a.id,
        email="alice@alpha.example.com",
        hashed_password="fakehash123",
        is_active=True,
        is_super_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_b(db_session: Session, tenant_b: Tenant) -> User:
    """Create a user belonging to Tenant B."""
    user = User(
        # id is auto-generated as Integer
        tenant_id=tenant_b.id,
        email="bob@beta.example.com",
        hashed_password="fakehash456",
        is_active=True,
        is_super_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def super_admin(db_session: Session, tenant_a: Tenant) -> User:
    """Create a super-admin user (cross-tenant access)."""
    user = User(
        # id is auto-generated as Integer
        tenant_id=tenant_a.id,  # Super-admin still belongs to a tenant
        email="admin@factortrace.example.com",
        hashed_password="fakehash789",
        is_active=True,
        is_super_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# =============================================================================
# AUTHENTICATION FIXTURES
# =============================================================================

def get_auth_headers(user: User) -> Dict[str, str]:
    """Generate authentication headers for a user."""
    token = create_access_token(
        user_id=str(user.id),  # Convert integer to string for JWT
        email=user.email,
        tenant_id=user.tenant_id,
        is_super_admin=user.is_super_admin,
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_a(user_a: User) -> Dict[str, str]:
    """Authentication headers for Tenant A user."""
    return get_auth_headers(user_a)


@pytest.fixture(scope="function")
def auth_headers_b(user_b: User) -> Dict[str, str]:
    """Authentication headers for Tenant B user."""
    return get_auth_headers(user_b)


@pytest.fixture(scope="function")
def auth_headers_admin(super_admin: User) -> Dict[str, str]:
    """Authentication headers for super-admin."""
    return get_auth_headers(super_admin)


@pytest.fixture(scope="function")
def client_a(test_app: FastAPI, auth_headers_a: Dict[str, str]) -> TestClient:
    """Test client authenticated as Tenant A user."""
    client = TestClient(test_app)
    client.headers.update(auth_headers_a)
    return client


@pytest.fixture(scope="function")
def client_b(test_app: FastAPI, auth_headers_b: Dict[str, str]) -> TestClient:
    """Test client authenticated as Tenant B user."""
    client = TestClient(test_app)
    client.headers.update(auth_headers_b)
    return client


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def emission_a(db_session: Session, tenant_a: Tenant, user_a: User) -> Emission:
    """Create an emission record for Tenant A."""
    emission = Emission(
        # id is auto-generated
        tenant_id=tenant_a.id,
        user_id=user_a.id,
        scope=EmissionScope.SCOPE_2,
        category="electricity",
        activity_data=10000.0,
        unit="kWh",
        emission_factor=0.35,
        emission_factor_source="DEFRA_2024",
        amount=3.5,  # tCO2e
        country_code="GB",
    )
    db_session.add(emission)
    db_session.commit()
    db_session.refresh(emission)
    return emission


@pytest.fixture(scope="function")
def emission_b(db_session: Session, tenant_b: Tenant, user_b: User) -> Emission:
    """Create an emission record for Tenant B."""
    emission = Emission(
        # id is auto-generated
        tenant_id=tenant_b.id,
        user_id=user_b.id,
        scope=EmissionScope.SCOPE_1,
        category="stationary_combustion",
        activity_data=5000.0,
        unit="m3",
        emission_factor=2.0,
        emission_factor_source="EPA_2024",
        amount=10.0,  # tCO2e
        country_code="US",
    )
    db_session.add(emission)
    db_session.commit()
    db_session.refresh(emission)
    return emission


@pytest.fixture(scope="function")
def voucher_a(db_session: Session, tenant_a: Tenant) -> Voucher:
    """Create a voucher for Tenant A."""
    voucher = Voucher(
        # id is auto-generated as Integer
        tenant_id=tenant_a.id,
        code="ALPHA-1234-5678-9012",
        valid_until=datetime.utcnow() + timedelta(days=90),
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture(scope="function")
def voucher_b(db_session: Session, tenant_b: Tenant) -> Voucher:
    """Create a voucher for Tenant B."""
    voucher = Voucher(
        # id is auto-generated as Integer
        tenant_id=tenant_b.id,
        code="BETA-0000-1111-2222",
        valid_until=datetime.utcnow() + timedelta(days=90),
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture(scope="function")
def payment_a(db_session: Session, tenant_a: Tenant) -> Payment:
    """Create a payment for Tenant A."""
    from app.models.payment import PaymentStatus
    payment = Payment(
        # id is auto-generated as Integer
        tenant_id=tenant_a.id,
        stripe_session_id="cs_test_alpha_123",
        amount=95000,  # €950.00 in cents
        currency="EUR",
        status=PaymentStatus.COMPLETED,
        customer_email="alice@alpha.example.com",
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture(scope="function")
def payment_b(db_session: Session, tenant_b: Tenant) -> Payment:
    """Create a payment for Tenant B."""
    from app.models.payment import PaymentStatus
    payment = Payment(
        # id is auto-generated as Integer
        tenant_id=tenant_b.id,
        stripe_session_id="cs_test_beta_456",
        amount=500000,  # €5000.00 in cents
        currency="EUR",
        status=PaymentStatus.COMPLETED,
        customer_email="bob@beta.example.com",
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_emission_for_tenant(
    db_session: Session,
    tenant: Tenant,
    scope: EmissionScope = EmissionScope.SCOPE_2,
    category: str = "electricity",
    amount: float = 1.0,
) -> Emission:
    """Helper to create emissions for any tenant."""
    emission = Emission(
        tenant_id=tenant.id,
        scope=scope,
        category=category,
        activity_type="Test Activity",
        activity_data=1000.0,
        unit="kWh",
        emission_factor=0.35,
        emission_factor_source="Test",
        amount=amount,
        country_code="GB",
    )
    db_session.add(emission)
    db_session.commit()
    db_session.refresh(emission)
    return emission


def assert_tenant_isolation(
    response_data: list,
    expected_tenant_id: str,
    entity_name: str = "record",
):
    """
    Assert that all records in response belong to expected tenant.

    Usage:
        response = client_a.get("/api/v1/emissions/")
        assert_tenant_isolation(response.json(), tenant_a.id, "emission")
    """
    for record in response_data:
        tenant_id = record.get("tenant_id")
        if tenant_id is not None:
            assert tenant_id == expected_tenant_id, (
                f"Cross-tenant data leak: {entity_name} with tenant_id={tenant_id} "
                f"returned to user with tenant_id={expected_tenant_id}"
            )
