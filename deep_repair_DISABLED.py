"
Deep Repair Mode V2
────────────────────
This script extends the original repair pipeline with surgical AST-level and regex-based
fixes for malformed Python files that standard parsing can't handle.

🧠 Fixes:
    • Broken parentheses and unterminated calls
    • Malformed Field(...) expressions with missing quotes
    • Unterminated strings and f-strings
    • Invalid characters in string literals (emojis, arrows)
    • Triple-quoted docstrings that start/close incorrectly
    • Lines with obvious syntax corruption that can be inferred

🚨 WARNING: This will now **aggressively try to rewrite** lines with recoverable corruption.
Backups (.bak2) are still created, and compile check is enforced before overwrite.
"

import re
import ast
import pathlib
import shutil
from tokenize import TokenError
from typing import List

INVALID_CHAR_RE = re.compile(r"[\u2190-\u21FF\u2600-\u27BF\u2700-\u27BF\u1F300-\u1F6FF]")
FIELD_EXPR_RE = re.compile(r'Field\(alias="[^"]*"\)')
BROKEN_FSTRING_RE = re.compile(r'f"[^"]*[{|}][^"]*$')
BROKEN_COMMENT_QUOTE_RE = re.compile(r'""[^"]{1,30}:(?!\")')


REPLACEMENTS = [
    (re.compile(r"(Field\(alias=\"[^"]+)\)\s+"), lambda m: m.group(1) + '")'),
    (re.compile(r'("[^"]*)(\n)'), lambda m: m.group(1).replace('"', '') + '"' + m.group(2)),
    (re.compile(r'("{3})(?!.*"{3})'), lambda m: '"' if m.group(1) else m.group(0)),
    (re.compile(r"\)(\s*[^\n\)])"), lambda m: ')' + m.group(1) if not m.group(1).startswith('#') else m.group(0)),
]


def aggressive_line_fix(line: str) -> str:
    line = INVALID_CHAR_RE.sub('', line)
    if 'Field(alias=' in line and line.count('"') == 1:
        line += '"')
    if 'f"' in line and line.count('"') == 1:
        line += '"'
    if line.strip().endswith('(') and not line.strip().startswith('#'):
        line += ')'  # Close lonely parens
    for pattern, func in REPLACEMENTS:
        line = pattern.sub(func, line)
    return line


def deep_repair(path: pathlib.Path) -> bool:
    try:
        original = path.read_text("utf-8", errors="ignore")
    except Exception:
        return False

    lines = original.splitlines()
    fixed_lines: List[str] = []

    for line in lines:
        fixed = aggressive_line_fix(line)
        fixed_lines.append(fixed)

    joined = "\n".join(fixed_lines)

    try:
        ast.parse(joined)
    except (SyntaxError, ValueError):
        return False  # Still broken

    bak_path = path.with_suffix(path.suffix + ".bak2")
    shutil.copy(path, bak_path)
    path.write_text(joined, encoding="utf-8")
    return True


def deep_repair_all(root_dir: pathlib.Path):
    all_py_files = list(root_dir.rglob("*.py"))
    fixed_files = []

    for py_file in all_py_files:
        if deep_repair(py_file):
            fixed_files.append(py_file)

    if fixed_files:
        print("\n🧠 Deep Repair Fixed:")
        for f in fixed_files:
            print("   ├─", f)
    else:
        print("✅ No deeply broken files were fixable.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    deep_repair_all(pathlib.Path(args.root).resolve())