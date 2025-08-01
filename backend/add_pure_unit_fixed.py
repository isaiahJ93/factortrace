with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we add units and add 'pure' if not already there
for i, line in enumerate(lines):
    if "measure7_den.text = 'esrs:millionEUR'" in line or "unit7" in line:
        # Check if 'pure' unit already exists nearby
        has_pure = False
        for j in range(max(0, i-20), min(i + 20, len(lines))):
            if "'id': 'pure'" in lines[j] or '"pure"' in lines[j]:
                has_pure = True
                break
        
        if not has_pure:
            indent = len(line) - len(line.lstrip())
            spaces = ' ' * indent
            
            pure_unit = f'''
{spaces}
{spaces}# Pure unit for ratios and scores
{spaces}namespaces = get_namespace_map()
{spaces}unit8 = ET.SubElement(contexts_div, namespaces["xbrli"] + 'unit', attrib={{'id': 'pure'}})
{spaces}measure8 = ET.SubElement(unit8, namespaces["xbrli"] + 'measure')
{spaces}measure8.text = 'xbrli:pure'
'''
            lines.insert(i + 1, pure_unit)
            print(f"Added 'pure' unit at line {i+1}")
        else:
            print("'pure' unit already exists")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Finished checking/adding 'pure' unit!")
