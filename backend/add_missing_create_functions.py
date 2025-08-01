with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all create_* function calls in generate_xbrl_report
import re
calls = re.findall(r'create_([a-zA-Z0-9_]+)\(body, data\)', content)
print(f"Found create_* function calls: {calls}")

# Check which ones are missing
missing = []
for func_name in calls:
    if f'def create_{func_name}' not in content:
        missing.append(func_name)

print(f"Missing functions: {missing}")

# Add stub functions for missing ones
if missing:
    # Find a good place to insert (before generate_xbrl_report)
    insert_pos = content.find('def generate_xbrl_report')
    
    stubs = '\n'.join([f'''
def create_{func_name}(body: ET.Element, data: Dict[str, Any]) -> None:
    """Stub for {func_name.replace('_', ' ').title()}"""
    namespaces = get_namespace_map()
    section = ET.SubElement(body, 'section', attrib={{'class': '{func_name.replace("_", "-")}'}})
    p = ET.SubElement(section, 'p')
    p.text = f"{func_name.replace('_', ' ').title()} - To be implemented"
''' for func_name in missing])
    
    content = content[:insert_pos] + stubs + '\n\n' + content[insert_pos:]
    
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print(f"✅ Added {len(missing)} stub functions")
