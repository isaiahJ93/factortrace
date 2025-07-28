#!/usr/bin/env python3
"""
Diagnose syntax error in pdf-export-handler.ts
"""

import os

def diagnose_error(file_path):
    """Show context around the error line"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Show context around line 1675
    error_line = 1675
    start = max(0, error_line - 10)
    end = min(len(lines), error_line + 10)
    
    print(f"\n📋 Context around line {error_line}:")
    print("=" * 80)
    
    for i in range(start, end):
        marker = ">>>" if i == error_line - 1 else "   "
        print(f"{marker} {i + 1:4d}: {lines[i].rstrip()}")
    
    print("=" * 80)
    
    # Check for common issues
    print("\n🔍 Checking for common issues:")
    
    # Check brace balance
    content = ''.join(lines)
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"Brace balance: {open_braces} open, {close_braces} close")
    
    if open_braces != close_braces:
        print(f"⚠️  Unbalanced braces! Missing {abs(open_braces - close_braces)} {'closing' if open_braces > close_braces else 'opening'} brace(s)")
    
    # Check the specific method
    method_start = None
    for i, line in enumerate(lines):
        if 'private addDataQualitySection' in line:
            method_start = i
            break
    
    if method_start:
        print(f"\n📍 Found addDataQualitySection at line {method_start + 1}")
        # Show the method signature
        for i in range(method_start, min(method_start + 5, len(lines))):
            print(f"    {i + 1:4d}: {lines[i].rstrip()}")

def main():
    """Main function"""
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        os.chdir(expected_dir)
    
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    diagnose_error(file_path)

if __name__ == "__main__":
    main()