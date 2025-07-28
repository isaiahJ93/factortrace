#!/usr/bin/env python3
"""Complete fix for api.py"""

import re

def fix_api_file():
    with open("app/api/v1/api.py", "r") as f:
        content = f.read()
    
    # Find the api_status function and replace it with a correct version
    # Pattern to find the broken api_status function
    pattern = r'@api_router\.get\("/status".*?\)\s*async def api_status\(\):[^@]*?(?=@api_router|\Z)'
    
    replacement = '''@api_router.get("/status", tags=["api", "monitoring"])
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
        "environment": settings.ENVIRONMENT,
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
            "ghg_analytics": "ghg_analytics" in loader.loaded_endpoints
        }
    }

'''
    
    # Replace the broken function
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write back
    with open("app/api/v1/api.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed api.py file")

if __name__ == "__main__":
    fix_api_file()
