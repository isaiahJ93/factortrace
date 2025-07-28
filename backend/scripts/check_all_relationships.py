#!/usr/bin/env python3
"""Check all model relationships"""

import os
import re

def check_relationships():
    models_dir = "app/models"
    relationships = {}
    
    # Find all back_populates relationships
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Find all back_populates
            matches = re.findall(r'relationship\("([^"]+)".*back_populates="([^"]+)"', content)
            for target_model, backref_name in matches:
                if target_model not in relationships:
                    relationships[target_model] = {}
                relationships[target_model][backref_name] = filename
    
    # Check if all relationships exist
    print("Checking relationships:")
    for model, backrefs in relationships.items():
        print(f"\n{model}:")
        for backref, source_file in backrefs.items():
            print(f"  - expects '{backref}' relationship (from {source_file})")
    
    # Now check if these relationships exist
    print("\n\nVerifying relationships exist:")
    issues = []
    for model_name, expected_backrefs in relationships.items():
        # Try to find the model file
        model_file = None
        for filename in os.listdir(models_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(models_dir, filename)
                with open(filepath, 'r') as f:
                    if f'class {model_name}' in f.read():
                        model_file = filepath
                        break
        
        if model_file:
            with open(model_file, 'r') as f:
                content = f.read()
            
            for backref in expected_backrefs:
                if f'{backref} = relationship(' not in content:
                    issues.append(f"❌ {model_name} is missing '{backref}' relationship")
                else:
                    print(f"✅ {model_name} has '{backref}' relationship")
        else:
            issues.append(f"⚠️  Could not find model file for {model_name}")
    
    if issues:
        print("\n\nIssues found:")
        for issue in issues:
            print(issue)
    else:
        print("\n\n✅ All relationships are properly configured!")

if __name__ == "__main__":
    check_relationships()
