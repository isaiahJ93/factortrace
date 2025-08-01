with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where to add it (after ESAP_CONFIG)
for i, line in enumerate(lines):
    if 'ESAP_CONFIG = {' in line:
        # Find the end of ESAP_CONFIG
        j = i
        brace_count = 0
        while j < len(lines):
            brace_count += lines[j].count('{') - lines[j].count('}')
            if brace_count == 0 and j > i:
                # Add GLEIF_API_CONFIG after ESAP_CONFIG
                lines.insert(j+2, '\n# GLEIF API Configuration\n')
                lines.insert(j+3, 'GLEIF_API_CONFIG = {\n')
                lines.insert(j+4, '    "base_url": "https://api.gleif.org/api/v1",\n')
                lines.insert(j+5, '    "enabled": False  # Set to True if you have GLEIF API access\n')
                lines.insert(j+6, '}\n\n')
                break
            j += 1
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added GLEIF_API_CONFIG")
