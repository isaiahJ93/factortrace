# fix_current_period.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Update extract_financial_effects_data to include current_period_effects
old_return = '''return {
        'climate_related_opportunities': financial_effects.get('opportunities', {}),
        'climate_related_risks': financial_effects.get('risks', {}),
        'transition_costs': financial_effects.get('transition_costs', 0),
        'physical_damage_costs': financial_effects.get('physical_damage_costs', 0),
        'opportunity_revenue': financial_effects.get('opportunity_revenue', 0),
        'total_opportunity_value': financial_effects.get('total_opportunity_value', 0),
        'total_risk_value': financial_effects.get('total_risk_value', 0),
        'net_financial_impact': financial_effects.get('net_impact', 0),
        'time_horizon': financial_effects.get('time_horizon', 'medium-term')
    }'''

new_return = '''return {
        'climate_related_opportunities': financial_effects.get('opportunities', {}),
        'climate_related_risks': financial_effects.get('risks', {}),
        'transition_costs': financial_effects.get('transition_costs', 0),
        'physical_damage_costs': financial_effects.get('physical_damage_costs', 0),
        'opportunity_revenue': financial_effects.get('opportunity_revenue', 0),
        'total_opportunity_value': financial_effects.get('total_opportunity_value', 0),
        'total_risk_value': financial_effects.get('total_risk_value', 0),
        'net_financial_impact': financial_effects.get('net_impact', 0),
        'time_horizon': financial_effects.get('time_horizon', 'medium-term'),
        'current_period_effects': financial_effects.get('current_period_effects', {
            'revenue_impact': 0,
            'cost_impact': 0,
            'asset_impact': 0,
            'liability_impact': 0
        }),
        'future_period_effects': financial_effects.get('future_period_effects', {})
    }'''

content = content.replace(old_return, new_return)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added current_period_effects to financial data")