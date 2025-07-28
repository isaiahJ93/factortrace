# app/db/base.py
"""
Database base configuration
Import all models here so Alembic can detect them
"""
from app.core.database import Base  # Import Base from the central database module

# Import all models to ensure they're registered with SQLAlchemy
# This is important for Alembic migrations to work properly
def import_all_models():
    """Import all models to register them with SQLAlchemy"""
    imported_models = []
    failed_imports = []
    
    # Core models
    model_imports = [
        # Existing models
        ("app.models.user", "User"),
        ("app.models.emission", "Emission"),
        ("app.models.emission_factor", "EmissionFactor"),
        ("app.models.voucher", "Voucher"),
        ("app.models.payment", "Payment"),
        ("app.models.data_quality", "DataQualityScore"),
        ("app.models.evidence_document", "EvidenceDocument"),
        
        # New GHG Protocol models
        ("app.models.ghg_domain", "Organization"),
        ("app.models.ghg_domain", "EmissionResult"),
        ("app.models.ghg_domain", "ActivityData"),
        ("app.models.ghg_domain", "PurchasedGoodsActivity"),
        ("app.models.ghg_domain", "BusinessTravelActivity"),
        ("app.models.ghg_domain", "UpstreamTransportActivity"),
        ("app.models.ghg_domain", "WasteActivity"),
        ("app.models.ghg_domain", "UsePhaseActivity"),
        ("app.models.ghg_domain", "CategoryCalculationResult"),
        ("app.models.ghg_domain", "Scope3Inventory"),
        ("app.models.ghg_domain", "AuditLogEntry"),
        
        # New GHG database models
        ("app.models.ghg_tables", "OrganizationDB"),
        ("app.models.ghg_tables", "EmissionFactorDB"),
        ("app.models.ghg_tables", "ActivityDataDB"),
        ("app.models.ghg_tables", "CalculationResultDB"),
        ("app.models.ghg_tables", "Scope3InventoryDB"),
        ("app.models.ghg_tables", "AuditLogDB"),
        ("app.models.ghg_tables", "EmissionTimeSeriesDB"),
        
        # Additional models that might exist
        ("app.models.emission_data", "EmissionData"),
        ("app.models.emissions_record", "EmissionsRecord"),
        ("app.models.emissions_voucher", "EmissionsVoucher"),
        ("app.models.climate", "ClimateTarget"),
        ("app.models.materiality", "MaterialityAssessment"),
        ("app.models.uncertainty_model", "UncertaintyModel"),
    ]
    
    for module_path, model_name in model_imports:
        try:
            module = __import__(module_path, fromlist=[model_name])
            imported_models.append(f"{module_path}.{model_name}")
        except ImportError as e:
            failed_imports.append(f"{module_path}.{model_name}: {str(e)}")
        except Exception as e:
            failed_imports.append(f"{module_path}.{model_name}: Unexpected error - {str(e)}")
    
    # Log results
    if imported_models:
        print(f"✅ Successfully imported {len(imported_models)} models:")
        for model in imported_models[:5]:  # Show first 5
            print(f"   - {model}")
        if len(imported_models) > 5:
            print(f"   ... and {len(imported_models) - 5} more")
    
    if failed_imports:
        print(f"\n⚠️  Failed to import {len(failed_imports)} models:")
        for failure in failed_imports[:5]:  # Show first 5
            print(f"   - {failure}")
        if len(failed_imports) > 5:
            print(f"   ... and {len(failed_imports) - 5} more")
    
    return imported_models, failed_imports

# Metadata naming conventions for better constraint names
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Apply naming convention to Base metadata
Base.metadata.naming_convention = naming_convention

# Import all models when this module is imported
# This ensures Alembic can see all models
import_all_models()

# Export Base so other modules can import from here
__all__ = ["Base", "import_all_models"]