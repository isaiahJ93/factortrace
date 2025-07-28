import re
from pathlib import Path

SOURCE_DIRS = ["src", "tests"]

fixes_applied = []

for path in [p for d in SOURCE_DIRS for p in Path(d).rglob("*.py")]:
    try:
        content = path.read_text(encoding="utf-8")
        original = content

        # Remove broken import statements like: from x import ()
        content = re.sub(r"from\s+[a-zA-Z0-9_.]+\s+import\s+\(\s*\)", ", content)

        # Fix unterminated triple quotes
        content = re.sub(r'""{2,}', '"', content)

        # Fix broken Field aliases
        content = re.sub(r'Field\(alias="([^"]+)"+"\)', r'Field(alias="\1")', content)

        # Fix unmatched parentheses in f-strings
        content = re.sub(r"\{([^\{\}]*?)\)\}", r"{\1})", content)
        content = re.sub(r"\{([^\{\}]*?)\]\}", r"{\1]}", content)

        # Remove placeholder functions like def FUNCTION():
        content = re.sub(r"\s*def FUNCTION\(\):\s*\n\s*pass\n?", ", content)

        # Fix unmatched parenthesis or brackets
        content = re.sub(r"\(\]", "()", content)
        content = re.sub(r"\[\)", "[]", content)

        # Fix unmatched parentheses/brackets at end of line
        content = re.sub(r"\([^\)]*\]\)", "()", content)
        content = re.sub(r"\[[^\]]*\)\]", "[]", content)

        # Fix unmatched string literal in Field or print/f-string
        content = re.sub(r'"([^"]*)""', r'"\1"', content)
        content = re.sub(r"'([^']*)''", r"'\1'", content)

        if content != original:
            path.write_text(content, encoding="utf-8")
            fixes_applied.append(str(path))

    except Exception as e:
        print(f"⚠️ Error fixing {path}: {e}")

# Final report
print(f"\n✅ Fixed {len(fixes_applied)} files.")
for f in fixes_applied:
    print(f" - {f}")