import re

# Read the fixed file
with open('./app/api/v1/endpoints/esrs_e1_full_fixed.py', 'r') as f:
    content = f.read()

print("=== FIXING PERIOD TYPES ===")

# Find and replace instant periods with duration periods
replacements = []

# Pattern 1: Fix the period creation blocks
instant_blocks = [
    (
        "period_elem_current = ET.SubElement(context_current, 'xbrli:period')\n    instant_current = ET.SubElement(period_elem_current, 'xbrli:instant')\n    instant_current.text = f'{current_year}-12-31'",
        "period_elem_current = ET.SubElement(context_current, 'xbrli:period')\n    start_date_current = ET.SubElement(period_elem_current, 'xbrli:startDate')\n    start_date_current.text = f'{current_year}-01-01'\n    end_date_current = ET.SubElement(period_elem_current, 'xbrli:endDate')\n    end_date_current.text = f'{current_year}-12-31'"
    ),
    (
        "period_elem_previous = ET.SubElement(context_previous, 'xbrli:period')\n    instant_previous = ET.SubElement(period_elem_previous, 'xbrli:instant')\n    instant_previous.text = f'{previous_year}-12-31'",
        "period_elem_previous = ET.SubElement(context_previous, 'xbrli:period')\n    start_date_previous = ET.SubElement(period_elem_previous, 'xbrli:startDate')\n    start_date_previous.text = f'{previous_year}-01-01'\n    end_date_previous = ET.SubElement(period_elem_previous, 'xbrli:endDate')\n    end_date_previous.text = f'{previous_year}-12-31'"
    ),
    (
        "period_elem_period = ET.SubElement(context_period, 'xbrli:period')\n    instant_period = ET.SubElement(period_elem_period, 'xbrli:instant')\n    instant_period.text = f'{current_year}-12-31'",
        "period_elem_period = ET.SubElement(context_period, 'xbrli:period')\n    start_date_period = ET.SubElement(period_elem_period, 'xbrli:startDate')\n    start_date_period.text = f'{current_year}-01-01'\n    end_date_period = ET.SubElement(period_elem_period, 'xbrli:endDate')\n    end_date_period.text = f'{current_year}-12-31'"
    ),
]

# Apply replacements
for old, new in instant_blocks:
    if old in content:
        content = content.replace(old, new)
        replacements.append("instant → duration period")

# Pattern 2: Fix any remaining instant references
# Look for patterns like: instant = ET.SubElement(period_elem, 'xbrli:instant')
instant_pattern = r"instant = ET\.SubElement\(period_elem, 'xbrli:instant'\)\s*\n\s*instant\.text = f?['\"].*?['\"]"
def replace_instant_with_duration(match):
    # Extract the year pattern from the instant text
    return """start_date = ET.SubElement(period_elem, 'xbrli:startDate')
        start_date.text = f'{current_year}-01-01'
        end_date = ET.SubElement(period_elem, 'xbrli:endDate')
        end_date.text = f'{current_year}-12-31'"""

# Apply regex replacement
content = re.sub(instant_pattern, replace_instant_with_duration, content)

# Pattern 3: Fix loop contexts
loop_pattern = r"period_elem = ET\.SubElement\(ctx, 'xbrli:period'\)\s*\n\s*instant = ET\.SubElement\(period_elem, 'xbrli:instant'\)\s*\n\s*instant\.text = f'{current_year}-12-31'"
loop_replacement = """period_elem = ET.SubElement(ctx, 'xbrli:period')
        start_date = ET.SubElement(period_elem, 'xbrli:startDate')
        start_date.text = f'{current_year}-01-01'
        end_date = ET.SubElement(period_elem, 'xbrli:endDate')
        end_date.text = f'{current_year}-12-31'"""

if loop_pattern in content:
    content = re.sub(loop_pattern, loop_replacement, content)
    replacements.append("loop context periods")

# Also fix any standalone instant periods
standalone_pattern = r"period_instant = ET\.SubElement\(([^,]+), 'xbrli:period'\)\s*\n\s*instant = ET\.SubElement\(period_instant, 'xbrli:instant'\)\s*\n\s*instant\.text = f?['\"]([^'\"]+)['\"]"
def fix_standalone(match):
    context_var = match.group(1)
    return f"""period_instant = ET.SubElement({context_var}, 'xbrli:period')
    start_date = ET.SubElement(period_instant, 'xbrli:startDate')
    start_date.text = f'{{current_year}}-01-01'
    end_date = ET.SubElement(period_instant, 'xbrli:endDate')
    end_date.text = f'{{current_year}}-12-31'"""

content = re.sub(standalone_pattern, fix_standalone, content)

print(f"✅ Fixed {len(replacements)} period declarations")

# Write the final fixed file
with open('./app/api/v1/endpoints/esrs_e1_full_final.py', 'w') as f:
    f.write(content)

print("✅ Created esrs_e1_full_final.py with all fixes")
print("\nNow replace the original file:")
print("cp ./app/api/v1/endpoints/esrs_e1_full_final.py ./app/api/v1/endpoints/esrs_e1_full.py")
