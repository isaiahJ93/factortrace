import re

with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Find the calculate endpoint
calc_start = content.find('@app.post("/api/v1/calculate-with-monte-carlo")')
if calc_start > 0:
    # Find where it returns the response (look for the return statement)
    # Search for "return {" after the endpoint
    return_pos = content.find('return {', calc_start)
    
    if return_pos > 0:
        # Check if we're already storing
        check_area = content[calc_start:return_pos]
        if 'app.state.last_calculation' not in check_area:
            print("🔧 Adding storage code...")
            
            # Add storage code before the return
            storage_code = '''
    # Store results for dashboard
    if hasattr(app, 'state'):
        # Calculate scope totals from breakdown
        scope1_total = 0
        scope2_total = 0  
        scope3_total = 0
        
        for item in breakdown:
            emissions_value = item.get("emissions_value", 0)
            # Determine scope from activity type
            activity = item.get("activity_type", "").lower()
            
            if activity in ["natural_gas", "stationary_combustion", "mobile_combustion", "fugitive_emissions"]:
                scope1_total += emissions_value
            elif activity in ["electricity", "purchased_electricity", "purchased_steam", "purchased_heating", "purchased_cooling"]:
                scope2_total += emissions_value
            else:
                scope3_total += emissions_value
        
        app.state.last_calculation = {
            "scope1_total": scope1_total,
            "scope2_total": scope2_total,
            "scope3_total": scope3_total,
            "total_emissions": total_emissions,
            "last_updated": datetime.now().isoformat(),
            "calculation_id": str(uuid.uuid4())
        }
        print(f"DEBUG: Stored calculation - Total: {total_emissions}, S1: {scope1_total}, S2: {scope2_total}, S3: {scope3_total}")
    
'''
            content = content[:return_pos] + storage_code + content[return_pos:]
            
            # Also add datetime import if missing
            if 'from datetime import datetime' not in content and 'import datetime' not in content:
                import_pos = content.find('from datetime import date')
                if import_pos > 0:
                    content = content[:import_pos] + 'from datetime import datetime, date\n' + content[import_pos+len('from datetime import date\n'):]
            
            # Add uuid import if missing
            if 'import uuid' not in content:
                import_pos = content.find('import uvicorn')
                if import_pos > 0:
                    content = content[:import_pos] + 'import uuid\n' + content[import_pos:]
            
            with open('ghg_monte_carlo_api.py', 'w') as f:
                f.write(content)
            
            print("✅ Added storage code!")
            print("🔄 Restart the server")
        else:
            print("✅ Storage code already exists")
    else:
        print("❌ Could not find return statement")
else:
    print("❌ Could not find calculate endpoint")
