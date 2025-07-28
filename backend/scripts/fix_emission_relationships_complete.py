#!/usr/bin/env python3
"""Fix all relationships in Emission model"""

def fix_emission_relationships():
    with open("app/models/emission.py", "r") as f:
        content = f.read()
    
    # Check which relationships already exist (with any formatting)
    has_user = "user = relationship" in content or "user=relationship" in content
    has_evidence = "evidence_documents = relationship" in content or "evidence_documents=relationship" in content
    has_quality = "data_quality_scores = relationship" in content or "data_quality_scores=relationship" in content
    
    print(f"Current status:")
    print(f"  - user relationship: {'exists' if has_user else 'missing'}")
    print(f"  - evidence_documents relationship: {'exists' if has_evidence else 'missing'}")
    print(f"  - data_quality_scores relationship: {'exists' if has_quality else 'missing'}")
    
    # Find the relationships section
    lines = content.split('\n')
    relationships_start = None
    
    for i, line in enumerate(lines):
        if "# Relationships" in line:
            relationships_start = i
            break
    
    if relationships_start is None:
        print("❌ Could not find relationships section")
        return
    
    # Add missing relationships
    new_lines = []
    relationships_added = False
    
    for i, line in enumerate(lines):
        if i == relationships_start + 1:  # Right after "# Relationships"
            new_lines.append(line)
            
            # Add all required relationships if they don't exist
            if not has_user:
                new_lines.append('    user = relationship("User", back_populates="emissions", foreign_keys=[user_id])')
            if not has_evidence:
                new_lines.append('    evidence_documents = relationship("EvidenceDocument", back_populates="emission", cascade="all, delete-orphan")')
            if not has_quality:
                new_lines.append('    data_quality_scores = relationship("DataQualityScore", back_populates="emission", cascade="all, delete-orphan")')
            
            relationships_added = True
        else:
            new_lines.append(line)
    
    # Write back
    with open("app/models/emission.py", "w") as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Fixed all relationships in Emission model")

if __name__ == "__main__":
    fix_emission_relationships()
