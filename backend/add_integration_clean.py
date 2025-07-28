import re

# Read the restored file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# 1. Add import at the top if needed
if 'from types import SimpleNamespace' not in content:
    import_pos = content.find('import uvicorn')
    if import_pos > 0:
        content = content[:import_pos] + 'from types import SimpleNamespace\n' + content[import_pos:]

# 2. Add state initialization after app creation
if 'app.state' not in content:
    # Find where app is created
    app_match = re.search(r'(app = FastAPI\([^)]*\))', content, re.DOTALL)
    if app_match:
        insert_pos = app_match.end()
        state_init = '''

# Initialize state for storing results  
app.state = SimpleNamespace()
app.state.last_calculation = None
'''
        content = content[:insert_pos] + state_init + content[insert_pos:]

# 3. Update calculate endpoint to store results
calc_pos = content.find('@app.post("/api/v1/calculate-with-monte-carlo")')
if calc_pos > 0:
    # Find the return statement in this function
    return_match = re.search(r'(return\s+{[^}]+})', content[calc_pos:], re.DOTALL)
    if return_match and 'app.state.last_calculation' not in content:
        return_pos = calc_pos + return_match.start()
        
        storage_code = '''
    # Store results for dashboard
    if hasattr(app, 'state'):
        app.state.last_calculation = {
            "scope1_total": sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["natural_gas", "stationary_combustion", "mobile_combustion"]),
            "scope2_total": sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["electricity", "purchased_electricity"]),
            "scope3_total": sum(e.get("emissions_value", 0) for e in emissions if e.get("activity_type") in ["business_travel"]),
            "total_emissions": total_emissions,
            "last_updated": datetime.now().isoformat(),
            "calculation_id": str(uuid.uuid4())
        }
    
    '''
        content = content[:return_pos] + storage_code + content[return_pos:]

# 4. Update summary endpoint
if '/api/v1/emissions/summary' in content:
    # Replace the summary function
    summary_pattern = r'@app\.get\("/api/v1/emissions/summary"\)[\s\S]*?(?=@app\.|if __name__)'
    new_summary = '''@app.get("/api/v1/emissions/summary")
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
    }

'''
    content = re.sub(summary_pattern, new_summary, content)

# Write to a new file first
with open('ghg_monte_carlo_api_integrated.py', 'w') as f:
    f.write(content)

print("✅ Created ghg_monte_carlo_api_integrated.py")
print("🔍 Test it first before replacing")
