with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the section with wrong indentation
# The pattern has extra spaces after 'tr = ET.SubElement(tbody, 'tr')'
wrong_pattern = '''            tr = ET.SubElement(tbody, 'tr')
                
                # Category number
                td = ET.SubElement(tr, 'td')'''

correct_pattern = '''            tr = ET.SubElement(tbody, 'tr')
            
            # Category number
            td = ET.SubElement(tr, 'td')'''

if wrong_pattern in content:
    # Fix all the indentation in this block by removing 4 spaces
    lines = content.split('\n')
    fixed_lines = []
    fixing = False
    
    for i, line in enumerate(lines):
        if i >= 794 and i <= 850:  # Around the problem area
            # Remove 4 spaces from lines that have extra indentation
            if line.startswith('                ') and not line.startswith('                    '):
                line = line[4:]  # Remove 4 spaces
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed indentation in scope3 section")
