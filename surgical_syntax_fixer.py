import os
import re

SOURCE_DIRS = ["src", "tests"]

# Targeted patterns and fixes
FIXES = [
    # Unmatched brackets: remove lone closers
    (r"(?<![{\[\(])\}\)?\]$", "),  # orphaned closing
    (r"\):$", ")"),  # safe fix for wrongly closed defs
    # Common syntax mistakes
    (r"([fF])?\"([^\"]*)\}([^\"]*)$", r'"\2}\3"'),  # broken f-string
    (r"\basync def ([\w_]+)\(([^)]*)$", r"async def \1(\2):"),  # incomplete async defs
    (r"\bdef ([\w_]+)\(([^)]*)$", r"def \1(\2):"),  # incomplete defs
    (r"print\(([^)]*)$", r"print(\1)"),  # broken print(
    (r"\{[^}]*$", lambda m: m.group(0).rstrip("{") + "}"),  # auto-close {
    (r"\[[^\]]*$", lambda m: m.group(0).rstrip("[") + "]"),  # auto-close [
    (r"\([^\)]*$", lambda m: m.group(0).rstrip("(") + ")"),  # auto-close (
    (r'"""([^"]*)$', r'"""\1"'),  # fix triple-quoted strings
    (r"(?<!\S)\}", "),  # orphaned closing brace
    (r",\s*\}", "}"),  # trailing commas before close
]

def fix_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.readlines()

        changed = False
        fixed = []

        for line in original:
            new_line = line
            for pattern, repl in FIXES:
                if callable(repl):
                    new_line = re.sub(pattern, repl, new_line)
                else:
                    new_line = re.sub(pattern, repl, new_line)
            if new_line != line:
                changed = True
            fixed.append(new_line.rstrip())

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(fixed) + "\n")
            print(f"✅ Fixed: {path}")

    except Exception as e:
        print(f"❌ Error fixing {path}: {e}")

def sweep_all():
    for base in SOURCE_DIRS:
        for root, _, files in os.walk(base):
            for file in files:
                if file.endswith(".py"):
                    fix_file(os.path.join(root, file))

if __name__ == "__main__":
    sweep_all()