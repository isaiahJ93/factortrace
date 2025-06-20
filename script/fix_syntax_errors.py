import re
from pathlib import Path

ROOT_DIRS = ["src", "tests"]
PY_FILES = [f for d in ROOT_DIRS for f in Path(d).rglob("*.py")]

FIXED_MARKER = "# [AUTO-FIXED]"

for file in PY_FILES:
    content = file.read_text()
    original = content
    lines = content.splitlines()

    # Fix unmatched import blocks
    if "from factortrace.shared_enums import (" in content and not re.search(r"^\s*\)", content, re.MULTILINE):
        for i, line in enumerate(lines):
            if "from factortrace.shared_enums import (" in line:
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == ")":
                        break
                    if j == len(lines) - 1:
                        lines.insert(j + 1, ")  " + FIXED_MARKER)
                        break

    # Fix docstrings that are opened but not closed
    open_triple = None
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') and line.count('"""') == 1:
            if open_triple is None:
                open_triple = i
            else:
                # Close it on this line
                lines[i] = lines[i] + '"""  ' + FIXED_MARKER
                open_triple = None

    # Fix single unmatched closing parens/brackets
    lines = [re.sub(r'=\s*("[^"]*")\)', r'= \1', l) for l in lines]  # e.g. uniform = "uniform")
    lines = [re.sub(r'([a-zA-Z_]\w*)\s*:\s*[\w\[\]]+\)', r'\1: TYPE', l) for l in lines]  # Remove rogue closing )
    lines = [l if l.strip() != ")" or lines[i-1].strip().endswith("(") else l + "  " + FIXED_MARKER for i, l in enumerate(lines)]

    # Fix unmatched import square brackets (if used by mistake)
    lines = [re.sub(r'^from .* import \[', 'from MODULE import (', l) for l in lines]
    lines = [l.replace(']', ')') if 'from' in l and '[' in l and ']' in l else l for l in lines]

    # Add commas if missing in field defs or kwargs
    lines = [re.sub(r'^(.*=".*")(?!,)', r'\1,', l) if '=' in l and 'description' in l else l for l in lines]

    fixed = "\n".join(lines)

    if fixed != original:
        file.write_text(fixed)
        print(f"✅ Fixed: {file}")