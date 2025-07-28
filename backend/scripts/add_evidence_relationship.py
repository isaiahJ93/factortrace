#!/usr/bin/env python3
"""Add evidence_documents relationship to Emission model"""

def add_evidence_relationship():
    with open("app/models/emission.py", "r") as f:
        lines = f.readlines()
    
    # Find where to add the relationship (after data_quality_scores)
    new_lines = []
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add after data_quality_scores relationship
        if "data_quality_scores = relationship" in line and not added:
            new_lines.append('    evidence_documents = relationship("EvidenceDocument", back_populates="emission", cascade="all, delete-orphan")\n')
            added = True
    
    if not added:
        print("⚠️  Could not find where to add the relationship")
        return
    
    with open("app/models/emission.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Added evidence_documents relationship to Emission model")

if __name__ == "__main__":
    add_evidence_relationship()
