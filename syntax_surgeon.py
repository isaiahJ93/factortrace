import re
from pathlib import Path

SOURCE_DIRS = ["./src", "./tests"]

# Common string and token sanitizers
CLEAN_REPLACEMENTS = {
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '❌': '', '✅': '', '→': '->',
}

def fix_syntax(text: str) -> str:
    # Replace smart quotes and symbols
    for bad, good in CLEAN_REPLACEMENTS.items():
        text = text.replace(bad, good)

    # Fix unterminated strings
    text = re.sub(r'"([^"\n]*)\n', r'"\1"\n', text)
    text = re.sub(r"'([^'\n]*)\n", r"'\1'\n", text)

    # Fix unterminated triple-quoted strings
    text = re.sub(r'"""(.*?)("\s*FIXME)?["]*', r'"""\1"', text, flags=re.DOTALL)

    # Fix decorators like @app.get("/)
    text = re.sub(r'@[\w\.]+\(["\'].*$', lambda m: m.group(0).rstrip('\'"') + '")', text)

    # Add colon to control statements if missing
    text = re.sub(r'^\s*(if|for|while|elif|except|with)\s.*[^:]\s*$', lambda m: m.group(0).rstrip() + ':', text, flags=re.M)

    # Fix unmatched parentheses (common pattern: input("something)
    text = re.sub(r'(\w+\()([^\n"\')]+)', r'\1"\2"', text)

    return text

def clean_file(path: Path):
    try:
        original = path.read_text(encoding="utf-8", errors="ignore")
        fixed = fix_syntax(original)
        path.write_text(fixed, encoding="utf-8")
        print(f"✅ Repaired: {path}")
    except Exception as e:
        print(f"❌ Error in {path}: {e}")

def sweep_all():
    for src_dir in SOURCE_DIRS:
        for path in Path(src_dir).rglob("*.py"):
            clean_file(path)

if __name__ == "__main__":
    sweep_all()
    