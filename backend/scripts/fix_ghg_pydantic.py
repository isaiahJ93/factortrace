#!/usr/bin/env python3
"""Fix Pydantic v2 compatibility in GHG domain models"""

import re
import os

def fix_ghg_domain():
    file_path = "app/models/ghg_domain.py"
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Creating the file with Pydantic v2 compatible version...")
        # We'll create a corrected version instead
        create_fixed_ghg_domain()
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace root_validator with model_validator
    content = re.sub(
        r'from pydantic import (.*?)root_validator',
        r'from pydantic import \1model_validator',
        content
    )
    
    # Replace @root_validator with @model_validator(mode='after')
    content = re.sub(
        r'@root_validator(\s*\(.*?\))?',
        r"@model_validator(mode='after')",
        content
    )
    
    # Update the validator method signatures
    # From: def validate_method(cls, values):
    # To: def validate_method(self):
    content = re.sub(
        r'def (\w+)\(cls, values\):',
        r'def \1(self):',
        content
    )
    
    # Update references to 'values' dict to 'self'
    # This is more complex and needs careful handling
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'values[' in line and 'def ' not in line:
            # Simple replacement for common patterns
            line = re.sub(r"values\['(\w+)'\]", r"self.\1", line)
            line = re.sub(r'values\.get\(["\'](\w+)["\']\)', r"getattr(self, '\1', None)", line)
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed Pydantic v2 compatibility in {file_path}")

def create_fixed_ghg_domain():
    """Create a fixed version of ghg_domain.py if it doesn't exist"""
    
    # For now, create an empty placeholder
    os.makedirs("app/models", exist_ok=True)
    
    with open("app/models/ghg_domain.py", "w") as f:
        f.write('''"""
GHG Protocol Domain Models
Placeholder - to be replaced with actual implementation
"""

from pydantic import BaseModel

class Organization(BaseModel):
    """Organization model placeholder"""
    pass
''')
    
    print("✅ Created placeholder ghg_domain.py")

if __name__ == "__main__":
    fix_ghg_domain()
