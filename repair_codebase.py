#!/usr/bin/env python3
"
repair_codebase.py
──────────────────
Recursively scans a codebase (default: current working directory) and
auto-repairs the most common structural breakages introduced by flaky
refactors or copy-paste chaos:

    • malformed/fancy quotes  (“ ” ‘ ’ « ») → normal ASCII quotes
    • unterminated strings / docstrings
    • missing colons after def/class/if/for/while/try/…
    • indentation mismatches (tabs → spaces, mixed tabs/spaces)
    • stray Unicode symbols (arrows, emojis, bullets)
    • unbalanced (), [], {}  — adds minimum closers at file end

Guarantees
──────────
✦ **Never** touches a syntactically valid file.  
✦ Creates   <filename>.py.bak2   before writing fixes.  
✦ Aborts a file’s edit if the post-fix source still fails to compile.  
✦ Finishes with   python -m compileall   to prove the repo compiles.

Usage
─────
    python repair_codebase.py --root .
    python repair_codebase.py --root ./src          # just one subtree
"

from __future__ import annotations

import argparse
import compileall
import io
import pathlib
import re
import shutil
import sys
import tokenize
from typing import List

# ──────────────────────────────────────────────────────────────────────────────
#  Low-level transformers
# ──────────────────────────────────────────────────────────────────────────────

FANCY_QUOTES = {
    "“": '"',
    "”": '"',
    "„": '"',
    "«": '"',
    "»": '"',
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‹": "'",
    "›": "'",
}

INVALID_CHARS_RE = re.compile(
    r"[•→←↔⇒►◄🡆✅❌🚫🔒🔐🤖💥🔥👀📝✨💯🔧📌⏱️]"
)


def replace_fancy_quotes(text: str) -> str:
    """Map curved / locale quotes to ASCII quotes."
    for bad, good in FANCY_QUOTES.items():
        text = text.replace(bad, good)
    return text


def strip_invalid_chars(text: str) -> str:
    """Remove stray symbols that break Python parsers."
    return INVALID_CHARS_RE.sub(", text)


TRIPLE = ('"""', "'''")  # used twice


def close_unterminated_triple_quotes(text: str) -> str:
    """Ensure each file ends with balanced triple quotes."
    for mark in TRIPLE:
        if text.count(mark) % 2:  # odd ⇒ unterminated
            text += mark
    return text


def close_unterminated_strings(text: str) -> str:
    """Add missing closing quote on lines with odd quote counts."
    fixed_lines: List[str] = []
    for line in text.splitlines():
        for q in ("'", '"'):
            if line.count(q) % 2 and not line.rstrip().endswith("\\"):
                line += q
        fixed_lines.append(line)
    return "\n".join(fixed_lines)


COLON_KW = (
    "if",
    "elif",
    "else",
    "for",
    "while",
    "def",
    "class",
    "try",
    "except",
    "finally",
)


def ensure_colons(text: str) -> str:
    """Add colons after block-opening keywords when missing."
    pattern = re.compile(rf"^(\s*)({'|'.join(COLON_KW)})\b([^:#\n]*)(\s*#.*)?$", re.M)

    def repl(m: re.Match[str]) -> str:
        indent, kw, rest, comment = m.groups()
        line = m.group(0)
        if line.rstrip().endswith(":"):
            return line
        return f"{indent}{kw}{rest.rstrip()}:{comment or ''}"

    return pattern.sub(repl, text)


def fix_indentation(text: str) -> str:
    """Convert hard tabs → 4 spaces; drop weird mixed-tab artefacts."
    return text.expandtabs(4)


BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}


def balance_brackets(text: str) -> str:
    """Naïvely append closing brackets if file ends imbalanced."
    stack: List[str] = []
    for ch in text:
        if ch in BRACKET_PAIRS:
            stack.append(ch)
        elif ch in BRACKET_PAIRS.values() and stack:
            if BRACKET_PAIRS[stack[-1]] == ch:
                stack.pop()
    if stack:
        closers = ".join(BRACKET_PAIRS[c] for c in reversed(stack))
        text += "\n" + closers + "\n"
    return text


# ──────────────────────────────────────────────────────────────────────────────
#  End-to-end repair pipeline
# ──────────────────────────────────────────────────────────────────────────────


def needs_fix(path: pathlib.Path) -> bool:
    """Fast check: does file raise Syntax/Indent errors?"
    try:
        compile(path.read_text("utf8"), str(path), "exec")
        return False
    except (SyntaxError, IndentationError, UnicodeDecodeError):
        return True


def attempt_fix(src: str) -> str:
    """Run the full suite of heuristic repairs on raw source text."
    src = replace_fancy_quotes(src)
    src = strip_invalid_chars(src)
    src = close_unterminated_triple_quotes(src)
    src = close_unterminated_strings(src)
    src = ensure_colons(src)
    src = fix_indentation(src)
    src = balance_brackets(src)
    # Token-level pass: tidy stray tokens, ignore broken indentation
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
        src = tokenize.untokenize(tokens)
    except (tokenize.TokenError, IndentationError):
        # File is still too broken to tokenize safely — skip this cleanup step
        pass
    return src


def process_file(py_file: pathlib.Path, fixed: List[pathlib.Path]) -> None:
    original = py_file.read_text("utf8", errors="ignore")
    patched = attempt_fix(original)
    try:
        compile(patched, str(py_file), "exec")
    except (SyntaxError, IndentationError):
        # Still broken – keep original to avoid masking deeper issues
        return
    # Passed compile ⇒ safe to write + backup
    bak = py_file.with_suffix(py_file.suffix + ".bak2")
    shutil.copyfile(py_file, bak)
    py_file.write_text(patched, "utf8")
    fixed.append(py_file)


def repair_tree(root: pathlib.Path) -> None:
    candidates = [
        p
        for p in root.rglob("*.py")
        if not any(part.startswith(".") for part in p.parts)
    ]
    fixed: List[pathlib.Path] = []
    for path in candidates:
        if needs_fix(path):
            process_file(path, fixed)

    # Final compile pass
    compile_success = compileall.compile_dir(
        root, quiet=1, force=False, rx=re.compile(r"site-packages")
    )

    if fixed:
        print("\n🛠️  Fixed the following files:")
        for f in fixed:
            print("   ├─", f)
    else:
        print("✅ No syntax breakages detected.")

    if not compile_success:
        print(
            "\n⚠️  Some files remain uncompilable; inspect the above compileall output.",
            file=sys.stderr,
        )


# ──────────────────────────────────────────────────────────────────────────────
#  CLI entry-point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Auto-repair Python syntax / indentation corruption "
        "across an entire repo without touching valid code."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory to scan (defaults to CWD)",
    )
    args = parser.parse_args()
    repair_tree(pathlib.Path(args.root).resolve())

