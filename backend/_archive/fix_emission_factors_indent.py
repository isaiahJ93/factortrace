import re

with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    lines = f.readlines()

# Check line 49 (index 48)
if len(lines) > 48:
    print(f"Line 49: '{lines[48]}'")
    print(f"Line 48: '{lines[47]}'")
    print(f"Line 50: '{lines[49] if len(lines) > 49 else 'EOF'}'")
    
    # Fix common indentation issues
    # Make sure the line has consistent indentation
    if lines[48].strip() and not lines[48].startswith(' ' * 4) and not lines[48].startswith('\t'):
        print("Found indentation issue on line 49")
        # Fix it based on context
        lines[48] = '    ' + lines[48].lstrip()
        
        with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
            f.writelines(lines)
        print("Fixed indentation")
    else:
        print("Checking for other issues...")

# Show the specific area
print("\nContent around line 49:")
for i in range(max(0, 45), min(len(lines), 55)):
    print(f"{i+1}: {repr(lines[i])}")

