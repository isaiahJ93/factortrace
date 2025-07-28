import re

# Read the file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# 1. Add state initialization after app creation
if "app.state" not in content:
    app_line = content.find('app = FastAPI')
    if app_line > 0:
        end_line = content.find('\n', app_line)
        init_code = '''

# Initialize state for storing results
from types import SimpleNamespace
app.state = SimpleNamespace()
app.state.last_calculation = None
'''
        content = content[:end_line] + init_code + content[end_line:]

# 2. Update calculate endpoint to store results
# Find the calculate function
calc_start = content.find('@app.post("/api/v1/calculate-with-monte-carlo")')
if calc_start > 0:
    # Find the return statement in this function
    func_start = content.find('async def', calc_start)
    # Find the corresponding return
    return_pos = content.find('return {', func_start)
    
    if return_pos > 0 and "app.state.last_calculation" not in content:
        storage_code = '''
    # Store results for dashboard
    scope_totals = {"scope1": 0, "scope2": 0, "scope3": 0}
    
    # Map activity types to scopes
    scope_mapping = {
        # Scope 1
        "stationary_combustion": 1, "mobile_combustion": 1, 
        "process_emissions": 1, "fugitive_emissions": 1, "natural_gas": 1,
        # Scope 2
        "electricity": 2, "purchased_electricity": 2,
        "purchased_steam": 2, "purchased_heating": 2, "purchased_cooling": 2,
        # Scope 3
        "business_travel": 3, "purchased_goods_services": 3,
        "capital_goods": 3, "fuel_energy_activities": 3,
        "upstream_transport": 3, "waste_generated": 3,
        "employee_commuting": 3, "upstream_leased_assets": 3,
        "downstream_transport": 3, "processing_sold_products": 3,
        "use_of_sold_products": 3, "end_of_life_treatment": 3,
        "downstream_leased_assets": 3, "franchises": 3, "investments": 3
    }
    
    # Calculate scope totals
    for emission in emissions:
        activity_type = emission.get("activity_type", "")
        scope = scope_mapping.get(activity_type, 0)
        if scope == 1:
            scope_totals["scope1"] += emission.get("emissions_value", 0)
        elif scope == 2:
            scope_totals["scope2"] += emission.get("emissions_value", 0)
        elif scope == 3:
            scope_totals["scope3"] += emission.get("emissions_value", 0)
    
    app.state.last_calculation = {
        "scope1_total": scope_totals["scope1"],
        "scope2_total": scope_totals["scope2"],
        "scope3_total": scope_totals["scope3"],
        "total_emissions": total_emissions,
        "last_updated": datetime.now().isoformat(),
        "calculation_id": str(uuid.uuid4())
    }
    
    '''
        content = content[:return_pos] + storage_code + content[return_pos:]

# 3. Update summary endpoint to return stored data
summary_start = content.find('@app.get("/api/v1/emissions/summary")')
if summary_start > 0:
    summary_end = content.find('\n@app.', summary_start + 1)
    if summary_end == -1:
        summary_end = content.find('\nif __name__', summary_start)
    
    new_summary = '''@app.get("/api/v1/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary for dashboard"""
    if hasattr(app, 'state') and hasattr(app.state, 'last_calculation') and app.state.last_calculation:
        return app.state.last_calculation
    
    return {
        "scope1_total": 0,
        "scope2_total": 0,
        "scope3_total": 0,
        "total_emissions": 0,
        "last_updated": None,
        "calculation_id": None
    }

'''
    content = content[:summary_start] + new_summary + content[summary_end:]

# Write back
with open('ghg_monte_carlo_api.py', 'w') as f:
    f.write(content)

print("✅ Integration complete!")
print("📊 Calculate endpoint now stores results")
print("📈 Summary endpoint now returns stored results")
print("�� Restart the server to apply changes")
