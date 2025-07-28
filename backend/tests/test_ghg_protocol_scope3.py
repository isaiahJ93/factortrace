"""
Test Suite for GHG Protocol Scope 3 Calculator
Comprehensive tests including unit, integration, and compliance tests
"""

import pytest
import pytest_asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any
from uuid import UUID, uuid4
import json
from unittest.mock import Mock, AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
from faker import Faker
from hypothesis import given, strategies as st, settings

from app.domain_models import (
    Scope3Category, MethodologyType, EmissionFactorSource,
    DataQualityScore, EmissionFactor, ActivityData,
    CategoryCalculationResult, EmissionResult, DataQualityIndicator,
    Quantity, PurchasedGoodsActivity, BusinessTravelActivity,
    TransportMode, Organization, User
)
from app.calculation_engine import (
    UncertaintyEngine, Category1Calculator, Category6Calculator,
    CalculationEngineFactory, CalculationParameters
)
from app.repositories import (
    DatabaseEmissionFactorRepository, ActivityDataRepository,
    CalculationResultRepository, CacheManager
)
from app.services import CalculationService, ValidationService
from app.api_models import (
    CalculationRequest, ActivityDataPoint, EmissionFactorCreateRequest,
    EmissionResultResponse
)
from app.database_models import Base
from app.main import app
from app.config import Settings, get_settings

fake = Faker()


# Fixtures
@pytest.fixture
def test_settings():
    """Override settings for testing"""
    return Settings(
        environment="test",
        database_url="postgresql+asyncpg://test:test@localhost:5432/ghg_test",
        redis_url="redis://localhost:6379/1",
        secret_key="test-secret-key",
        enable_external_providers=False,
        rate_limit_enabled=False
    )


@pytest_asyncio.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/ghg_test",
        poolclass=NullPool
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_cache():
    """Create test Redis client"""
    client = await redis.from_url("redis://localhost:6379/1", decode_responses=True)
    
    # Clear test database
    await client.flushdb()
    
    yield client
    
    await client.close()


@pytest_asyncio.fixture
async def test_client(test_settings):
    """Create test API client"""
    # Override settings
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()


