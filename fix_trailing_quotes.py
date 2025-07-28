import os
import re

# Directories to scan
TARGET_DIRS = ["src", "tests"]

# File extensions to clean
ALLOWED_EXTENSIONS = {".py", ".xml", ".xsd", ".html", ".xhtml"}

def should_process(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def clean_line(line):
    # Fix trailing double quotes: ..."" → ..."
    line = re.sub(r'"{2,}([^"\n]*)$', r'"\1', line)

    # Fix assignment or function params with = "value" → = "value"
    line = re.sub(r'=\s*"([^"]+?)"{2,}', r'= "\1"', line)

    # Strip triple quotes that never close properly (very naive safeguard)
    line = re.sub(r'("""[^"]*)"{2,}', r'\1"', line)

    return line

def walk_and_clean():
    total_changes = 0
    for root, _, files in os.walk("."):
        for file in files:
            if not should_process(file):
                continue

            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            modified = False
            cleaned_lines = []

            for line in lines:
                cleaned = clean_line(line)
                if cleaned != line:
                    modified = True
                    total_changes += 1
                cleaned_lines.append(cleaned)

            if modified:
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(cleaned_lines)
                print(f"[fixed] {path}")

    print(f"\n✅ Cleaning complete. {total_changes} lines fixed.")

if __name__ == "__main__":
    walk_and_clean()