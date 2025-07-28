import os
import re

TARGET_DIRS = ["src", "tests"]
SYNTAX_ISSUES = [
    (r'(?<!["\'])\b("[^"]*")\s*:', r"\1:"),  # avoid using dicts as annotations
    (r"\)(\s*\))+", r")"),  # reduce duplicate closing parens
    (r"\}\s*\}", r"}"),     # reduce duplicate closing braces
    (r"\]\s*\]", r"]"),     # reduce duplicate closing brackets
    (r'"""([^"]*)$', r'"""\1"'),  # incomplete triple-quoted string
    (r'(?<!")("""[^"]*)$', r'\1"'),  # trailing triple quote fixer
    (r"\)\s*\}", r"}"),     # mismatched paren + brace
    (r"\)\s*\]", r"]"),     # mismatched paren + bracket
]

def fix_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        for pattern, repl in SYNTAX_ISSUES:
            content = re.sub(pattern, repl, content)

        lines = content.splitlines()
        fixed_lines = []
        for line in lines:
            if line.strip().startswith('"') and ':' in line:
                # likely misused JSON-style field
                line = "#" + line
            fixed_lines.append(line.rstrip())

        content = "\n".join(fixed_lines) + "\n"

        if content != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Patched: {path}")
    except Exception as e:
        print(f"❌ Failed: {path} → {e}")

def walk_and_fix():
    for root_dir in TARGET_DIRS:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):
                    fix_file(os.path.join(root, file))

if __name__ == "__main__":
    walk_and_fix()
    