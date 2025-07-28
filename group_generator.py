import os
from pathlib import Path

# Set your source folder path
SRC_DIR = Path("src")

# How many files per group to paste into Claude
FILES_PER_GROUP = 5

# Get all Python files recursively
py_files = list(SRC_DIR.rglob("*.py"))

# Split into groups
groups = [py_files[i:i + FILES_PER_GROUP] for i in range(0, len(py_files), FILES_PER_GROUP)]

# Output
for idx, group in enumerate(groups, 1):
    print(f"\n\n### GROUP {idx} of {len(groups)} — Paste this into Claude:\n")
    print("Say: These are Python files from my project. Please fix **only syntax errors** and keep logic intact.")
    for file in group:
        print(f"\n# FILE: {file.relative_to(SRC_DIR)}")
        try:
            with open(file, "r", encoding="utf-8") as f:
                print(f.read())
        except Exception as e:
            print(f"# ERROR READING FILE: {e}")
