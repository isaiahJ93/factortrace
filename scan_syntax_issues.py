import os
import re

TARGET_DIRS = ['src', 'tests']
ISSUE_PATTERNS = {
    'unmatched_paren': re.compile(r'[^\(\)]*\)(?![^()]*\()'),
    'unmatched_brace': re.compile(r'[^\{\}]*\}(?![^{}]*\{)'),
    'unmatched_bracket': re.compile(r'[^\[\]]*\](?![^\[\]]*\[)'),
    'invalid_annotation': re.compile(r'^\s*"[^"]+"\s*:', re.MULTILINE),
    'bad_triple_quotes': re.compile(r'^\s*["\']{3}[^"\']*$', re.MULTILINE),
}

flagged_files = []

def scan_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        for name, pattern in ISSUE_PATTERNS.items():
            if pattern.search(content):
                flagged_files.append(filepath)
                return
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        flagged_files.append(filepath)

def walk_and_scan():
    for dir in TARGET_DIRS:
        for root, _, files in os.walk(dir):
            for file in files:
                if file.endswith('.py'):
                    scan_file(os.path.join(root, file))

def main():
    print("🔍 Scanning for syntax issues...")
    walk_and_scan()
    print(f"\n⚠️ {len(flagged_files)} files flagged for manual review:\n")
    for path in flagged_files:
        print(" -", path)

if __name__ == '__main__':
    main()
    