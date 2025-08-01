# fix_efrag_uri.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good place to add the constant (after imports, before first function)
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('def ') or line.startswith('class '):
        # Insert before the first function/class
        insert_pos = i
        break

if insert_pos is None:
    # Fallback: insert after ESAP_CONFIG
    for i, line in enumerate(lines):
        if 'ESAP_CONFIG = {' in line:
            # Find the end of ESAP_CONFIG
            j = i
            brace_count = 0
            while j < len(lines):
                brace_count += lines[j].count('{') - lines[j].count('}')
                if brace_count == 0 and j > i:
                    insert_pos = j + 1
                    break
                j += 1
            break

# Add the constant
if insert_pos:
    lines.insert(insert_pos, '\n# EFRAG XBRL Base URI\n')
    lines.insert(insert_pos + 1, 'EFRAG_BASE_URI = "https://www.efrag.org/xbrl"\n\n')

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added EFRAG_BASE_URI constant")