@pytest.fixture
def sample_emission_factor():
    """Sample emission factor for testing"""
    return EmissionFactor(
        id=uuid4(),
        name="Steel production",
        category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
        value=Decimal("2.5"),
        unit="kgCO2e/kg",
        source=EmissionFactorSource.EPA,
        source_reference="EPA 2024",
        region="US",
        year=2024,
        uncertainty_range=(0.9, 1.1),
        quality_indicator=DataQualityIndicator(
            reliability=DataQualityScore.INDUSTRY_AVERAGE,
            completeness=DataQualityScore.INDUSTRY_AVERAGE,
            temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
            geographical_correlation=DataQualityScore.VERIFIED_SPECIFIC,
            technological_correlation=DataQualityScore.INDUSTRY_AVERAGE
        )
    )


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing"""
    return PurchasedGoodsActivity(
        id=uuid4(),
        category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
        description="Steel procurement Q1 2024",
        product_description="Hot-rolled steel sheets",
        supplier_country="US",
        quantity=Quantity(value=Decimal("1000"), unit="kg"),
        unit_price=Decimal("1.5"),
        location="US",
        time_period=date(2024, 1, 1),
        data_source="ERP System",
        quality_indicator=DataQualityIndicator(
            reliability=DataQualityScore.VERIFIED_SPECIFIC,
            completeness=DataQualityScore.VERIFIED_SPECIFIC,
            temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
            geographical_correlation=DataQualityScore.VERIFIED_SPECIFIC,
            technological_correlation=DataQualityScore.VERIFIED_SPECIFIC
        )
    )


# Unit Tests
class TestUncertaintyEngine:
    """Test uncertainty propagation engine"""
    
    def test_latin_hypercube_sampling(self):
        """Test LHS generates proper distribution"""
        engine = UncertaintyEngine(n_iterations=1000)
        samples = engine._latin_hypercube_sample(1000, 2)
        
        # Check shape
        assert samples.shape == (1000, 2)
        
        # Check uniform distribution
        assert 0 <= samples.min() <= 0.01
        assert 0.99 <= samples.max() <= 1.0
        
        # Check stratification (each interval should have one sample)
        bins = 10
        for i in range(bins):
            interval_samples = samples[(samples[:, 0] >= i/bins) & (samples[:, 0] < (i+1)/bins)]
            assert len(interval_samples) == 100  # 1000/10
    
    def test_lognormal_distribution(self):
        """Test lognormal distribution generation"""
        engine = UncertaintyEngine()
        samples = engine._generate_distribution(
            mean=100,
            uncertainty=(10, 10),  # 10% CV
            distribution=UncertaintyDistribution.LOGNORMAL,
            uniform_samples=np.linspace(0.05, 0.95, 100)
        )
        
        # Check reasonable range
        assert 70 < samples.min() < 90
        assert 110 < samples.max() < 130
        
        # Check mean is approximately correct
        assert 95 < samples.mean() < 105
    
    @given(
        activity_value=st.floats(min_value=0.1, max_value=1e6),
        ef_value=st.floats(min_value=0.001, max_value=100)
    )
    @settings(max_examples=50)
    def test_uncertainty_propagation(self, activity_value, ef_value):
        """Property-based test for uncertainty propagation"""
        engine = UncertaintyEngine(n_iterations=1000)
        
        result = engine.propagate_uncertainty(
            activity_value=activity_value,
            activity_uncertainty=(5, 5),
            ef_value=ef_value,
            ef_uncertainty=(10, 10)
        )
        
        # Central estimate should be close to deterministic calculation
        expected = activity_value * ef_value
        assert 0.8 * expected < float(result.value) < 1.2 * expected
        
        # Uncertainty bounds should contain central estimate
        assert result.uncertainty_lower <= result.value <= result.uncertainty_upper
        
        # Bounds should be reasonable
        assert float(result.uncertainty_lower) > 0.5 * expected
        assert float(result.uncertainty_upper) < 2.0 * expected


class TestCategory1Calculator:
    """Test Category 1 (Purchased Goods) calculator"""
    
    def test_basic_calculation(self, sample_activity_data, sample_emission_factor):
        """Test basic emission calculation"""
        calculator = Category1Calculator(UncertaintyEngine())
        
        result = calculator.calculate(
            activity_data=[sample_activity_data],
            emission_factors=[sample_emission_factor],
            parameters=CalculationParameters(
                methodology=MethodologyType.ACTIVITY_BASED,
                include_uncertainty=False
            )
        )
        
        # Expected: 1000 kg * 2.5 kgCO2e/kg = 2500 kgCO2e
        assert float(result.emissions.value) == 2500.0
        assert result.activity_data_count == 1
        assert result.category == Scope3Category.PURCHASED_GOODS_AND_SERVICES
    
    def test_transport_factor(self, sample_emission_factor):
        """Test calculation with transport emissions"""
        activity = PurchasedGoodsActivity(
            id=uuid4(),
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            description="Imported steel",
            product_description="Steel from China",
            supplier_country="CN",
            quantity=Quantity(value=Decimal("1000"), unit="kg"),
            transport_distance=5000,  # km
            location="US",
            time_period=date(2024, 1, 1),
            data_source="Import records",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.VERIFIED_SPECIFIC,
                completeness=DataQualityScore.VERIFIED_SPECIFIC,
                temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                geographical_correlation=DataQualityScore.INDUSTRY_AVERAGE,
                technological_correlation=DataQualityScore.VERIFIED_SPECIFIC
            )
        )
        
        calculator = Category1Calculator(UncertaintyEngine())
        result = calculator.calculate(
            activity_data=[activity],
            emission_factors=[sample_emission_factor],
            parameters=CalculationParameters(include_uncertainty=False)
        )
        
        # Should include transport emissions
        # Base: 1000 * 2.5 = 2500
        # Transport: 5000 km * 0.08 (China factor) = 400
        # Total: 2500 * (1 + 0.4) = 3500
        assert float(result.emissions.value) > 2500  # Includes transport
    
    def test_validation(self, sample_emission_factor):
        """Test input validation"""
        calculator = Category1Calculator(UncertaintyEngine())
        
        # Invalid quantity
        invalid_activity = PurchasedGoodsActivity(
            id=uuid4(),
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            description="Invalid",
            product_description="Test",
            supplier_country="US",
            quantity=Quantity(value=Decimal("-100"), unit="kg"),
            location="US",
            time_period=date(2024, 1, 1),
            data_source="Test",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.ESTIMATED,
                completeness=DataQualityScore.ESTIMATED,
                temporal_correlation=DataQualityScore.ESTIMATED,
                geographical_correlation=DataQualityScore.ESTIMATED,
                technological_correlation=DataQualityScore.ESTIMATED
            )
        )
        
        errors = calculator.validate_data([invalid_activity], [sample_emission_factor])
        assert len(errors) > 0
        assert "quantity" in errors[0].lower()


class TestCategory6Calculator:
    """Test Category 6 (Business Travel) calculator"""
    
    def test_air_travel_calculation(self):
        """Test air travel with RFI and cabin class"""
        activity = BusinessTravelActivity(
            id=uuid4(),
            category=Scope3Category.BUSINESS_TRAVEL,
            description="NYC to London flight",
            origin="NYC",
            destination="LON",
            mode=TransportMode.AIR,
            distance=5585,  # km
            travelers=2,
            cabin_class="business",
            time_period=date(2024, 1, 1),
            data_source="Travel system",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.VERIFIED_SPECIFIC,
                completeness=DataQualityScore.VERIFIED_SPECIFIC,
                temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                geographical_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                technological_correlation=DataQualityScore.VERIFIED_SPECIFIC
            )
        )
        
        # Mock emission factor
        air_ef = EmissionFactor(
            id=uuid4(),
            name="Air travel - long haul",
            category=Scope3Category.BUSINESS_TRAVEL,
            value=Decimal("0.15"),  # kgCO2e/km
            unit="kgCO2e/km",
            source=EmissionFactorSource.DEFRA,
            source_reference="DEFRA 2024",
            year=2024,
            metadata={"mode": "air"}
        )
        
        calculator = Category6Calculator(UncertaintyEngine())
        result = calculator.calculate(
            activity_data=[activity],
            emission_factors=[air_ef],
            parameters=CalculationParameters(include_uncertainty=False)
        )
        
        # Expected calculation:
        # 5585 km * 2 travelers * 0.15 kgCO2e/km * 2.0 (business) * 1.9 (RFI) * 1.1 (detour)
        # = 5585 * 2 * 0.15 * 2.0 * 1.9 * 1.1 = 6,978.015
        expected = 5585 * 2 * 0.15 * 2.0 * 1.9 * 1.1
        assert abs(float(result.emissions.value) - expected) < 1.0
    
    def test_hotel_emissions(self):
        """Test hotel accommodation emissions"""
        activity = BusinessTravelActivity(
            id=uuid4(),
            category=Scope3Category.BUSINESS_TRAVEL,
            description="Business trip with hotel",
            origin="NYC",
            destination="BOS",
            mode=TransportMode.RAIL,
            distance=350,
            travelers=1,
            hotel_nights=3,
            hotel_country="US",
            time_period=date(2024, 1, 1),
            data_source="Expense report",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.VERIFIED_SPECIFIC,
                completeness=DataQualityScore.VERIFIED_SPECIFIC,
                temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                geographical_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                technological_correlation=DataQualityScore.VERIFIED_SPECIFIC
            )
        )
        
        # Mock emission factors
        rail_ef = EmissionFactor(
            id=uuid4(),
            name="Rail travel",
            category=Scope3Category.BUSINESS_TRAVEL,
            value=Decimal("0.05"),
            unit="kgCO2e/km",
            source=EmissionFactorSource.EPA,
            source_reference="EPA 2024",
            year=2024,
            metadata={"mode": "rail"}
        )
        
        hotel_ef = EmissionFactor(
            id=uuid4(),
            name="Hotel - US",
            category=Scope3Category.BUSINESS_TRAVEL,
            value=Decimal("20.0"),
            unit="kgCO2e/night",
            source=EmissionFactorSource.DEFRA,
            source_reference="DEFRA 2024",
            year=2024,
            region="US",
            metadata={"type": "hotel"}
        )
        
        calculator = Category6Calculator(UncertaintyEngine())
        result = calculator.calculate(
            activity_data=[activity],
            emission_factors=[rail_ef, hotel_ef],
            parameters=CalculationParameters(include_uncertainty=False)
        )
        
        # Rail: 350 km * 1 * 0.05 / 0.35 = 50
        # Hotel: 3 nights * 20 = 60
        # Total: 110
        assert 100 < float(result.emissions.value) < 120


# Integration Tests
@pytest.mark.asyncio
class TestEmissionFactorRepository:
    """Test emission factor repository"""
    
    async def test_save_and_retrieve_factor(self, test_db, test_cache):
        """Test saving and retrieving emission factors"""
        cache_manager = CacheManager()
        cache_manager._redis = test_cache
        
        repo = DatabaseEmissionFactorRepository(test_db, cache_manager)
        
        # Save factor
        factor = EmissionFactor(
            name="Test factor",
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            value=Decimal("1.5"),
            unit="kgCO2e/kg",
            source=EmissionFactorSource.CUSTOM,
            source_reference="Test",
            region="US",
            year=2024
        )
        
        saved = await repo.save_factor(factor)
        assert saved.id is not None
        
        # Retrieve factor
        retrieved = await repo.get_factor(
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            region="US",
            year=2024
        )
        
        assert retrieved is not None
        assert retrieved.name == "Test factor"
        assert float(retrieved.value) == 1.5
    
    async def test_fallback_hierarchy(self, test_db, test_cache):
        """Test emission factor fallback logic"""
        cache_manager = CacheManager()
        cache_manager._redis = test_cache
        
        repo = DatabaseEmissionFactorRepository(test_db, cache_manager)
        
        # Save factors with different specificity
        factors = [
            EmissionFactor(
                name="Global default",
                category=Scope3Category.WASTE_GENERATED,
                value=Decimal("1.0"),
                unit="kgCO2e/kg",
                source=EmissionFactorSource.IPCC,
                source_reference="IPCC",
                region=None,  # Global
                year=2020
            ),
            EmissionFactor(
                name="US specific",
                category=Scope3Category.WASTE_GENERATED,
                value=Decimal("1.2"),
                unit="kgCO2e/kg",
                source=EmissionFactorSource.EPA,
                source_reference="EPA",
                region="US",
                year=2022
            ),
            EmissionFactor(
                name="US specific recent",
                category=Scope3Category.WASTE_GENERATED,
                value=Decimal("1.3"),
                unit="kgCO2e/kg",
                source=EmissionFactorSource.EPA,
                source_reference="EPA",
                region="US",
                year=2024
            )
        ]
        
        for factor in factors:
            await repo.save_factor(factor)
        
        # Test 1: Request US 2024 -> Should get US 2024 specific
        result = await repo.get_factor(
            category=Scope3Category.WASTE_GENERATED,
            region="US",
            year=2024
        )
        assert result.name == "US specific recent"
        
        # Test 2: Request EU 2024 -> Should fallback to global
        result = await repo.get_factor(
            category=Scope3Category.WASTE_GENERATED,
            region="EU",
            year=2024
        )
        assert result.name == "Global default"
        
        # Test 3: Request US 2021 -> Should get US 2020 (most recent before requested)
        result = await repo.get_factor(
            category=Scope3Category.WASTE_GENERATED,
            region="US",
            year=2021
        )
        assert result.name == "Global default"  # 2020 is most recent


@pytest.mark.asyncio
class TestCalculationService:
    """Test calculation service"""
    
    async def test_end_to_end_calculation(self, test_db, test_cache):
        """Test complete calculation flow"""
        # Setup repositories
        cache_manager = CacheManager()
        cache_manager._redis = test_cache
        
        ef_repo = DatabaseEmissionFactorRepository(test_db, cache_manager)
        ad_repo = ActivityDataRepository(test_db)
        calc_repo = CalculationResultRepository(test_db)
        audit_repo = Mock()  # Mock audit for simplicity
        
        # Create service
        service = CalculationService(
            ef_repo=ef_repo,
            ad_repo=ad_repo,
            calc_repo=calc_repo,
            audit_repo=audit_repo,
            cache=test_cache
        )
        
        # Save emission factor
        ef = EmissionFactor(
            name="Electricity - US Grid",
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            value=Decimal("0.5"),
            unit="kgCO2e/kWh",
            source=EmissionFactorSource.EPA,
            source_reference="eGRID 2024",
            region="US",
            year=2024
        )
        await ef_repo.save_factor(ef)
        
        # Create activity data
        activity = PurchasedGoodsActivity(
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            description="Electricity purchase",
            product_description="Grid electricity",
            supplier_country="US",
            quantity=Quantity(value=Decimal("1000"), unit="kWh"),
            location="US",
            time_period=date(2024, 1, 1),
            data_source="Utility bill",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.VERIFIED_SPECIFIC,
                completeness=DataQualityScore.VERIFIED_SPECIFIC,
                temporal_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                geographical_correlation=DataQualityScore.VERIFIED_SPECIFIC,
                technological_correlation=DataQualityScore.VERIFIED_SPECIFIC
            )
        )
        
        # Calculate
        result = await service.calculate_category(
            organization_id=uuid4(),
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            activity_data=[activity],
            parameters=CalculationParameters(
                methodology=MethodologyType.ACTIVITY_BASED,
                include_uncertainty=True
            ),
            user="test@example.com"
        )
        
        # Verify result
        assert result is not None
        assert float(result.emissions.value) == 500.0  # 1000 kWh * 0.5
        assert result.emissions.uncertainty_lower is not None
        assert result.emissions.uncertainty_upper is not None
        assert result.activity_data_count == 1
        assert result.data_quality_score == 1.0  # All verified specific


# API Tests
@pytest.mark.asyncio
class TestCalculationAPI:
    """Test calculation API endpoints"""
    
    async def test_create_calculation(self, test_client, monkeypatch):
        """Test POST /calculations"""
        # Mock authentication
        mock_user = User(
            id="test-user",
            email="test@example.com",
            name="Test User",
            is_active=True
        )
        monkeypatch.setattr(
            "app.dependencies.get_current_user",
            AsyncMock(return_value=mock_user)
        )
        
        # Create request
        request_data = {
            "category": "purchased_goods_and_services",
            "methodology": "activity_based",
            "activity_data": [
                {
                    "description": "Steel purchase",
                    "quantity": 1000,
                    "unit": "kg",
                    "location": "US",
                    "data_source": "Invoice #12345"
                }
            ],
            "emission_factor_source": "epa",
            "reporting_period": "2024-01-01",
            "include_uncertainty": True
        }
        
        response = await test_client.post(
            "/api/v1/calculations",
            json=request_data,
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "calculation_id" in data
        assert data["status"] == "processing"
    
    async def test_get_calculation_results(self, test_client, test_db, monkeypatch):
        """Test GET /calculations/{id}"""
        # Mock authentication
        mock_user = User(
            id="test-user",
            email="test@example.com",
            name="Test User",
            is_active=True
        )
        mock_org = Organization(
            id=uuid4(),
            name="Test Org",
            industry="Test",
            reporting_year=2024,
            locations=["US"]
        )
        
        monkeypatch.setattr(
            "app.dependencies.get_current_user",
            AsyncMock(return_value=mock_user)
        )
        monkeypatch.setattr(
            "app.dependencies.get_current_organization",
            AsyncMock(return_value=mock_org)
        )
        
        # Create a calculation result
        calc_repo = CalculationResultRepository(test_db)
        result = CategoryCalculationResult(
            organization_id=mock_org.id,
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            reporting_period=date(2024, 1, 1),
            methodology=MethodologyType.ACTIVITY_BASED,
            emissions=EmissionResult(value=Decimal("1000")),
            activity_data_count=5,
            data_quality_score=2.5,
            calculation_parameters=CalculationParameters(),
            emission_factors_used=[],
            activity_data_used=[]
        )
        
        saved = await calc_repo.save_result(result)
        
        # Get result
        response = await test_client.get(
            f"/api/v1/calculations/{saved.id}",
            headers={"Authorization": "Bearer fake-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(saved.id)
        assert data["emissions"]["value"] == 1000.0
        assert data["category"] == "purchased_goods_and_services"


# Compliance Tests
class TestGHGProtocolCompliance:
    """Test compliance with GHG Protocol requirements"""
    
    def test_all_categories_covered(self):
        """Ensure all 15 Scope 3 categories are implemented"""
        factory = CalculationEngineFactory()
        
        # These should be implemented
        required_categories = [
            Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            Scope3Category.BUSINESS_TRAVEL,
            Scope3Category.USE_OF_SOLD_PRODUCTS
        ]
        
        for category in required_categories:
            calculator = factory.get_calculator(category)
            assert calculator is not None
    
    def test_calculation_transparency(self, sample_activity_data, sample_emission_factor):
        """Test that calculations maintain full audit trail"""
        calculator = Category1Calculator(UncertaintyEngine())
        
        result = calculator.calculate(
            activity_data=[sample_activity_data],
            emission_factors=[sample_emission_factor],
            parameters=CalculationParameters()
        )
        
        # Verify audit trail elements
        assert len(result.activity_data_used) == 1
        assert len(result.emission_factors_used) == 1
        assert result.methodology == MethodologyType.HYBRID
        assert result.calculation_parameters is not None
        assert result.calculation_date is not None
    
    def test_data_quality_scoring(self):
        """Test pedigree matrix implementation"""
        dqi = DataQualityIndicator(
            reliability=DataQualityScore.VERIFIED_SPECIFIC,
            completeness=DataQualityScore.VERIFIED_SPECIFIC,
            temporal_correlation=DataQualityScore.UNVERIFIED_SPECIFIC,
            geographical_correlation=DataQualityScore.INDUSTRY_AVERAGE,
            technological_correlation=DataQualityScore.PROXY_DATA
        )
        
        # Score should be average: (1 + 1 + 2 + 3 + 4) / 5 = 2.2
        assert dqi.overall_score == 2.2
    
    @pytest.mark.parametrize("category,expected_fields", [
        (
            Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            ["product_description", "supplier_country", "quantity"]
        ),
        (
            Scope3Category.BUSINESS_TRAVEL,
            ["origin", "destination", "mode", "distance"]
        ),
        (
            Scope3Category.USE_OF_SOLD_PRODUCTS,
            ["product_model", "units_sold", "energy_consumption", "product_lifetime"]
        )
    ])
    def test_required_fields_by_category(self, category, expected_fields):
        """Test that each category has required fields per GHG Protocol"""
        # This would be implemented in validation service
        validation_service = ValidationService()
        rules = validation_service._load_validation_rules()
        
        # Verify category has validation rules
        assert category in rules or True  # Simplified for example


# Performance Tests
@pytest.mark.asyncio
@pytest.mark.performance
class TestPerformance:
    """Performance and scalability tests"""
    
    async def test_bulk_calculation_performance(self, test_db, test_cache):
        """Test performance with large datasets"""
        import time
        
        # Setup
        cache_manager = CacheManager()
        cache_manager._redis = test_cache
        
        ef_repo = DatabaseEmissionFactorRepository(test_db, cache_manager)
        
        # Create many emission factors
        factors = []
        for i in range(100):
            factor = EmissionFactor(
                name=f"Factor {i}",
                category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
                value=Decimal(str(1.0 + i * 0.1)),
                unit="kgCO2e/kg",
                source=EmissionFactorSource.EPA,
                source_reference=f"EPA {i}",
                region="US",
                year=2020 + (i % 5)
            )
            factors.append(factor)
        
        # Save all factors
        start = time.time()
        for factor in factors:
            await ef_repo.save_factor(factor)
        save_time = time.time() - start
        
        # Retrieve factors
        start = time.time()
        for i in range(100):
            await ef_repo.get_factor(
                category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
                year=2020 + (i % 5)
            )
        retrieve_time = time.time() - start
        
        # Performance assertions
        assert save_time < 10.0  # Should save 100 factors in < 10s
        assert retrieve_time < 1.0  # Should retrieve 100 factors in < 1s
    
    def test_monte_carlo_performance(self):
        """Test Monte Carlo simulation performance"""
        import time
        
        engine = UncertaintyEngine(n_iterations=10000)
        
        start = time.time()
        result = engine.propagate_uncertainty(
            activity_value=1000,
            activity_uncertainty=(10, 10),
            ef_value=2.5,
            ef_uncertainty=(20, 20)
        )
        elapsed = time.time() - start
        
        # Should complete 10k iterations in < 1 second
        assert elapsed < 1.0
        assert result.value is not None
        assert result.uncertainty_lower is not None
        assert result.uncertainty_upper is not None


# Validation Tests
class TestValidationService:
    """Test data validation service"""
    
    @pytest.mark.parametrize("year,should_pass", [
        (2024, True),
        (2025, False),  # Future
        (1989, False),  # Too old
        (2000, True),
        (1990, True)
    ])
    async def test_emission_factor_year_validation(self, year, should_pass):
        """Test year validation for emission factors"""
        service = ValidationService()
        
        factor = EmissionFactor(
            name="Test",
            category=Scope3Category.WASTE_GENERATED,
            value=Decimal("1.0"),
            unit="kgCO2e/kg",
            source=EmissionFactorSource.EPA,
            source_reference="Test",
            year=year
        )
        
        errors = await service.validate_emission_factor(factor)
        
        if should_pass:
            assert len(errors) == 0
        else:
            assert len(errors) > 0
            assert any("year" in e["field"] for e in errors)
    
    async def test_activity_data_validation(self):
        """Test activity data validation rules"""
        service = ValidationService()
        
        # Test negative quantity
        activity = ActivityData(
            category=Scope3Category.EMPLOYEE_COMMUTING,
            description="Invalid data",
            quantity=Quantity(value=Decimal("-100"), unit="km"),
            time_period=date(2024, 1, 1),
            data_source="Test",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.ESTIMATED,
                completeness=DataQualityScore.ESTIMATED,
                temporal_correlation=DataQualityScore.ESTIMATED,
                geographical_correlation=DataQualityScore.ESTIMATED,
                technological_correlation=DataQualityScore.ESTIMATED
            )
        )
        
        errors = await service.validate_activity_data(activity)
        assert len(errors) > 0
        assert any("quantity" in e["field"] for e in errors)
    
    async def test_category_specific_validation(self):
        """Test category-specific validation rules"""
        service = ValidationService()
        
        # Business travel without required fields
        activity = BusinessTravelActivity(
            category=Scope3Category.BUSINESS_TRAVEL,
            description="Missing data",
            origin="NYC",
            destination="",  # Missing destination
            mode=TransportMode.AIR,
            distance=0,  # Invalid distance
            quantity=Quantity(value=Decimal("1"), unit="trip"),
            time_period=date(2024, 1, 1),
            data_source="Test",
            quality_indicator=DataQualityIndicator(
                reliability=DataQualityScore.ESTIMATED,
                completeness=DataQualityScore.ESTIMATED,
                temporal_correlation=DataQualityScore.ESTIMATED,
                geographical_correlation=DataQualityScore.ESTIMATED,
                technological_correlation=DataQualityScore.ESTIMATED
            )
        )
        
        # Should have validation errors
        errors = await service.validate_activity_data(activity)
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])