#!/usr/bin/env python3
"""Fix the Emission model to include quality_scores relationship"""

def fix_emission_model():
    with open("app/models/emission.py", "r") as f:
        lines = f.readlines()
    
    # Find where to add the relationship
    import_added = False
    relationship_added = False
    
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add import if needed
        if "from sqlalchemy.orm import" in line and not import_added:
            if "relationship" not in line:
                new_lines[-1] = line.rstrip() + ", relationship\n"
            import_added = True
        
        # Add relationship after other relationships or before the class ends
        if ("evidence_documents" in line or "user = relationship" in line) and not relationship_added:
            # Add the quality_scores relationship after this line
            new_lines.append('    quality_scores = relationship("DataQualityScore", back_populates="emission", cascade="all, delete-orphan")\n')
            relationship_added = True
        elif line.strip() == "" and i > 0 and "class Emission" in lines[i-10:i] and not relationship_added:
            # Add before the empty line at the end of the class
            new_lines.insert(-1, '    quality_scores = relationship("DataQualityScore", back_populates="emission", cascade="all, delete-orphan")\n')
            relationship_added = True
    
    # If we still haven't added it, find the end of the Emission class
    if not relationship_added:
        for i in range(len(new_lines)):
            if "class Emission" in new_lines[i]:
                # Find the next class or end of file
                for j in range(i+1, len(new_lines)):
                    if j == len(new_lines)-1 or (new_lines[j].startswith("class ") or new_lines[j].startswith("def ")):
                        # Insert before this line
                        new_lines.insert(j-1, '    quality_scores = relationship("DataQualityScore", back_populates="emission", cascade="all, delete-orphan")\n')
                        break
                break
    
    with open("app/models/emission.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Fixed Emission model - added quality_scores relationship")

if __name__ == "__main__":
    fix_emission_model()
