#!/usr/bin/env python3
"""Fix model relationship issues"""

import os
import re

def fix_emission_relationships():
    """Fix the quality_scores relationship issue"""
    
    # Check data_quality.py
    data_quality_file = "app/models/data_quality.py"
    if os.path.exists(data_quality_file):
        with open(data_quality_file, 'r') as f:
            content = f.read()
        
        # Fix the relationship name
        # Change back_populates="quality_scores" to back_populates="data_quality_scores"
        content = re.sub(
            r'back_populates="quality_scores"',
            'back_populates="data_quality_scores"',
            content
        )
        
        with open(data_quality_file, 'w') as f:
            f.write(content)
        print(f"✅ Fixed relationships in {data_quality_file}")
    
    # Check emission.py
    emission_file = "app/models/emission.py"
    if os.path.exists(emission_file):
        with open(emission_file, 'r') as f:
            content = f.read()
        
        # Ensure the relationship exists with correct name
        if "data_quality_scores" not in content and "relationship" in content:
            # Add the relationship if missing
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "class Emission" in line and "Base" in line:
                    # Find where to add the relationship
                    for j in range(i, len(lines)):
                        if "# Relationships" in lines[j] or "relationship(" in lines[j]:
                            # Add after other relationships
                            lines.insert(j + 1, '    data_quality_scores = relationship("DataQualityScore", back_populates="emission")')
                            break
            content = '\n'.join(lines)
        
        with open(emission_file, 'w') as f:
            f.write(content)
        print(f"✅ Fixed relationships in {emission_file}")

if __name__ == "__main__":
    fix_emission_relationships()
