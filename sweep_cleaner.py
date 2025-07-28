import os
import re
from pathlib import Path

SOURCE_DIRS = ["./src", "./tests"]

REPLACEMENTS = {
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '❌': '', '✅': '', '→': '->', '…': '...',
}

MERGE_PATTERN = re.compile(r'""".*?"\s*"""|"\s*"')

def clean_line(line):
    # Replace smart chars
    for k, v in REPLACEMENTS.items():
        line = line.replace(k, v)

    # Remove lines that are just a dangling double or triple quote
    if line.strip() in ['"', "'''", '"""', "'", '"']:
        return "

    # Replace broken FIXMEs or triple quote collisions
    line = MERGE_PATTERN.sub('"""FIXME"', line)

    # Add colons to control structures missing them
    if re.match(r'^\s*(if|for|while|elif|except|with)\s.+[^:]\s*$', line):
        return line.rstrip() + ":"

    return line

def fix_file(path: Path):
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        fixed = []

        for line in lines:
            fixed.append(clean_line(line))

        # Rejoin and close unclosed quotes or brackets
        joined = "\n".join(fixed)

        # Cheap patch for unterminated string or parens
        if joined.count('"') % 2 != 0:
            joined += '"'
        if joined.count('(') > joined.count(')'):
            joined += ')'

        path.write_text(joined, encoding='utf-8')
        print(f"✅ Fixed: {path}")
    except Exception as e:
        print(f"❌ Failed: {path} - {e}")

def sweep():
    for dir in SOURCE_DIRS:
        for path in Path(dir).rglob("*.py"):
            fix_file(path)

if __name__ == "__main__":
    sweep()