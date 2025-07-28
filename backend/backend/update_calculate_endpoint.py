import re

# Read the file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Check if we're already storing results
if "app.state" not in content:
    # Add app state initialization after app creation
    app_creation = content.find('app = FastAPI')
    if app_creation > 0:
        # Find the end of the FastAPI() call
        insert_pos = content.find('\n', app_creation)
        state_init = '''

# Initialize app state for storing results
from types import SimpleNamespace
app.state = SimpleNamespace()
app.state.last_calculation = None
'''
        content = content[:insert_pos] + state_init + content[insert_pos:]

# Now update the calculate endpoint to store results
# Find the calculate-with-monte-carlo endpoint
calc_pattern = r'(@app\.post\("/api/v1/calculate-with-monte-carlo"\)[\s\S]*?)(return\s+{[\s\S]*?})'

def update_calc(match):
    before_return = match.group(1)
    return_statement = match.group(2)
    
    # Add storage before return
    storage_code = '''
    # Store results for dashboard
    if hasattr(app, 'state'):
        # Calculate scope totals from emissions
        scope1_total = sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["stationary_combustion", "mobile_combustion", "process_emissions", "fugitive_emissions", "natural_gas"])
        scope2_total = sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["purchased_electricity", "electricity", "purchased_steam", "purchased_heating", "purchased_cooling"])
        scope3_total = sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["business_travel", "purchased_goods_services", "capital_goods", "fuel_energy_activities", "upstream_transport", "waste_generated", "employee_commuting"])
        
        app.state.last_calculation = {
            "scope1_total": scope1_total,
            "scope2_total": scope2_total,
            "scope3_total": scope3_total,
            "total_emissions": total_emissions,
            "last_updated": datetime.now().isoformat(),
            "calculation_id": str(uuid.uuid4())
        }
    
    '''
    
    return before_return + storage_code + return_statement

content = re.sub(calc_pattern, update_calc, content, flags=re.DOTALL)

# Update the summary endpoint to return stored data
summary_pattern = r'(@app\.get\("/api/v1/emissions/summary"\)[\s\S]*?def get_emissions_summary[\s\S]*?return\s+{[\s\S]*?})'

def update_summary(match):
    return '''@app.get("/api/v1/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary for dashboard"""
    if hasattr(app, 'state') and app.state.last_calculation:
        return app.state.last_calculation
    
    return {
        "scope1_total": 0,
        "scope2_total": 0,
        "scope3_total": 0,
        "total_emissions": 0,
        "last_updated": None,
        "calculation_id": None
    }'''

content = re.sub(summary_pattern, update_summary, content, flags=re.DOTALL)

# Write back
with open('ghg_monte_carlo_api.py', 'w') as f:
    f.write(content)

print("✅ Updated calculate endpoint to store results!")
print("✅ Updated summary endpoint to return stored results!")
