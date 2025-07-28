#!/usr/bin/env python3
"""Fix syntax error in api.py around line 370"""

def fix_api_syntax():
    with open("app/api/v1/api.py", "r") as f:
        content = f.read()
    
    # Find the problematic section and fix it
    # The "features": { line needs to be part of the return statement
    
    # Replace the broken section
    broken_pattern = '''    critical_endpoints = {
        name: info for name, info in endpoint_registry.items() 
        if info.get("critical", False)
    }
    
    "features": {'''
    
    fixed_pattern = '''    critical_endpoints = {
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
        "features": {'''
    
    content = content.replace(broken_pattern, fixed_pattern)
    
    # Also need to close the features dict properly
    # Find where the features dict ends
    features_end = content.find('"ghg_external_providers": "ghg_emission_factors" in loader.loaded_endpoints,')
    if features_end != -1:
        # Add the closing braces after the last feature
        end_pos = features_end + len('"ghg_external_providers": "ghg_emission_factors" in loader.loaded_endpoints,')
        content = content[:end_pos].rstrip(',') + '\n        }\n    }' + content[end_pos:]
    
    with open("app/api/v1/api.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed syntax error in app/api/v1/api.py")

if __name__ == "__main__":
    fix_api_syntax()
