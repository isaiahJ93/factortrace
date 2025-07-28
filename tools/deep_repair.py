#!/usr/bin/env python3
"
Deep Repair Script for Scope 3 Compliance Tool
Fixes syntax errors while preserving business logic and architectural patterns
"

import ast
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import logging
import argparse
from dataclasses import dataclass
from datetime import datetime
import difflib
import black


@dataclass
class RepairResult:
    """Result of a repair operation"
    file_path: Path
    original_lines: List[str]
    repaired_lines: List[str]
    changes_made: List[Tuple[int, str, str]]  # (line_no, original, repaired)
    success: bool
    error: Optional[str] = None


class CodebaseRepairTool:
    "
    Deep repair tool specifically tailored for the Scope 3 compliance codebase
    Preserves architectural patterns and coding style used throughout the project
    "
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.backup_suffix = ".bak2"
        self.stats = {
            "files_scanned": 0,
            "files_repaired": 0,
            "errors_fixed": 0,
            "files_skipped": 0
        }
        
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns specific to our codebase patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns used for repairs"
        
        # Pattern 1: Invalid UTF-8 characters (emojis, special arrows)
        # We use these sparingly in comments/logs, but not in production code
        self.invalid_char_re = re.compile(
            r"[\u2190-\u21FF\u2600-\u27BF\u2700-\u27BF\u1F300-\u1F6FF\u1F900-\u1F9FF]"
        )
        
        # Pattern 2: Pydantic Field with broken syntax
        # Common pattern: Field(alias="something", description="...")
        self.field_basic_re = re.compile(
            r'Field\s*\(\s*alias\s*=\s*"([^"]*)"(?:\s*,\s*|\s*\))'
        )
        
        # Pattern 3: Field with multiple parameters (more comprehensive)
        self.field_complex_re = re.compile(
            r'(\w+)\s*:\s*(\w+(?:\[[\w\[\], ]+\])?)\s*=\s*Field\s*\((.*?)\)(?=\s*(?:#|$|\w+\s*:))',
            re.MULTILINE | re.DOTALL
        )
        
        # Pattern 4: Broken f-strings (unterminated)
        self.broken_fstring_re = re.compile(
            r'(f"[^"]*(?:{[^}]*}[^"]*)*{[^}]*)$|'  # f-string with unclosed brace
            r'(f"[^"]*{[^}]*}[^"]*)(?=[^"]|$)'     # f-string missing closing quote
        )
        
        # Pattern 5: Malformed docstrings/comments
        self.broken_docstring_re = re.compile(
            r'^\s*("""|\'\'\')?([^"\']*)(?::|;)\s*$'  # Docstring with wrong ending
        )
        
        # Pattern 6: Import statement issues
        self.broken_import_re = re.compile(
            r'^(\s*)(from\s+[\w.]+\s+import\s+)([^#\n]+?)(\s*)(,)?(\s*)(#.*)?$'
        )
        
        # Pattern 7: Type hint issues (common in our codebase)
        self.type_hint_re = re.compile(
            r'(\w+)\s*:\s*((?:Optional|List|Dict|Tuple|Union|Any)\[[^\]]*)'  # Unclosed type hint
        )
        
        # Pattern 8: Async function declaration issues
        self.async_def_re = re.compile(
            r'^(\s*)(async\s+)?def\s+(\w+)\s*\((.*?)\)\s*(->\s*[\w\[\], |]+)?\s*:?\s*$',
            re.MULTILINE
        )
        
        # Pattern 9: Decorator issues
        self.decorator_re = re.compile(
            r'^(\s*)@(\w+(?:\.\w+)*)\s*(?:\((.*?)\))?\s*$'
        )
    
    def repair_file(self, file_path: Path) -> RepairResult:
        """Repair a single Python file"
        
        self.stats["files_scanned"] += 1
        
        try:
            # Read the file
            original_content = file_path.read_text(encoding='utf-8')
            original_lines = original_content.splitlines(keepends=True)
            
            # Check if already valid
            if self._is_valid_python(original_content):
                self.logger.debug(f"File {file_path} is already valid, skipping")
                self.stats["files_skipped"] += 1
                return RepairResult(
                    file_path=file_path,
                    original_lines=original_lines,
                    repaired_lines=original_lines,
                    changes_made=[],
                    success=True
                )
            
            # Apply repairs
            repaired_lines = original_lines.copy()
            changes_made = []
            
            for i, line in enumerate(original_lines):
                repaired_line = self._repair_line(line, i, repaired_lines)
                if repaired_line != line:
                    repaired_lines[i] = repaired_line
                    changes_made.append((i + 1, line.rstrip(), repaired_line.rstrip()))
            
            # Join and validate
            repaired_content = ''.join(repaired_lines)
            
            # Additional full-content repairs
            repaired_content = self._repair_multiline_issues(repaired_content)
            
            # Validate repaired content
            if not self._is_valid_python(repaired_content):
                # Try more aggressive repairs
                repaired_content = self._aggressive_repair(repaired_content)
            
            # Final validation
            if self._is_valid_python(repaired_content):
                # Format with black (matching project style)
                try:
                    repaired_content = black.format_str(
                        repaired_content,
                        mode=black.Mode(
                            line_length=100,
                            string_normalization=True,
                            magic_trailing_comma=True
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Black formatting failed: {e}")
                
                # Write repairs if not dry run
                if not self.dry_run:
                    # Create backup
                    backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)
                    shutil.copy2(file_path, backup_path)
                    
                    # Write repaired content
                    file_path.write_text(repaired_content, encoding='utf-8')
                    self.logger.info(f"Repaired {file_path} ({len(changes_made)} changes)")
                else:
                    self.logger.info(f"Would repair {file_path} ({len(changes_made)} changes)")
                
                self.stats["files_repaired"] += 1
                self.stats["errors_fixed"] += len(changes_made)
                
                return RepairResult(
                    file_path=file_path,
                    original_lines=original_lines,
                    repaired_lines=repaired_content.splitlines(keepends=True),
                    changes_made=changes_made,
                    success=True
                )
            else:
                self.logger.error(f"Failed to repair {file_path}")
                return RepairResult(
                    file_path=file_path,
                    original_lines=original_lines,
                    repaired_lines=repaired_lines,
                    changes_made=changes_made,
                    success=False,
                    error="Repairs did not result in valid Python"
                )
                
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return RepairResult(
                file_path=file_path,
                original_lines=[],
                repaired_lines=[],
                changes_made=[],
                success=False,
                error=str(e)
            )
    
    def _repair_line(self, line: str, line_idx: int, all_lines: List[str]) -> str:
        """Repair a single line based on common patterns"
        
        original_line = line
        
        # 1. Remove invalid UTF-8 characters (but preserve in comments)
        if not line.strip().startswith('#'):
            line = self.invalid_char_re.sub('', line)
        
        # 2. Fix Pydantic Field declarations
        if 'Field(' in line:
            line = self._fix_field_declaration(line)
        
        # 3. Fix broken f-strings
        if 'f"' in line or "f'" in line:
            line = self._fix_fstring(line)
        
        # 4. Fix type hints
        if ':' in line and '=' in line and not line.strip().startswith('#'):
            line = self._fix_type_hint(line)
        
        # 5. Fix import statements
        if line.strip().startswith(('import ', 'from ')):
            line = self._fix_import(line)
        
        # 6. Fix function definitions
        if 'def ' in line:
            line = self._fix_function_def(line)
        
        # 7. Fix decorators
        if line.strip().startswith('@'):
            line = self._fix_decorator(line)
        
        return line
    
    def _fix_field_declaration(self, line: str) -> str:
        """Fix Pydantic Field declarations"
        
        # Pattern for our common Field usage
        # Example: scope1_total: Decimal = Field(alias="total_scope1", description="Total Scope 1")
        
        # Check for missing comma after alias
        line = re.sub(
            r'(Field\s*\(\s*alias\s*=\s*"[^"]*")\s+(\w+\s*=)',
            r'\1, \2',
            line
        )
        
        # Check for missing closing parenthesis
        if 'Field(' in line and line.count('(') > line.count(')'):
            # Count quotes to ensure we're not in a string
            if line.count('"') % 2 == 0:
                line = line.rstrip() + ')\n'
        
        # Fix Field with description but missing comma
        line = re.sub(
            r'(Field\s*\(\s*alias\s*=\s*"[^"]*")\s+(description\s*=)',
            r'\1, \2',
            line
        )
        
        # Fix Field with ge/le constraints (common in our numeric fields)
        line = re.sub(
            r'(Field\s*\([^)]*?)\s+(ge\s*=\s*\d+)',
            r'\1, \2',
            line
        )
        
        return line
    
    def _fix_fstring(self, line: str) -> str:
        """Fix broken f-strings"
        
        # Fix unterminated f-strings
        if line.count('"') % 2 == 1 and ('f"' in line or "f'" in line):
            # Check if it's actually broken
            try:
                ast.parse(line.strip())
            except SyntaxError:
                # Add closing quote
                if 'f"' in line and not line.rstrip().endswith('"'):
                    line = line.rstrip() + '"\n'
                elif "f'" in line and not line.rstrip().endswith("'"):
                    line = line.rstrip() + "'\n"
        
        # Fix f-strings with unclosed braces
        if match := self.broken_fstring_re.search(line):
            # Count braces
            open_braces = line.count('{') - line.count('{{')
            close_braces = line.count('}') - line.count('}}')
            
            if open_braces > close_braces:
                # Add closing braces
                line = line.rstrip() + '}' * (open_braces - close_braces)
                
                # Ensure string is also closed
                if 'f"' in line and not line.rstrip().endswith('"'):
                    line = line.rstrip() + '"\n'
        
        return line
    
    def _fix_type_hint(self, line: str) -> str:
        """Fix type hint issues"
        
        # Fix unclosed type hints like: List[str
        if match := self.type_hint_re.search(line):
            type_hint = match.group(2)
            if type_hint.count('[') > type_hint.count(']'):
                # Add closing brackets
                missing_brackets = ']' * (type_hint.count('[') - type_hint.count(']'))
                line = line.replace(type_hint, type_hint + missing_brackets)
        
        # Fix Optional without brackets: Optional str -> Optional[str]
        line = re.sub(
            r'\b(Optional|List|Dict|Set|Tuple)\s+([a-zA-Z_]\w*)\b',
            r'\1[\2]',
            line
        )
        
        return line
    
    def _fix_import(self, line: str) -> str:
        """Fix import statement issues"
        
        # Fix trailing commas in imports
        line = re.sub(
            r'(from\s+[\w.]+\s+import\s+[\w\s,]+),\s*$',
            r'\1',
            line
        )
        
        # Fix missing commas in multi-import
        # from module import ClassA ClassB -> from module import ClassA, ClassB
        line = re.sub(
            r'(from\s+[\w.]+\s+import\s+\w+)\s+(\w+)',
            r'\1, \2',
            line
        )
        
        return line
    
    def _fix_function_def(self, line: str) -> str:
        """Fix function definition issues"
        
        # Ensure colon at end of function def
        if match := self.async_def_re.match(line):
            if not line.rstrip().endswith(':'):
                line = line.rstrip() + ':\n'
        
        # Fix async def spacing
        line = re.sub(r'async\s+def', 'async def', line)
        
        return line
    
    def _fix_decorator(self, line: str) -> str:
        """Fix decorator issues"
        
        # Ensure decorators don't have trailing commas
        line = re.sub(r'(@\w+(?:\.\w+)*\([^)]*),\s*\)', r'\1)', line)
        
        return line
    
    def _repair_multiline_issues(self, content: str) -> str:
        """Repair issues that span multiple lines"
        
        # Fix unclosed triple quotes
        triple_single = content.count("'''")
        triple_double = content.count('"')
        
        if triple_single % 2 == 1:
            content += "\n'''"
        if triple_double % 2 == 1:
            content += '\n"'
        
        # Fix class definitions with our common patterns
        content = re.sub(
            r'class\s+(\w+)\s*\(\s*BaseModel\s*\)\s*:\s*\n\s*"',
            r'class \1(BaseModel):\n    "',
            content
        )
        
        # Fix our common async patterns
        content = re.sub(
            r'async\s+with\s+(\w+)\s*\(\s*\)\s+as\s+(\w+)\s*(?!:)',
            r'async with \1() as \2:',
            content
        )
        
        return content
    
    def _aggressive_repair(self, content: str) -> str:
        """More aggressive repairs when basic repairs fail"
        
        lines = content.splitlines(keepends=True)
        repaired_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                repaired_lines.append(line)
                i += 1
                continue
            
            # Try to parse this line in isolation
            try:
                ast.parse(line.strip())
                repaired_lines.append(line)
            except SyntaxError as e:
                # Apply targeted fix based on error
                if "EOL while scanning string" in str(e):
                    # Close the string
                    if '"' in line:
                        line = line.rstrip() + '"\n'
                    elif "'" in line:
                        line = line.rstrip() + "'\n"
                elif "unexpected EOF" in str(e):
                    # Likely missing closing bracket/paren
                    if line.count('(') > line.count(')'):
                        line = line.rstrip() + ')\n'
                    elif line.count('[') > line.count(']'):
                        line = line.rstrip() + ']\n'
                    elif line.count('{') > line.count('}'):
                        line = line.rstrip() + '}\n'
                
                repaired_lines.append(line)
            
            i += 1
        
        return ''.join(repaired_lines)
    
    def _is_valid_python(self, content: str) -> bool:
        """Check if content is valid Python using AST"
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
    
    def repair_directory(self, directory: Path, patterns: List[str] = None) -> List[RepairResult]:
        """Repair all Python files in a directory"
        
        if patterns is None:
            patterns = ['*.py']
        
        results = []
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip backup files
                if self.backup_suffix in str(file_path):
                    continue
                
                # Skip __pycache__
                if '__pycache__' in str(file_path):
                    continue
                
                self.logger.info(f"Processing {file_path}")
                result = self.repair_file(file_path)
                results.append(result)
                
                if self.verbose and result.changes_made:
                    self._print_diff(result)
        
        return results
    
    def _print_diff(self, result: RepairResult):
        """Print a diff of changes made"
        
        print(f"\n{'=' * 60}")
        print(f"Changes to {result.file_path}:")
        print('=' * 60)
        
        for line_no, original, repaired in result.changes_made:
            print(f"\nLine {line_no}:")
            print(f"- {original}")
            print(f"+ {repaired}")
    
    def print_summary(self):
        """Print repair summary"
        
        print("\n" + "=" * 60)
        print("REPAIR SUMMARY")
        print("=" * 60)
        print(f"Files scanned:  {self.stats['files_scanned']}")
        print(f"Files repaired: {self.stats['files_repaired']}")
        print(f"Files skipped:  {self.stats['files_skipped']}")
        print(f"Errors fixed:   {self.stats['errors_fixed']}")
        print("=" * 60)


def main():
    """Main entry point"
    
    parser = argparse.ArgumentParser(
        description="Deep repair tool for Scope 3 compliance codebase"
    )
    parser.add_argument(
        "directories",
        nargs="+",
        type=Path,
        help="Directories to repair (e.g., src/ tests/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output and diffs"
    )
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=["*.py"],
        help="File patterns to match (default: *.py)"
    )
    
    args = parser.parse_args()
    
    # Create repair tool
    repair_tool = CodebaseRepairTool(
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    # Process each directory
    all_results = []
    for directory in args.directories:
        if not directory.exists():
            print(f"Warning: {directory} does not exist, skipping")
            continue
        
        print(f"\nRepairing {directory}...")
        results = repair_tool.repair_directory(directory, args.patterns)
        all_results.extend(results)
    
    # Print summary
    repair_tool.print_summary()
    
    # Exit with error if any repairs failed
    failed_repairs = [r for r in all_results if not r.success]
    if failed_repairs:
        print(f"\n⚠️  {len(failed_repairs)} files could not be repaired:")
        for result in failed_repairs:
            print(f"  - {result.file_path}: {result.error}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
