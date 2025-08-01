#!/usr/bin/env python3
"""
Diagnose the exact syntax error at line 4840
"""

import os

def diagnose_syntax_error():
    """Find and show the exact syntax error"""
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("🔍 SYNTAX ERROR DIAGNOSIS")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Show context around line 4840
        error_line = 4840 - 1  # Convert to 0-based index
        context_start = max(0, error_line - 10)
        context_end = min(len(lines), error_line + 5)
        
        print(f"\n📍 Context around line {error_line + 1}:")
        print("-" * 60)
        
        for i in range(context_start, context_end):
            line_num = i + 1
            line = lines[i].rstrip('\n')
            
            # Highlight the error line
            if i == error_line:
                print(f">>> {line_num:4d}: {line} <<<ERROR HERE")
            else:
                print(f"    {line_num:4d}: {line}")
        
        print("-" * 60)
        
        # Analyze the error
        print("\n📊 Analysis:")
        
        if error_line < len(lines):
            error_line_content = lines[error_line].strip()
            
            if error_line_content == ") -> ET.Element:":
                print("❌ Found orphaned closing parenthesis with return type")
                print("   This line should be part of a function signature")
                
                # Look for the function definition
                func_found = False
                for i in range(error_line - 1, max(0, error_line - 50), -1):
                    if 'def create_enhanced_xbrl_tag' in lines[i]:
                        print(f"\n📍 Function definition found at line {i + 1}")
                        func_found = True
                        
                        # Check if function is properly closed
                        j = i
                        paren_count = 0
                        while j < len(lines) and j < error_line:
                            line = lines[j]
                            paren_count += line.count('(') - line.count(')')
                            j += 1
                        
                        if paren_count > 0:
                            print("   Function signature is missing closing parenthesis")
                        elif paren_count < 0:
                            print("   Function signature has extra closing parenthesis")
                        
                        break
                
                if not func_found:
                    print("   Could not find associated function definition")
            
            # Check for other syntax patterns
            elif ')' in error_line_content and '(' not in error_line_content:
                print("❌ Unmatched closing parenthesis")
            elif error_line_content.endswith(','):
                print("❌ Trailing comma might be causing issues")
        
        # Quick fix suggestion
        print("\n🔧 Quick fix:")
        print("1. Delete line 4840 (the orphaned ') -> ET.Element:' line)")
        print("2. Find the create_enhanced_xbrl_tag function definition")
        print("3. Ensure the function signature is properly closed")
        
        # Show how to fix manually
        print("\n📝 Manual fix command:")
        print(f"sed -i '4840d' {file_path}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

def quick_fix_syntax():
    """Apply a quick fix for the syntax error"""
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("\n\n🔧 APPLYING QUICK FIX")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove line 4840 if it's the problematic line
        if len(lines) >= 4840:
            error_line = lines[4839]  # 0-based index
            if error_line.strip() == ") -> ET.Element:":
                lines.pop(4839)
                print(f"✅ Removed orphaned line: {error_line.strip()}")
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                print("✅ File updated!")
                
                # Try to compile
                import py_compile
                try:
                    py_compile.compile(file_path, doraise=True)
                    print("✅ File now compiles successfully!")
                except py_compile.PyCompileError as e:
                    print(f"⚠️ Still has compilation errors: {e}")
            else:
                print(f"⚠️ Line 4840 is not the expected error: {error_line.strip()}")
        else:
            print("⚠️ File has fewer than 4840 lines")
            
    except Exception as e:
        print(f"❌ Error applying fix: {e}")

if __name__ == "__main__":
    diagnose_syntax_error()
    
    response = input("\n\nApply quick fix? (y/n): ")
    if response.lower() == 'y':
        quick_fix_syntax()
    
    print("\n✅ Done!")