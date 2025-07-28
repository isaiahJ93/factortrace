#!/usr/bin/env python3
"""Remove markdown code fences from Python files."""
import os
import glob

def clean_file(filepath):
    """Remove markdown fences from a file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return False
        
    changed = False
    # Check first line
    if lines[0].strip() == '```python':
        lines = lines[1:]
        changed = True
    
    # Check last line
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
        changed = True
        
    if changed:
        with open(filepath, 'w') as f:
            f.writelines(lines)
        print(f"✅ Cleaned: {filepath}")
        return True
    return False

# Clean all test files
test_files = glob.glob("xpath31/tests/*.py")
for tf in test_files:
    clean_file(tf)

# Clean all module files
module_files = glob.glob("xpath31/**/*.py", recursive=True)
for mf in module_files:
    clean_file(mf)
