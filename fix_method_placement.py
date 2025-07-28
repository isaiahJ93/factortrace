#!/usr/bin/env python3
"""
Fix method placement in pdf-export-handler.ts
"""

import os
import shutil
from datetime import datetime
import re

def analyze_and_fix_structure(file_path):
    """Analyze class structure and fix method placement"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    print("🔍 Analyzing class structure...")
    
    # Find the PDFExportHandler class
    class_start = None
    class_end = None
    
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_start = i
            print(f"✅ Found class start at line {i + 1}")
        
        # Look for where our ESRS methods were inserted
        if '// ESRS E1 Enhanced Section Methods' in line:
            esrs_methods_line = i
            print(f"📍 Found ESRS methods at line {i + 1}")
            
            # Check if this is inside the class
            # Count braces from class start to this point
            if class_start:
                content_to_check = '\n'.join(lines[class_start:i])
                open_count = content_to_check.count('{')
                close_count = content_to_check.count('}')
                
                if open_count <= close_count:
                    print(f"❌ ERROR: ESRS methods are OUTSIDE the class!")
                    print(f"   Brace count from class start: {open_count} open, {close_count} close")
                    
                    # Find the correct insertion point (last method before class end)
                    # Look for the pattern of the last private method
                    correct_insertion = None
                    
                    for j in range(i-1, class_start, -1):
                        if re.search(r'^\s*private\s+\w+.*\{', lines[j]):
                            # Found a method start, now find its end
                            method_brace_count = 0
                            for k in range(j, i):
                                if '{' in lines[k]:
                                    method_brace_count += lines[k].count('{')
                                if '}' in lines[k]:
                                    method_brace_count -= lines[k].count('}')
                                if method_brace_count == 0 and k > j:
                                    correct_insertion = k + 1
                                    print(f"✅ Found correct insertion point after line {k + 1}")
                                    break
                            if correct_insertion:
                                break
                    
                    if correct_insertion and correct_insertion < esrs_methods_line:
                        print("🔧 Moving methods to correct location...")
                        
                        # Extract the ESRS methods
                        esrs_start = esrs_methods_line - 1  # Include empty line before
                        esrs_end = len(lines) - 1
                        
                        # Find the end of ESRS methods (before class closing or next section)
                        for j in range(esrs_start, len(lines)):
                            if j > esrs_start + 10 and (
                                re.search(r'^\s*}\s*$', lines[j]) and 
                                j + 1 < len(lines) and 
                                ('export' in lines[j+1] or not lines[j+1].strip())
                            ):
                                esrs_end = j
                                break
                        
                        # Extract methods
                        esrs_methods = lines[esrs_start:esrs_end]
                        
                        # Remove from current location
                        del lines[esrs_start:esrs_end]
                        
                        # Insert at correct location
                        for idx, method_line in enumerate(esrs_methods):
                            lines.insert(correct_insertion + idx, method_line)
                        
                        # Save the fixed file
                        fixed_content = '\n'.join(lines)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        
                        print("✅ Methods moved to correct location inside the class")
                        return True
                else:
                    print("✅ ESRS methods are correctly inside the class")
    
    # If we get here, check for other issues
    print("\n🔍 Checking for other syntax issues...")
    
    # Look for the specific error line
    if len(lines) > 1674:
        error_line = lines[1674]  # Line 1675 in 1-indexed
        print(f"\nError line content: {error_line}")
        
        # Check if there's a missing semicolon or brace before this line
        prev_line = lines[1673] if len(lines) > 1673 else ""
        if prev_line.strip() and not prev_line.strip().endswith(('{', '}', ';', '*/', ':')):
            print(f"⚠️  Previous line might be missing punctuation: {prev_line.strip()}")
    
    return False

def main():
    """Main function"""
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        try:
            os.chdir(expected_dir)
        except Exception as e:
            print(f"❌ Could not change directory: {e}")
            return
    
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Processing: {file_path}")
    
    # Create backup
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    try:
        # Analyze and fix structure
        success = analyze_and_fix_structure(file_path)
        
        if success:
            print("\n✨ Structure fixed!")
            print("Try building again: npm run dev")
        else:
            print("\n⚠️  Manual intervention may be needed")
            print("The methods appear to be in the correct location.")
            print("\nPossible issues:")
            print("1. Check if 'DESIGN' constant is defined")
            print("2. Check if all type imports are correct")
            print("3. Try running: npx tsc --noEmit to see all TypeScript errors")
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()