import os
import re

TARGET_DIRS = ['src', 'tests']
QUOTES = ['"', "'", '"""', "'''"]

def has_unclosed_quote(line):
    for q in QUOTES:
        if line.count(q) % 2 != 0:
            return True
    return False

def try_fix_line(line):
    for q in ['"""', "'''", '"', "'"]:
        if line.count(q) % 2 != 0:
            # Try appending one
            return line.rstrip() + q + "\n"
    return line

def backup_file(path):
    with open(path, 'r') as f:
        content = f.read()
    with open(path + '.bak', 'w') as f:
        f.write(content)

def fix_file(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    modified = False
    fixed_lines = []

    for line in lines:
        if has_unclosed_quote(line):
            fixed_line = try_fix_line(line)
            if fixed_line != line:
                print(f"🛠️  Fixed quote in {path}: {line.strip()}")
                modified = True
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    if modified:
        backup_file(path)
        with open(path, 'w') as f:
            f.writelines(fixed_lines)

for root in TARGET_DIRS:
    for dirpath, _, files in os.walk(root):
        for file in files:
            if file.endswith('.py'):
                fix_file(os.path.join(dirpath, file))

print("\n✅ Final quote sweep complete. Re-run compile check.")
