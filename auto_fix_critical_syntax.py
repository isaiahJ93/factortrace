import os
import re

SOURCE_DIRS = ["src", "tests"]
EXTENSIONS = (".py",)

# Unsafe Unicode chars that break Python parsing
UNICODE_REPLACEMENTS = {
    "—": "-",   # em dash
    "–": "-",   # en dash
    "§": "S",   # section sign
    "➜": "->",  # arrow
    "•": "*",   # bullet
    "₁": "1", "₂": "2", "₃": "3",  # subscripts
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
}

# Quick-fix patterns
QUICK_FIXES = [
    (r"(class|def|async def) [\w_]+\([^\)]*\)$", r"\1 FUNCTION():"),
    (r"(class [\w_]+)\s*$", r"\1:"),
    (r"(?<!['\"#])\"\"\".*$", r'"""FIXME"'),  # open triple-quoted lines
    (r"(?<!['\"#])\"[^\"]*$", r'"FIXME"'),      # open string
    (r"(?<!['\"#])'[^\']*$", r"'FIXME'"),       # open string
    (r"^\s*\)", ""), (r"^\s*\]", ""), (r"^\s*\}", "),  # unmatched closers
    (r"\([^\)]*$", lambda m: m.group(0) + ")"),
    (r"\[[^\]]*$", lambda m: m.group(0) + "]"),
    (r"\{[^\}]*$", lambda m: m.group(0) + "}"),
]

def clean_unicode(text):
    for bad, replacement in UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, replacement)
    return text

def fix_line(line):
    line = clean_unicode(line)
    for pattern, replacement in QUICK_FIXES:
        if callable(replacement):
            line = re.sub(pattern, replacement, line)
        else:
            line = re.sub(pattern, replacement, line)
    return line

def fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = [fix_line(line.rstrip()) for line in lines]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")

        print(f"✅ Fixed: {filepath}")
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")

def run_fix():
    for base_dir in SOURCE_DIRS:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(EXTENSIONS):
                    fix_file(os.path.join(root, file))

if __name__ == "__main__":
    run_fix()
    