# app/api/v1/api.py
"""
API v1 Router - Smart endpoint loading with graceful degradation
Prioritizes critical endpoints and provides detailed status reporting
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional, Tuple
import logging
import importlib
import time
from datetime import datetime
from typing import Dict, Any
from app.api.v1.endpoints import (
    emissions,
    emission_factors,
    ghg_calculations,
    data_quality,
    voucher,
    compliance,
    auth,
    users,
    xbrl,
    scope3,
    esrs_e1_full,
    ghg_emission_factors,
    ghg_activity_data,
    ghg_reports,
    ghg_analytics,
    ghg_inventory,
    ghg_calculator
)
from app.core.config import settings
# Configure logging
logger = logging.getLogger(__name__)
# Security scheme for Swagger UI
security = HTTPBearer()
# Create main API router
from app.api.v1.endpoints import verify_voucher
logger.info(f"✅ Imported verify_voucher module: {verify_voucher}")
logger.info(f"✅ Verify router: {verify_voucher.router}")

api_router = APIRouter()
from app.api.v1.endpoints import esrs_e1_full
# Track endpoint loading status
endpoint_registry: Dict[str, Dict[str, Any]] = {}
class EndpointLoader:
    """Smart endpoint loader with dependency checking"""
    def __init__(self):
        self.loaded_endpoints: List[str] = []
        self.failed_endpoints: List[Tuple[str, str]] = []
        self.load_times: Dict[str, float] = {}
    def register_endpoint(
        self,
        name: str,
        module_path: str,
        router_attr: str = "router",
        prefix: str = "",
        tags: List[str] = None,
        dependencies: List[str] = None,
        critical: bool = False,
        description: str = ""
    ) -> bool:
        """Register and load an endpoint with smart error handling"""
        start_time = time.time()
        # Check dependencies first
        if dependencies:
            for dep in dependencies:
                if dep not in self.loaded_endpoints:
                    error_msg = f"Missing dependency: {dep}"
                    logger.warning(f"❌ {name}: {error_msg}")
                    self.failed_endpoints.append((name, error_msg))
                    endpoint_registry[name] = {
                        "status": "failed",
                        "error": error_msg,
                        "critical": critical
                    }
                    return False
        try:
            # Import the module
            module = importlib.import_module(f"app.api.v1.endpoints.{module_path}")
            router = getattr(module, router_attr)
            # Include the router
            api_router.include_router(
                router,
                prefix=prefix,
                tags=tags or [name.replace("_", "-")]
            )
            # Track success
            load_time = time.time() - start_time
            self.loaded_endpoints.append(name)
            self.load_times[name] = load_time
            endpoint_registry[name] = {
                "status": "active",
                "prefix": prefix,
                "tags": tags or [name.replace("_", "-")],
                "description": description,
                "critical": critical,
                "load_time": load_time,
                "loaded_at": datetime.utcnow().isoformat()
            }
            logger.info(f"✅ {name}: Loaded successfully at {prefix} ({load_time:.3f}s)")
            return True
        except ImportError as e:
            error_msg = f"Import error: {str(e)}"
            logger.error(f"❌ {name}: {error_msg}")
            self.failed_endpoints.append((name, error_msg))
            endpoint_registry[name] = {
                "status": "failed",
                "error": error_msg,
                "critical": critical,
                "module": module_path
            }
            if critical:
                logger.critical(f"CRITICAL endpoint {name} failed to load!")
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {name}: {error_msg}", exc_info=True)
            self.failed_endpoints.append((name, error_msg))
            endpoint_registry[name] = {
                "status": "failed",
                "error": error_msg,
                "critical": critical,
                "exception_type": type(e).__name__
            }
            return False
# Initialize loader
loader = EndpointLoader()
# ============= CRITICAL ENDPOINTS (Must load for basic operation) =============
# Health checks - ALWAYS first, no dependencies
loader.register_endpoint(
    name="health",
    module_path="health",
    prefix="/health",
    tags=["health", "monitoring"],
    critical=True,
    description="System health monitoring endpoints"
)
# ============= CORE BUSINESS ENDPOINTS =============
# Voucher/Payment system - Critical for revenue
# Voucher/Payment system - Critical for revenue
loader.register_endpoint(
    name="vouchers",
    module_path="voucher",
    prefix="/vouchers",
    tags=["vouchers", "payments"],
    critical=True,
    description="Voucher management and Stripe checkout"
)
# ============= AUTHENTICATION & USERS =============
# Authentication - Required for most operations
loader.register_endpoint(
    name="auth",
    module_path="auth",
    prefix="/auth",
    tags=["authentication"],
    dependencies=["health"],
    critical=True,
    description="User authentication and JWT tokens"
)
# User management
loader.register_endpoint(
    name="users",
    module_path="users",
    prefix="/users",
    tags=["users"],
    dependencies=["auth"],
    description="User account management"
)
# ============= EMISSIONS TRACKING CORE =============
# Emission factors - Required for calculations
loader.register_endpoint(
    name="emission_factors",
    module_path="emission_factors",
    prefix="/emission-factors",
    tags=["emission-factors"],
    description="Emission factor database and management"
)
# Emissions tracking - Core functionality
loader.register_endpoint(
    name="emissions",
    module_path="emissions",
    prefix="/emissions",
    tags=["emissions"],
    dependencies=["emission_factors"],
    critical=True,
    description="Emissions data entry and tracking"
)
# ============= DATA QUALITY & COMPLIANCE =============
# Data quality assessment
loader.register_endpoint(
    name="data_quality",
    module_path="data_quality",
    prefix="/data-quality",
    tags=["data-quality"],
    dependencies=["emissions"],
    description="Data quality scoring and validation"
)
# Compliance reporting
loader.register_endpoint(
    name="compliance",
    module_path="compliance",
    prefix="/compliance",
    tags=["compliance", "reporting"],
    dependencies=["emissions", "data_quality"],
    description="ESRS E1 compliance reporting"
)
# ============= ADVANCED FEATURES =============
# XBRL export
loader.register_endpoint(
    name="xbrl",
    module_path="xbrl",
    prefix="/xbrl",
    tags=["xbrl", "export"],
    dependencies=["compliance"],
    description="XBRL format export for regulatory filing"
)
# Scope 3 emissions
loader.register_endpoint(
    name="scope3",
    module_path="scope3",
    prefix="/scope3",
    tags=["scope3", "emissions"],
    dependencies=["emissions"],
    description="Scope 3 emissions calculations"
)
# ESRS E1 Full compliance
loader.register_endpoint(
    name="esrs_e1_full",
    module_path="esrs_e1_full",
    prefix="/esrs-e1",
    tags=["esrs-e1", "compliance"],
    dependencies=["compliance"],
    description="Full ESRS E1 compliance features"
)
# ============= GHG PROTOCOL COMPREHENSIVE CALCULATIONS =============
# GHG Protocol Scope 3 Calculations - Advanced
loader.register_endpoint(
    name="ghg_calculations",
    module_path="ghg_calculations",
    prefix="/ghg/calculations",
    tags=["ghg-protocol", "scope3", "calculations"],
    dependencies=["emissions", "emission_factors"],
    critical=True,
    description="Comprehensive GHG Protocol Scope 3 calculations with uncertainty analysis"
)
# GHG Emission Factors Management
loader.register_endpoint(
    name="ghg_emission_factors",
    module_path="ghg_emission_factors",
    prefix="/ghg/emission-factors",
    tags=["ghg-protocol", "emission-factors"],
    dependencies=["emission_factors"],
    description="Advanced emission factor management with external provider integration"
)
# GHG Activity Data Management
loader.register_endpoint(
    name="ghg_activity_data",
    module_path="ghg_activity_data",
    prefix="/ghg/activity-data",
    tags=["ghg-protocol", "activity-data"],
    dependencies=["ghg_calculations"],
    description="Activity data management for GHG calculations"
)
# GHG Reports Generation
loader.register_endpoint(
    name="ghg_reports",
    module_path="ghg_reports",
    prefix="/ghg/reports",
    tags=["ghg-protocol", "reports", "cdp", "tcfd"],
    dependencies=["ghg_calculations", "compliance"],
    description="Generate CDP, TCFD, and CSRD compliant reports"
)
# GHG Analytics and Insights
loader.register_endpoint(
    name="ghg_analytics",
    module_path="ghg_analytics",
    prefix="/ghg/analytics",
    tags=["ghg-protocol", "analytics", "insights"],
    dependencies=["ghg_calculations"],
    description="Analytics and insights for emissions data"
)
# GHG Inventory Management
loader.register_endpoint(
    name="ghg_inventory",
    module_path="ghg_inventory",
    prefix="/ghg/inventory",
    tags=["ghg-protocol", "inventory"],
    dependencies=["ghg_calculations"],
    description="Complete GHG inventory management"
)
# ============= REPORTING ENDPOINTS =============
# CSRD Summary Reports
loader.register_endpoint(
    name="reports",
    module_path="reports",
    prefix="/reports",
    tags=["reports", "csrd", "esrs"],
    dependencies=["emissions"],
    description="CSRD/ESRS compliant report generation with iXBRL tags"
)

# ============= REGULATORY REGIME ENDPOINTS =============
# CBAM (Carbon Border Adjustment Mechanism) - EU Regulation 2023/956
loader.register_endpoint(
    name="cbam",
    module_path="cbam",
    prefix="/cbam",
    tags=["cbam", "regulatory-regimes"],
    dependencies=["auth", "emission_factors"],
    description="CBAM declarations, products, and embedded emissions calculations"
)

# EUDR (EU Deforestation Regulation) - Regulation (EU) 2023/1115
loader.register_endpoint(
    name="eudr",
    module_path="eudr",
    prefix="/eudr",
    tags=["eudr", "regulatory-regimes"],
    dependencies=["auth", "emission_factors"],
    description="EUDR supply chain traceability, geo risk assessment, and due diligence"
)

# ISSB (IFRS S1 + S2) - Climate-related financial disclosures
loader.register_endpoint(
    name="issb",
    module_path="issb",
    prefix="/issb",
    tags=["issb", "regulatory-regimes"],
    dependencies=["auth", "emission_factors"],
    description="ISSB climate-related financial disclosures, scenario analysis, and materiality assessment"
)

# ============= SELF-SERVE WIZARD =============
# Compliance Wizard - The "€500 magic moment" for Tier 2 suppliers
loader.register_endpoint(
    name="wizard",
    module_path="wizard",
    prefix="/wizard",
    tags=["wizard", "self-serve"],
    dependencies=["auth", "vouchers", "emission_factors"],
    description="Self-serve compliance wizard - email to report in 10 minutes"
)

# ============= ADMINISTRATIVE ENDPOINTS =============
# Admin endpoints
loader.register_endpoint(
    name="admin",
    module_path="admin",
    prefix="/admin",
    tags=["admin"],
    dependencies=["auth", "users"],
    description="Administrative functions"
)
# ============= API STATUS AND DOCUMENTATION =============
@api_router.get("/", tags=["api"])
async def api_root():
    """API v1 root - provides API information and endpoint directory"""
    total_endpoints = len(endpoint_registry)
    active_endpoints = sum(1 for e in endpoint_registry.values() if e["status"] == "active")
    # Get list of active endpoints with their prefixes
    active_endpoint_list = {
        name: {
            "url": info["prefix"],
            "description": info.get("description", ""),
            "tags": info.get("tags", [])
        }
        for name, info in endpoint_registry.items()
        if info["status"] == "active"
    }
    return {
        "api": "FactorTrace API v1",
        "version": settings.VERSION,
        "status": "operational" if active_endpoints > 0 else "error",
        "endpoints": {
            "total": total_endpoints,
            "active": active_endpoints,
            "failed": total_endpoints - active_endpoints
        },
        "available_endpoints": active_endpoint_list,
        "documentation": "/docs" if settings.environment != "production" else None,
        "support": "support@factortrace.com"
    }
@api_router.get("/status", tags=["api", "monitoring"])
async def api_status():
    """Detailed API status with endpoint health information"""
    # Check critical endpoints
    critical_endpoints = {
        name: info for name, info in endpoint_registry.items() 
        if info.get("critical", False)
    }
    all_critical_healthy = all(
        ep["status"] == "active" for ep in critical_endpoints.values()
    )
    # Calculate API health score (0-100)
    total_endpoints = len(endpoint_registry)
    active_endpoints = sum(1 for e in endpoint_registry.values() if e["status"] == "active")
    critical_active = sum(1 for e in critical_endpoints.values() if e["status"] == "active")
    health_score = 0
    if total_endpoints > 0:
        # 70% weight for critical endpoints, 30% for others
        critical_weight = 0.7
        other_weight = 0.3
        critical_score = (critical_active / len(critical_endpoints) * 100) if critical_endpoints else 100
        overall_score = (active_endpoints / total_endpoints * 100)
        health_score = (critical_score * critical_weight) + (overall_score * other_weight)
    return {
        "status": "healthy" if all_critical_healthy else "degraded",
        "health_score": round(health_score, 2),
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": settings.VERSION,
        "environment": settings.environment,
        "endpoints": {
            "summary": {
                "total": total_endpoints,
                "active": active_endpoints,
                "failed": total_endpoints - active_endpoints,
                "critical_active": critical_active,
                "critical_total": len(critical_endpoints)
            },
            "details": endpoint_registry,
            "load_times": loader.load_times,
            "failures": [
                {"endpoint": name, "error": error} 
                for name, error in loader.failed_endpoints
            ]
        },
        "features": {
            "payments": "vouchers" in loader.loaded_endpoints,
            "emissions_tracking": "emissions" in loader.loaded_endpoints,
            "compliance_reporting": "compliance" in loader.loaded_endpoints,
            "xbrl_export": "xbrl" in loader.loaded_endpoints,
            "authentication": "auth" in loader.loaded_endpoints,
            "ghg_protocol_calculations": "ghg_calculations" in loader.loaded_endpoints,
            "ghg_uncertainty_analysis": "ghg_calculations" in loader.loaded_endpoints,
            "ghg_external_providers": "ghg_emission_factors" in loader.loaded_endpoints,
            "cdp_tcfd_reporting": "ghg_reports" in loader.loaded_endpoints,
            "ghg_analytics": "ghg_analytics" in loader.loaded_endpoints,
            "cbam_declarations": "cbam" in loader.loaded_endpoints,
            "eudr_due_diligence": "eudr" in loader.loaded_endpoints,
            "issb_disclosures": "issb" in loader.loaded_endpoints,
            "compliance_wizard": "wizard" in loader.loaded_endpoints
        }
    }
@api_router.get("/endpoints", tags=["api"])
async def list_endpoints():
    """List all registered endpoints with their status"""
    return {
        "endpoints": [
            {
                "name": name,
                "status": info["status"],
                "prefix": info.get("prefix", "N/A"),
                "tags": info.get("tags", []),
                "description": info.get("description", ""),
                "critical": info.get("critical", False),
                "error": info.get("error") if info["status"] == "failed" else None
            }
            for name, info in endpoint_registry.items()
        ],
        "statistics": {
            "total": len(endpoint_registry),
            "active": sum(1 for e in endpoint_registry.values() if e["status"] == "active"),
            "failed": sum(1 for e in endpoint_registry.values() if e["status"] == "failed"),
            "critical_failures": sum(
                1 for e in endpoint_registry.values() 
                if e["status"] == "failed" and e.get("critical", False)
            )
        }
    }
api_router.include_router(esrs_e1_full.router, prefix="/esrs-e1", tags=["ESRS E1"])
api_router.include_router(
    ghg_calculator.router,
    prefix="/ghg-calculator",
    tags=["ghg-calculator"]
)
api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])

# Direct iXBRL export route for frontend compatibility
@api_router.post("/export/ixbrl")
async def export_ixbrl_direct(data: Dict[str, Any] = Body(...)):
    """
    Direct iXBRL export endpoint that forwards to compliance export.
    This matches the URL that the frontend is expecting.
    """
    from app.api.v1.endpoints.compliance import export_ixbrl
    
    # Forward to the compliance endpoint with the correct format
    return await export_ixbrl({
        "format": "ixbrl",
        "data": data
    })

@api_router.get("/ready", tags=["health", "monitoring"])
async def readiness_check():
    """Kubernetes readiness probe - checks if API is ready to serve traffic"""
    # Check if critical endpoints are loaded
    critical_loaded = all(
        endpoint_registry.get(name, {}).get("status") == "active"
        for name in ["health", "vouchers", "auth", "emissions"]
    )
    if not critical_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Critical endpoints not ready"
        )
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "critical_endpoints": "active"
    }
# ============= API CONFIGURATION =============
# Log final loading status
total = len(endpoint_registry)
loaded = len(loader.loaded_endpoints)
failed = len(loader.failed_endpoints)
logger.info("=" * 60)
logger.info(f"API v1 Router Configuration Complete")
logger.info(f"Endpoints: {loaded}/{total} loaded successfully")
if failed > 0:
    logger.warning(f"Failed endpoints ({failed}):")
    for name, error in loader.failed_endpoints:
        logger.warning(f"  - {name}: {error}")
# Check critical endpoints
critical_failures = [
    name for name, info in endpoint_registry.items()
    if info.get("critical") and info["status"] == "failed"
]
if critical_failures:
    logger.critical(f"CRITICAL endpoints failed: {', '.join(critical_failures)}")
    logger.critical("API may not function correctly!")
logger.info("=" * 60)
# Export for use in other modules
__all__ = ["api_router", "endpoint_registry"]