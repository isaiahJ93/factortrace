import os
import re
from pathlib import Path

# Root directory for your project
ROOT_DIR = Path("src")

# Regex fix patterns
FIXES = [
    (r'\"{3,}', '"'),  # Triple quotes
    (r'\"{2,}', '"'),    # Double quotes
    (r"\'{2,}", "'"),    # Single quotes
    (r'"(\s*\))', r'"\1'),  # Close quote before close paren
    (r'(\()\s*"', r'\1"'),  # Open paren before open quote
    (r'"$', '",'),          # Hanging end quote
    (r'"\s*$', '",'),       # Hanging quote w/ whitespace
    (r'"\)', '")'),         # Common typo fix
    (r'"\]', '"]'),         # Common typo fix
    (r'"\}', '"}'),         # Common typo fix
    (r'"\n', '",\n'),       # Open string not terminated
    (r"(?<!\\)''", '"'),    # Convert stray double single quotes
]

# Function to fix a file
def fix_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    for pattern, replacement in FIXES:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🔧 Fixed: {file_path}")

# Walk through all Python files in `src/` and `tests/`
def run_second_pass():
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                fix_file(os.path.join(root, file))
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                fix_file(os.path.join(root, file))

if __name__ == "__main__":
    run_second_pass()
    print("✅ Second pass complete.")