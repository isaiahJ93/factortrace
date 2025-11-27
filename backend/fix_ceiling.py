import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add import at the top
if 'import math' not in content:
    content = re.sub(r'(import.*?\n)', r'\1import math\n', content, count=1)

# Replace round with ceiling logic
replacements = [
    (r"data\['scope3_detailed'\]\['category_1'\]\['emissions_tco2e'\] = round\(paper_emissions \+ plastic_emissions\)",
     "emissions_val = paper_emissions + plastic_emissions\n                data['scope3_detailed']['category_1']['emissions_tco2e'] = math.ceil(emissions_val) if 0 < emissions_val < 1 else round(emissions_val)"),
    
    (r"data\['scope3_detailed'\]\['category_4'\]\['emissions_tco2e'\] = round\(road_emissions \+ rail_emissions\)",
     "emissions_val = road_emissions + rail_emissions\n                data['scope3_detailed']['category_4']['emissions_tco2e'] = math.ceil(emissions_val) if 0 < emissions_val < 1 else round(emissions_val)"),
    
    (r"data\['scope3_detailed'\]\['category_6'\]\['emissions_tco2e'\] = round\(domestic_emissions \+ longhaul_emissions\)",
     "emissions_val = domestic_emissions + longhaul_emissions\n                data['scope3_detailed']['category_6']['emissions_tco2e'] = math.ceil(emissions_val) if 0 < emissions_val < 1 else round(emissions_val)")
]

for old, new in replacements:
    content = re.sub(old, new, content)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed to use ceiling for small emissions (0-1 tCO₂e)")
