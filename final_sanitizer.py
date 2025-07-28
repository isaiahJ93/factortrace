import os
import re

TARGET_DIRS = ['src', 'tests']

# Patterns to fix: trailing quote/comma junk from syntax recovery
fix_patterns = [
    (re.compile(r'(".*?")\s*,\s*$'), r'\1'),         # trailing quote-comma
    (re.compile(r'\)\s*"\)?\s*$'), r')'),            # closing paren + extra quote
    (re.compile(r'^(\s*)",\s*$'), r'\1""'),          # dangling ", on its own line
    (re.compile(r'"\)$'), r')'),                     # remove rogue quote before )
    (re.compile(r'"\]$'), r']'),                     # quote before ]
    (re.compile(r'"\}$'), r'}'),                     # quote before }
    (re.compile(r'"$'), r''),                        # final lone quote
]

def fix_line(line):
    for pattern, replacement in fix_patterns:
        line = pattern.sub(replacement, line)
    return line

def sanitize_file(path):
    with open(path, 'r') as f:
        original = f.readlines()

    fixed = [fix_line(line) for line in original]

    if fixed != original:
        with open(path, 'w') as f:
            f.writelines(fixed)
        print(f"🧹 Cleaned: {path}")

for root in TARGET_DIRS:
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith('.py'):
                sanitize_file(os.path.join(dirpath, file))