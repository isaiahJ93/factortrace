import re

# Read the file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Check if we're already storing results
if 'app.state.last_calculation' not in content:
    print("🔧 Adding storage to calculate endpoint...")
    
    # Find the calculate endpoint
    calc_match = re.search(r'(@app\.post\("/api/v1/calculate-with-monte-carlo"\)[\s\S]*?)(return\s+{)', content)
    
    if calc_match:
        before_return = calc_match.group(1)
        return_start = calc_match.group(2)
        
        # Storage code to insert
        storage_code = '''
    # Store results for dashboard
    if hasattr(app, 'state'):
        # Map activity types to scopes
        scope_mapping = {
            "electricity": 2, "natural_gas": 1, "business_travel": 3,
            "stationary_combustion": 1, "mobile_combustion": 1,
            "process_emissions": 1, "fugitive_emissions": 1,
            "purchased_electricity": 2, "purchased_steam": 2,
            "purchased_heating": 2, "purchased_cooling": 2,
            "purchased_goods_services": 3, "capital_goods": 3,
            "fuel_energy_activities": 3, "upstream_transport": 3,
            "waste_generated": 3, "employee_commuting": 3,
            "upstream_leased_assets": 3, "downstream_transport": 3,
            "processing_sold_products": 3, "use_of_sold_products": 3,
            "end_of_life_treatment": 3, "downstream_leased_assets": 3,
            "franchises": 3, "investments": 3
        }
        
        scope_totals = {1: 0, 2: 0, 3: 0}
        for emission in emissions:
            activity = emission.get("activity_type", "")
            scope = scope_mapping.get(activity, 0)
            if scope:
                scope_totals[scope] += emission.get("emissions_value", 0)
        
        app.state.last_calculation = {
            "scope1_total": scope_totals[1],
            "scope2_total": scope_totals[2],
            "scope3_total": scope_totals[3],
            "total_emissions": total_emissions,
            "last_updated": datetime.now().isoformat(),
            "calculation_id": str(uuid.uuid4())
        }
    
    '''
        
        # Find the exact position to insert (before return)
        insert_pos = calc_match.end(1)
        content = content[:insert_pos] + storage_code + content[insert_pos:]
        
        # Write back
        with open('ghg_monte_carlo_api.py', 'w') as f:
            f.write(content)
        
        print("✅ Added storage code to calculate endpoint!")
        print("🔄 Restart the server to apply changes")
    else:
        print("❌ Could not find calculate endpoint")
else:
    print("✅ Already storing calculation results!")
