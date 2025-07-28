#!/bin/bash

echo "🚀 Elite Monte Carlo Dashboard Integration Script"
echo "================================================"

# Step 1: Backup the Monte Carlo API
echo "📦 Creating backup..."
cp ghg_monte_carlo_api.py ghg_monte_carlo_api.py.backup_$(date +%Y%m%d_%H%M%S)

# Step 2: Create a Python script to update the Monte Carlo API
cat > update_monte_carlo_api.py << 'PYTHON_EOF'
import re
import sys

print("🔍 Reading Monte Carlo API file...")
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Check if summary endpoint already exists
if "/api/v1/emissions/summary" in content:
    print("✅ Summary endpoint already exists!")
else:
    print("📝 Adding summary endpoint...")
    
    # Find where to insert the summary endpoint (after the calculate endpoint)
    calculate_pattern = r'(@app\.post\("/api/v1/calculate-with-monte-carlo"\)[\s\S]*?)(\n@app\.|$)'
    
    # Import necessary modules if not already imported
    if "from datetime import datetime" not in content:
        content = "from datetime import datetime\n" + content
    if "import uuid" not in content:
        content = "import uuid\n" + content
    
    # Add summary endpoint
    summary_endpoint = '''

@app.get("/api/v1/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary for dashboard"""
    # Return the last calculation if available
    if hasattr(app, 'state') and hasattr(app.state, 'last_calculation'):
        calc = app.state.last_calculation
        return {
            "scope1_total": calc.get("scope1_total", 0),
            "scope2_total": calc.get("scope2_total", 0),
            "scope3_total": calc.get("scope3_total", 0),
            "total_emissions": calc.get("total_emissions", 0),
            "last_updated": calc.get("timestamp", datetime.now().isoformat()),
            "calculation_id": calc.get("calculation_id", str(uuid.uuid4()))
        }
    
    return {
        "scope1_total": 0,
        "scope2_total": 0,
        "scope3_total": 0,
        "total_emissions": 0,
        "last_updated": None,
        "calculation_id": None
    }
'''
    
    # Insert the summary endpoint
    def replacer(match):
        return match.group(1) + summary_endpoint + '\n' + match.group(2)
    
    content = re.sub(calculate_pattern, replacer, content)

# Update the calculate endpoint to store results
print("🔧 Updating calculate endpoint to store results...")

# Find the calculate-with-monte-carlo function
calc_function_pattern = r'(@app\.post\("/api/v1/calculate-with-monte-carlo"\).*?async def.*?\):)([\s\S]*?)(return[\s\S]*?})'

def update_calculate_function(match):
    function_start = match.group(1)
    function_body = match.group(2)
    return_statement = match.group(3)
    
    # Check if we already store results
    if "app.state.last_calculation" in function_body:
        print("✅ Already storing calculation results!")
        return match.group(0)
    
    # Add initialization if not present
    if "if not hasattr(app, 'state'):" not in function_body:
        init_code = '''
    # Initialize app state if needed
    if not hasattr(app, 'state'):
        from types import SimpleNamespace
        app.state = SimpleNamespace()
'''
        function_body = init_code + function_body
    
    # Find where to insert the storage code (before the return statement)
    storage_code = '''
    
    # Store results for dashboard summary
    scope1_total = sum(e.get("emissions_value", 0) for e in emissions if activities_dict.get(e["activity_type"], {}).get("scope", 0) == 1)
    scope2_total = sum(e.get("emissions_value", 0) for e in emissions if activities_dict.get(e["activity_type"], {}).get("scope", 0) == 2)
    scope3_total = sum(e.get("emissions_value", 0) for e in emissions if activities_dict.get(e["activity_type"], {}).get("scope", 0) == 3)
    
    app.state.last_calculation = {
        "scope1_total": scope1_total,
        "scope2_total": scope2_total,
        "scope3_total": scope3_total,
        "total_emissions": total_emissions,
        "timestamp": datetime.now().isoformat(),
        "calculation_id": str(uuid.uuid4())
    }
    
'''
    
    return function_start + function_body + storage_code + return_statement

content = re.sub(calc_function_pattern, update_calculate_function, content, flags=re.DOTALL)

# Add activity type to scope mapping if not present
if "activities_dict" not in content:
    print("📝 Adding activity type to scope mapping...")
    activities_mapping = '''
# Activity type to scope mapping
activities_dict = {
    # Scope 1
    "stationary_combustion": {"scope": 1},
    "mobile_combustion": {"scope": 1},
    "process_emissions": {"scope": 1},
    "fugitive_emissions": {"scope": 1},
    
    # Scope 2
    "purchased_electricity": {"scope": 2},
    "electricity": {"scope": 2},  # Alias
    "purchased_steam": {"scope": 2},
    "purchased_heating": {"scope": 2},
    "purchased_cooling": {"scope": 2},
    
    # Scope 3
    "purchased_goods_services": {"scope": 3},
    "capital_goods": {"scope": 3},
    "fuel_energy_activities": {"scope": 3},
    "upstream_transport": {"scope": 3},
    "waste_generated": {"scope": 3},
    "business_travel": {"scope": 3},
    "employee_commuting": {"scope": 3},
    "upstream_leased_assets": {"scope": 3},
    "downstream_transport": {"scope": 3},
    "processing_sold_products": {"scope": 3},
    "use_of_sold_products": {"scope": 3},
    "end_of_life_treatment": {"scope": 3},
    "downstream_leased_assets": {"scope": 3},
    "franchises": {"scope": 3},
    "investments": {"scope": 3},
    
    # Legacy mappings
    "natural_gas": {"scope": 1},
}

'''
    # Add after imports
    import_end = content.find('\n\n', content.rfind('import '))
    if import_end > 0:
        content = content[:import_end] + '\n' + activities_mapping + content[import_end:]

# Write the updated content
print("💾 Writing updated file...")
with open('ghg_monte_carlo_api.py', 'w') as f:
    f.write(content)

print("✅ Monte Carlo API updated successfully!")
PYTHON_EOF

# Step 3: Run the Python updater
echo ""
echo "🔧 Updating Monte Carlo API..."
python3 update_monte_carlo_api.py

# Step 4: Clean up
rm update_monte_carlo_api.py

# Step 5: Restart instructions
echo ""
echo "✅ Integration complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart the backend:"
echo "   cd backend"
echo "   python ghg_monte_carlo_api.py"
echo ""
echo "2. The dashboard will now:"
echo "   - Show calculated emissions after using the calculator"
echo "   - Refresh automatically when calculations complete"
echo "   - Display scope breakdowns correctly"
echo ""
echo "3. Test flow:"
echo "   - Go to http://localhost:3000/calculator"
echo "   - Enter some values and calculate"
echo "   - Return to dashboard - it should show your results!"
echo ""
echo "🚀 Your GHG calculator is now fully integrated!"
