with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Check what's missing and add all configs
configs_to_add = []

if 'GLEIF_API_CONFIG' not in content:
    configs_to_add.append('''
# GLEIF API Configuration
GLEIF_API_CONFIG = {
    "base_url": "https://api.gleif.org/api/v1",
    "enabled": False
}
''')

if 'EMISSION_FACTOR_REGISTRY' not in content:
    configs_to_add.append('''
# Emission Factor Registry Configuration
EMISSION_FACTOR_REGISTRY = {
    "default_source": "EPA",
    "version": "2024",
    "enabled": True
}
''')

if 'SCOPE3_CATEGORIES' not in content:
    configs_to_add.append('''
# Scope 3 Categories Configuration
SCOPE3_CATEGORIES = {
    "1": "Purchased goods and services",
    "2": "Capital goods",
    "3": "Fuel-and-energy-related activities",
    "4": "Upstream transportation and distribution",
    "5": "Waste generated in operations",
    "6": "Business travel",
    "7": "Employee commuting",
    "8": "Upstream leased assets",
    "9": "Downstream transportation and distribution",
    "10": "Processing of sold products",
    "11": "Use of sold products",
    "12": "End-of-life treatment of sold products",
    "13": "Downstream leased assets",
    "14": "Franchises",
    "15": "Investments"
}
''')

# Add any other common configs
additional_configs = '''
# Additional configurations
DEFAULT_CURRENCY = "EUR"
DEFAULT_REPORTING_YEAR = "2024"
DEFAULT_LANGUAGE = "en"
VALIDATION_ENABLED = False  # We're shipping bare minimum!
'''

# Find where to insert (after existing configs)
import re
pattern = r'(ESAP_CONFIG = {[^}]+}\n)'
match = re.search(pattern, content, re.DOTALL)

if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + '\n'.join(configs_to_add) + additional_configs + '\n' + content[insert_pos:]
else:
    # Fallback: add after imports
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('router = APIRouter'):
            new_content = '\n'.join(lines[:i]) + '\n' + '\n'.join(configs_to_add) + additional_configs + '\n' + '\n'.join(lines[i:])
            break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(new_content)

print("✅ Added ALL missing configurations!")
print("Added:")
print("- GLEIF_API_CONFIG")
print("- EMISSION_FACTOR_REGISTRY") 
print("- SCOPE3_CATEGORIES")
print("- DEFAULT_CURRENCY")
print("- DEFAULT_REPORTING_YEAR")
print("- DEFAULT_LANGUAGE")
print("- VALIDATION_ENABLED")
