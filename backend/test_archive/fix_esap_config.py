# fix_esap_config.py
import fileinput
import sys

# Read the file and fix the structure
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find and fix the specific issue
lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Look for the problematic pattern: closing brace followed by xmlns entries
    if "'pdf': '.pdf'" in line:
        fixed_lines.append(line)
        i += 1
        # Check if next line has a closing brace
        if i < len(lines) and lines[i].strip() == '}':
            # Check if line after that starts with whitespace and quotes (orphaned entry)
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("'"):
                # Fix: add comma and 'namespaces' key
                fixed_lines.append("    },")  # Close file_extensions with comma
                fixed_lines.append("    'namespaces': {")  # Add namespaces section
                i += 1  # Skip the standalone }
            else:
                fixed_lines.append(lines[i])
                i += 1
        else:
            i += 1
    else:
        fixed_lines.append(line)
        i += 1

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("✅ Fixed ESAP_CONFIG structure!")