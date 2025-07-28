import re

# Read the restored file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# 1. Add imports
if 'from datetime import datetime' not in content:
    content = content.replace('from datetime import date', 'from datetime import date, datetime')
if 'import uuid' not in content:
    content = content.replace('import uvicorn', 'import uuid\nimport uvicorn')
if 'from types import SimpleNamespace' not in content:
    content = content.replace('import uvicorn', 'from types import SimpleNamespace\nimport uvicorn')

# 2. Add state initialization after FastAPI creation
app_pattern = r'(app = FastAPI\([^)]*\))'
app_match = re.search(app_pattern, content, re.DOTALL)
if app_match and 'app.state' not in content:
    insert_pos = app_match.end()
    state_init = '\n\n# Initialize state\napp.state = SimpleNamespace()\napp.state.last_calculation = None\n'
    content = content[:insert_pos] + state_init + content[insert_pos:]

# 3. Add summary endpoint before main
main_pos = content.find('if __name__ == "__main__":')
if main_pos > 0 and '/api/v1/emissions/summary' not in content:
    summary_endpoint = '''
@app.get("/api/v1/emissions/summary")
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
    content = content[:main_pos] + summary_endpoint + content[main_pos:]

# 4. Add storage to calculate endpoint
calc_pattern = r'(@app\.post\("/api/v1/calculate-with-monte-carlo"\).*?)(return\s+{[^}]+?"message"[^}]+?})'
calc_match = re.search(calc_pattern, content, re.DOTALL)

if calc_match and 'app.state.last_calculation' not in content:
    before_return = calc_match.group(1)
    return_statement = calc_match.group(2)
    
    storage_code = '''
    # Store results for dashboard
    if hasattr(app, 'state'):
        # Simple scope mapping
        scope1_total = sum(item["emissions_value"] for item in breakdown 
                          if item["activity_type"].lower() in ["natural_gas", "stationary_combustion"])
        scope2_total = sum(item["emissions_value"] for item in breakdown 
                          if item["activity_type"].lower() in ["electricity", "purchased_electricity"])
        scope3_total = sum(item["emissions_value"] for item in breakdown 
                          if item["activity_type"].lower() in ["business_travel", "waste_landfill"])
        
        app.state.last_calculation = {
            "scope1_total": round(scope1_total, 2),
            "scope2_total": round(scope2_total, 2),
            "scope3_total": round(scope3_total, 2),
            "total_emissions": round(total_emissions, 2),
            "last_updated": datetime.now().isoformat(),
            "calculation_id": str(uuid.uuid4())
        }
    
    '''
    
    new_content = before_return + storage_code + return_statement
    content = re.sub(calc_pattern, new_content, content, flags=re.DOTALL)

# Write the final integrated file
with open('ghg_monte_carlo_api_final.py', 'w') as f:
    f.write(content)

print("✅ Created ghg_monte_carlo_api_final.py")
print("🔍 Test it first:")
print("   python3 -m py_compile ghg_monte_carlo_api_final.py")
