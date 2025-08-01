import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the add_xbrl_contexts function and add missing contexts
old_function = '''def add_xbrl_contexts(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add XBRL contexts for reporting periods - EFRAG compliant"""
    # Current reporting period context
    context = ET.SubElement(parent, 'xbrli:context', {'id': 'current-period'})'''

new_function = '''def add_xbrl_contexts(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add XBRL contexts for reporting periods - EFRAG compliant"""
    
    # Current instant context (for point-in-time data)
    context_instant = ET.SubElement(parent, 'xbrli:context', {'id': 'current-instant'})
    entity_instant = ET.SubElement(context_instant, 'xbrli:entity')
    identifier_instant = ET.SubElement(entity_instant, 'xbrli:identifier', {
        'scheme': 'http://www.lei-worldwide.com'
    })
    identifier_instant.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period_instant = ET.SubElement(context_instant, 'xbrli:period')
    instant = ET.SubElement(period_instant, 'xbrli:instant')
    instant.text = f"{data.get('reporting_period', '2025')}-12-31"
    
    # Current reporting period context
    context = ET.SubElement(parent, 'xbrli:context', {'id': 'current-period'})'''

content = content.replace(old_function, new_function)

# Add c-current and c-base contexts after the target contexts
insertion_point = "instant_target.text = f\"{target_year}-12-31\""
insertion_text = '''instant_target.text = f"{target_year}-12-31"
    
    # c-current context (used by enhanced sections)
    context_c_current = ET.SubElement(parent, 'xbrli:context', {'id': 'c-current'})
    entity_c_current = ET.SubElement(context_c_current, 'xbrli:entity')
    identifier_c_current = ET.SubElement(entity_c_current, 'xbrli:identifier', {
        'scheme': 'http://www.lei-worldwide.com'
    })
    identifier_c_current.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period_c_current = ET.SubElement(context_c_current, 'xbrli:period')
    instant_c_current = ET.SubElement(period_c_current, 'xbrli:instant')
    instant_c_current.text = f"{data.get('reporting_period', '2025')}-12-31"
    
    # c-base context (for base year)
    context_c_base = ET.SubElement(parent, 'xbrli:context', {'id': 'c-base'})
    entity_c_base = ET.SubElement(context_c_base, 'xbrli:entity')
    identifier_c_base = ET.SubElement(entity_c_base, 'xbrli:identifier', {
        'scheme': 'http://www.lei-worldwide.com'
    })
    identifier_c_base.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period_c_base = ET.SubElement(context_c_base, 'xbrli:period')
    instant_c_base = ET.SubElement(period_c_base, 'xbrli:instant')
    base_year = data.get('targets', {}).get('base_year', data.get('reporting_period', '2025'))
    instant_c_base.text = f"{base_year}-12-31"'''

content = content.replace(insertion_point, insertion_text)

# Add missing units
units_insertion = '''    measure_tco2e.text = 'esrs:metricTonnesCO2e'
    
    # Additional tCO2e unit (u-tCO2e)
    unit_u_tco2e = ET.SubElement(parent, 'xbrli:unit', {'id': 'u-tCO2e'})
    measure_u_tco2e = ET.SubElement(unit_u_tco2e, 'xbrli:measure')
    measure_u_tco2e.text = 'esrs:metricTonnesCO2e'
    
    # Tonnes unit
    unit_tonnes = ET.SubElement(parent, 'xbrli:unit', {'id': 'tonnes'})
    measure_tonnes = ET.SubElement(unit_tonnes, 'xbrli:measure')
    measure_tonnes.text = 'esrs:tonnes' '''

content = content.replace(
    "measure_tco2e.text = 'esrs:metricTonnesCO2e'",
    units_insertion
)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added missing XBRL contexts: current-instant, c-current, c-base")
print("✅ Added missing units: u-tCO2e, tonnes")
