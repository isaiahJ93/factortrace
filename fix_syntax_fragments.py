import os
import re
from pathlib import Path
import shutil

# Directories to scan
source_dirs = ["src", "tests"]

# Safe replacements for bad characters or fragments
replacements = {
    "—": "-", 
    "➜": "->", 
    "§": "section", 
    "₃": "3", 
    "₂": "2", 
    "•": "*", 
    "─": "-",
    'FIXME"': '"',
    "FIXME'": "'",
    'FIXME': '',  # Remove any remaining 'FIXME' markers
}

change_log = []

for directory in source_dirs:
    for path in Path(directory).rglob("*.py"):
        try:
            content = path.read_text(encoding="utf-8")
            original = content

            # Backup original
            backup_path = path.with_suffix(".bak")
            shutil.copy(path, backup_path)

            # Replace broken string fragments and characters
            for bad, fixed in replacements.items():
                content = content.replace(bad, fixed)

            # Fix common unterminated string patterns
            content = re.sub(r'("[^"\n]*)\n', r'\1"\n', content)
            content = re.sub(r"('[^'\n]*)\n", r"\1'\n", content)

            if content != original:
                path.write_text(content, encoding="utf-8")
                change_log.append(str(path))

        except Exception as e:
            print(f"⚠️ Error processing {path}: {e}")

# Final log
print(f"\n✅ Fixed syntax in {len(change_log)} files")
for f in change_log:
    print(f"  - {f}")