#!/usr/bin/env python3
"""Fix duplicate quality_scores relationship"""

def fix_duplicate_relationship():
    with open("app/models/emission.py", "r") as f:
        lines = f.readlines()
    
    # Remove any line with quality_scores (not data_quality_scores)
    new_lines = []
    removed = False
    
    for line in lines:
        if "quality_scores = relationship" in line and "data_quality_scores" not in line:
            removed = True
            print(f"Removing duplicate: {line.strip()}")
            continue
        new_lines.append(line)
    
    if removed:
        with open("app/models/emission.py", "w") as f:
            f.writelines(new_lines)
        print("✅ Removed duplicate relationship")
    else:
        print("No duplicates found")

if __name__ == "__main__":
    fix_duplicate_relationship()
