#!/usr/bin/env python3
"""Fix the DataQualityScore relationship name"""

def fix_data_quality_relationship():
    with open("app/models/data_quality.py", "r") as f:
        content = f.read()
    
    # Replace quality_scores with data_quality_scores
    content = content.replace(
        'back_populates="quality_scores"',
        'back_populates="data_quality_scores"'
    )
    
    with open("app/models/data_quality.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed DataQualityScore relationship name")

if __name__ == "__main__":
    fix_data_quality_relationship()
