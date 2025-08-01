with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the generate_xbrl_report function
import re
pattern = r'(def generate_xbrl_report.*?)(return\s+)(.*?)(\n(?=\ndef|class|\Z))'

def replacer(match):
    if 'None' in match.group(3) or not match.group(3).strip():
        # If it returns None or nothing, make it return the XML
        return match.group(1) + 'return ET.tostring(html, encoding="unicode", method="xml")' + match.group(4)
    return match.group(0)

# Check if the function ends properly
if 'def generate_xbrl_report' in content:
    # Find the function
    start = content.find('def generate_xbrl_report')
    # Find the next function
    next_func = content.find('\ndef ', start + 1)
    if next_func == -1:
        next_func = content.find('\nclass ', start + 1)
    
    func_content = content[start:next_func] if next_func != -1 else content[start:]
    
    # Check if it has a return statement
    if 'return' not in func_content or 'return None' in func_content:
        print("⚠️  Function doesn't return anything or returns None!")
        # Add return at the end
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def generate_xbrl_report' in line:
                # Find the end of the function
                j = i + 1
                while j < len(lines) and (lines[j].startswith(' ') or not lines[j].strip()):
                    j += 1
                # Insert return before the next function
                lines.insert(j-1, '    return ET.tostring(html, encoding="unicode", method="xml")')
                break
        
        content = '\n'.join(lines)
        with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
            f.write(content)
        print("✅ Added return statement")

