#!/usr/bin/env python3
"""Fix the api_status function in api.py"""

def fix_api_status():
    with open("app/api/v1/api.py", "r") as f:
        lines = f.readlines()
    
    # Find the api_status function
    api_status_start = None
    for i, line in enumerate(lines):
        if 'async def api_status():' in line:
            api_status_start = i
            break
    
    if api_status_start is None:
        print("❌ Could not find api_status function")
        return
    
    # Find where we have the broken features section
    features_line = None
    for i in range(api_status_start, min(api_status_start + 100, len(lines))):
        if '"features": {' in lines[i] and 'return' not in lines[i]:
            features_line = i
            break
    
    if features_line is None:
        print("❌ Could not find features section")
        return
    
    # Count braces to find where the function should end
    open_braces = 0
    close_braces = 0
    func_end = None
    
    # Start from the features line and count braces
    for i in range(features_line, min(features_line + 200, len(lines))):
        open_braces += lines[i].count('{')
        close_braces += lines[i].count('}')
        
        # Check if we have a new function definition (that would mean we went too far)
        if 'async def' in lines[i] and i > features_line + 1:
            func_end = i - 1
            break
    
    # Now let's rebuild the function properly
    new_lines = lines[:features_line]
    
    # Add the proper return statement with features
    new_lines.append('''    
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
            # New GHG Protocol features
            "ghg_protocol_calculations": "ghg_calculations" in loader.loaded_endpoints,
            "ghg_uncertainty_analysis": "ghg_calculations" in loader.loaded_endpoints,
            "ghg_external_providers": "ghg_emission_factors" in loader.loaded_endpoints,
            "cdp_tcfd_reporting": "ghg_reports" in loader.loaded_endpoints,
            "ghg_analytics": "ghg_analytics" in loader.loaded_endpoints
        }
    }

''')
    
    # Find the next function after api_status and add everything from there
    next_func = None
    for i in range(features_line, len(lines)):
        if '@api_router' in lines[i] or 'async def' in lines[i]:
            if 'api_status' not in lines[i]:
                next_func = i
                break
    
    if next_func:
        new_lines.extend(lines[next_func:])
    else:
        # If we can't find the next function, just add the rest
        new_lines.extend(lines[func_end if func_end else features_line + 50:])
    
    # Write the fixed content
    with open("app/api/v1/api.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Fixed api_status function")

if __name__ == "__main__":
    fix_api_status()
