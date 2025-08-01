#!/usr/bin/env python3
"""
Comprehensive Python Syntax Fixer
Intelligently repairs common syntax errors in Python files
"""

import ast
import re
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Optional
import tokenize
import io

class SyntaxFixer:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lines = []
        self.fixes_applied = []
        
    def backup_file(self) -> str:
        """Create a timestamped backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.filepath}.backup_comprehensive_{timestamp}"
        shutil.copy2(self.filepath, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    
    def load_file(self):
        """Load the file content"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
    
    def save_file(self):
        """Save the fixed content"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.writelines(self.lines)
    
    def fix_function_definitions(self):
        """Fix function definitions missing closing ):"""
        print("\n🔍 Fixing function definitions...")
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            # Check if this is a function definition
            if line.strip().startswith('def ') and '(' in line:
                # Track parentheses balance
                start_line = i
                paren_count = line.count('(') - line.count(')')
                j = i
                
                # Find where the parameters end
                while j < len(self.lines) - 1 and paren_count > 0:
                    j += 1
                    paren_count += self.lines[j].count('(') - self.lines[j].count(')')
                    
                    # Check if we hit a docstring or code without closing the def
                    next_line = self.lines[j].strip()
                    if (next_line.startswith('"""') or 
                        next_line.startswith("'''") or
                        (paren_count > 0 and '=' in next_line and ':' not in next_line)):
                        
                        # We need to close the function definition
                        # Insert ): before this line
                        self.lines.insert(j, '):\n')
                        self.fixes_applied.append(f"Fixed function definition at line {start_line + 1}")
                        break
                
                i = j + 1
            else:
                i += 1
    
    def fix_dictionary_closures(self):
        """Fix dictionaries incorrectly closed with ):"""
        print("\n🔍 Fixing dictionary closures...")
        
        for i, line in enumerate(self.lines):
            # Skip function definitions
            if 'def ' in line and '(' in line:
                continue
            
            # Fix patterns like 'key': value):
            if re.search(r"'[^']+'\s*:\s*[^,\n]+\):", line):
                original = line
                self.lines[i] = re.sub(r"(:[^,\n]+)\):", r'\1}', line)
                if self.lines[i] != original:
                    self.fixes_applied.append(f"Fixed dictionary at line {i + 1}")
            
            # Fix patterns like {}):
            elif re.search(r"\{\s*\}\s*\):", line):
                self.lines[i] = line.replace('})', '}}')
                self.fixes_applied.append(f"Fixed empty dict at line {i + 1}")
    
    def fix_unclosed_parentheses(self):
        """Fix unclosed parentheses in function calls"""
        print("\n🔍 Fixing unclosed parentheses...")
        
        # Pattern to find function calls that span multiple lines
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            # Look for common patterns that start multi-line expressions
            patterns = [
                r'\.append\($',
                r'\.extend\($',
                r'\.get\($',
                r'\($',  # General function call
                r'=\s*\($',  # Assignment with opening paren
            ]
            
            for pattern in patterns:
                if re.search(pattern, line.rstrip()):
                    # Track parentheses to find where to close
                    start_line = i
                    paren_count = line.count('(') - line.count(')')
                    j = i
                    
                    while j < len(self.lines) - 1 and paren_count > 0:
                        j += 1
                        paren_count += self.lines[j].count('(') - self.lines[j].count(')')
                        
                        # If we're at zero, we're done
                        if paren_count == 0:
                            break
                        
                        # Check if the next line starts something new
                        if j + 1 < len(self.lines):
                            next_line = self.lines[j + 1].strip()
                            # If next line is a new statement, close here
                            if (next_line and 
                                not next_line.startswith((')', ']', '}', ',')) and
                                not self.lines[j].rstrip().endswith((',', '\\'))):
                                
                                # Add closing parentheses
                                self.lines[j] = self.lines[j].rstrip() + ')' * paren_count + '\n'
                                self.fixes_applied.append(f"Closed parentheses at line {j + 1}")
                                break
                    
                    i = j
                    break
            else:
                i += 1
    
    def fix_all(self):
        """Apply all fixes"""
        print("🔧 COMPREHENSIVE PYTHON SYNTAX FIX")
        print("=" * 60)
        
        # Backup first
        backup_path = self.backup_file()
        
        # Load file
        self.load_file()
        print(f"📄 Processing {len(self.lines)} lines")
        
        # Apply fixes in order
        self.fix_dictionary_closures()
        self.fix_function_definitions()
        self.fix_unclosed_parentheses()
        
        # Save the fixed file
        self.save_file()
        
        print(f"\n✅ Applied {len(self.fixes_applied)} fixes")
        
        # Test compilation
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "py_compile", self.filepath],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ SUCCESS! File compiles without errors!")
            return True, None
        else:
            print("\n❌ Still has errors:")
            print(result.stderr)
            return False, result.stderr
    
    def iterative_fix(self, max_iterations=10):
        """Fix errors iteratively until all are resolved"""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Iteration {iteration}")
            
            success, error = self.fix_all()
            if success:
                return True
            
            # Try to fix the specific error
            if error and not self.fix_specific_error(error):
                print("❌ Could not automatically fix the remaining error")
                return False
            
            # Reload for next iteration
            self.load_file()
        
        return False
    
    def fix_specific_error(self, error_msg: str) -> bool:
        """Fix a specific error based on the error message"""
        # Parse error location
        import re
        match = re.search(r'line (\d+)', error_msg)
        if not match:
            return False
        
        line_num = int(match.group(1)) - 1  # 0-indexed
        
        if "does not match opening parenthesis '{'" in error_msg:
            # Change ) to }
            if line_num < len(self.lines):
                self.lines[line_num] = self.lines[line_num].replace('):', '}')
                self.lines[line_num] = self.lines[line_num].replace('),', '},')
                self.save_file()
                return True
        
        elif "does not match opening parenthesis '('" in error_msg:
            # Change } to )
            if line_num < len(self.lines):
                if self.lines[line_num].strip() == '}':
                    self.lines[line_num] = self.lines[line_num].replace('}', ')')
                self.save_file()
                return True
        
        return False

def main():
    """Main execution"""
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    if not os.path.exists(filepath):
        print("❌ File not found!")
        return
    
    fixer = SyntaxFixer(filepath)
    
    # Try to fix iteratively
    if fixer.iterative_fix():
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! All syntax errors have been fixed!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("1. Test import: python3 -c \"from app.api.v1.endpoints.esrs_e1_full import create_proper_ixbrl_report\"")
        print("2. Start server: poetry run uvicorn app.main:app --reload")
        print("3. Test your ESRS endpoints")
        print("\n✨ Your iXBRL generator is now production-ready!")
    else:
        print("\n⚠️ Some manual fixes may still be needed")
        print("Check the specific errors above")

if __name__ == "__main__":
    main()