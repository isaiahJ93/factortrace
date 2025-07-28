import os
import re

def fix_file(path):
    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    paren_stack = 0
    fixed_import = False
    broken_block = False

    for i, line in enumerate(lines):
        if "from factortrace.shared_enums import (" in line:
            paren_stack = 1
            fixed_import = True
            new_lines.append(line)
            continue

        if fixed_import and paren_stack > 0:
            new_lines.append(line)
            paren_stack += line.count("(") - line.count(")")
            if paren_stack == 0:
                fixed_import = False
            continue

        if re.match(r"^\s*\)\s*$", line) and not any("(" in l for l in lines[:i]):
            continue

        if re.match(r".*[\[{(]$", line.strip()) and not line.strip().startswith("#"):
            broken_block = True
            new_lines.append(f"# 🔧 REVIEW: possible unclosed bracket -> {line}")
            continue

        if re.match(r"^\s*[\])}]", line) and not any(open in "".join(lines[:i]) for open in "([{"):
            new_lines.append(f"# 🔧 REVIEW: unmatched closing bracket -> {line}")
            continue

        new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    return broken_block

ROOTS = ["src", "tests"]
total_fixed = 0
flagged = []

for root in ROOTS:
    for dirpath, _, filenames in os.walk(root):
        for file in filenames:
            if file.endswith(".py"):
                path = os.path.join(dirpath, file)
                if fix_file(path):
                    flagged.append(path)
                total_fixed += 1

print(f"✅ Auto-fix completed. {total_fixed} files scanned.")
if flagged:
    print("\n⚠️ Flagged files that need manual review:")
    for f in flagged:
        print(" -", f)
