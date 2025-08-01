with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where to add it (after GLEIF_API_CONFIG or ESAP_CONFIG)
insert_pos = None
for i, line in enumerate(lines):
    if 'GLEIF_API_CONFIG = {' in line or 'ESAP_CONFIG = {' in line:
        # Find the end of this config
        j = i
        brace_count = 0
        while j < len(lines):
            brace_count += lines[j].count('{') - lines[j].count('}')
            if brace_count == 0 and j > i:
                insert_pos = j + 2
                break
            j += 1
        if insert_pos:
            break

if insert_pos:
    lines.insert(insert_pos, '\n# Emission Factor Registry Configuration\n')
    lines.insert(insert_pos + 1, 'EMISSION_FACTOR_REGISTRY = {\n')
    lines.insert(insert_pos + 2, '    "default_source": "EPA",\n')
    lines.insert(insert_pos + 3, '    "version": "2024",\n')
    lines.insert(insert_pos + 4, '    "enabled": True\n')
    lines.insert(insert_pos + 5, '}\n\n')

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added EMISSION_FACTOR_REGISTRY")
