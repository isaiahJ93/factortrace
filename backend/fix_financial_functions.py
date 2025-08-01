# fix_financial_functions.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good insertion point - after the extract_ghg_breakdown function
insert_line = None
for i, line in enumerate(lines):
    if 'def extract_ghg_breakdown' in line:
        # Find the end of this function (next def or class)
        j = i + 1
        while j < len(lines) and not (lines[j].startswith('def ') or lines[j].startswith('class ')):
            j += 1
        insert_line = j
        break

if insert_line is None:
    # Fallback: insert before first usage at line 2194
    for i, line in enumerate(lines):
        if 'fe_data = extract_financial_effects_data(data)' in line:
            insert_line = i
            break

# Add the missing functions
new_functions = '''
def extract_financial_effects_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract financial effects data for ESRS E1 reporting"""
    financial_effects = data.get('financial_effects', {})
    
    return {
        'climate_related_opportunities': financial_effects.get('opportunities', {}),
        'climate_related_risks': financial_effects.get('risks', {}),
        'transition_costs': financial_effects.get('transition_costs', 0),
        'physical_damage_costs': financial_effects.get('physical_damage_costs', 0),
        'opportunity_revenue': financial_effects.get('opportunity_revenue', 0),
        'total_opportunity_value': financial_effects.get('total_opportunity_value', 0),
        'total_risk_value': financial_effects.get('total_risk_value', 0),
        'net_financial_impact': financial_effects.get('net_impact', 0),
        'time_horizon': financial_effects.get('time_horizon', 'medium-term')
    }

def extract_financial_effects_data_enhanced(data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced extraction of financial effects data with additional metrics"""
    base_data = extract_financial_effects_data(data)
    financial_effects = data.get('financial_effects', {})
    
    # Add enhanced metrics
    base_data.update({
        'carbon_pricing_impact': financial_effects.get('carbon_pricing_impact', 0),
        'stranded_assets_value': financial_effects.get('stranded_assets_value', 0),
        'green_revenue_percentage': financial_effects.get('green_revenue_percentage', 0),
        'climate_adaptation_costs': financial_effects.get('climate_adaptation_costs', 0),
        'scenario_analysis': financial_effects.get('scenario_analysis', {}),
        'financial_resilience_score': financial_effects.get('resilience_score', 0)
    })
    
    return base_data

'''

if insert_line:
    lines.insert(insert_line, new_functions)
    
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Added missing financial functions at line {insert_line}")