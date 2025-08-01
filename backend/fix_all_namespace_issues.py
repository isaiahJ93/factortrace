with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix 1: Add namespaces = get_namespace_map() at the start of double materiality function
old_double_mat = '''def create_double_materiality_section(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create double materiality assessment section"""
    section = ET.SubElement(body, 'section', attrib={'''

new_double_mat = '''def create_double_materiality_section(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create double materiality assessment section"""
    namespaces = get_namespace_map()
    
    section = ET.SubElement(body, 'section', attrib={'''

content = content.replace(old_double_mat, new_double_mat)

# Fix 2: In the GHG intensity section, we need to add namespaces there too
# Find the create_e1_6_ghg_emissions function
lines = content.split('\n')
in_e16_function = False
for i, line in enumerate(lines):
    if 'def create_e1_6_ghg_emissions' in line:
        in_e16_function = True
    elif in_e16_function and 'def ' in line and 'create_e1_6' not in line:
        in_e16_function = False
    
    # If we find the intensity section we added
    if in_e16_function and '# Add GHG intensity metrics' in line:
        # Check if namespaces is already defined in this function
        # If not, add it after the comment
        func_start = i
        while func_start > 0 and 'def create_e1_6_ghg_emissions' not in lines[func_start]:
            func_start -= 1
        
        # Check if namespaces is defined between function start and our code
        has_namespaces = False
        for j in range(func_start, i):
            if 'namespaces = get_namespace_map()' in lines[j]:
                has_namespaces = True
                break
        
        if not has_namespaces:
            # Add it right after our comment
            indent = len(lines[i]) - len(lines[i].lstrip())
            lines.insert(i + 1, ' ' * indent + 'namespaces = get_namespace_map()')

content = '\n'.join(lines)

# Fix 3: Fix the unit creation - need namespaces there too
# Find where we create unit7 (our new intensity unit)
if 'unit7 = ET.SubElement(contexts_div,' in content:
    # We need to ensure namespaces is available in that context too
    # This is in the section where we add contexts at the end
    # Let's check if that section has namespaces defined
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '# Additional unit for intensity metrics' in line:
            # Look backwards to see if namespaces is defined
            has_ns = False
            for j in range(max(0, i-50), i):
                if 'namespaces = get_namespace_map()' in lines[j]:
                    has_ns = True
                    break
            
            if not has_ns:
                # Add it before the unit creation
                indent = len(lines[i]) - len(lines[i].lstrip())
                lines.insert(i, ' ' * indent + 'namespaces = get_namespace_map()')
                lines.insert(i + 1, '')

content = '\n'.join(lines)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed all namespace issues by adding get_namespace_map() calls")
