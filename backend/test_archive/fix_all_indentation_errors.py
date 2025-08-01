#!/usr/bin/env python3
"""
Fix all indentation errors in the ESRS E1 file
"""

def fix_all_indentation_errors(filepath="app/api/v1/endpoints/esrs_e1_full.py"):
    print("🔧 Fixing all indentation errors...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    fixed_count = 0
    
    # Look for patterns where 'if' statements are followed by unindented code
    for i in range(len(lines) - 1):
        current_line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        
        # Check if current line is an if statement
        if current_line.strip().startswith('if ') and current_line.strip().endswith(':'):
            # Get the indentation of the if statement
            if_indent = len(current_line) - len(current_line.lstrip())
            
            # Check if next non-empty line has proper indentation
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            
            if j < len(lines) and lines[j].strip():
                next_indent = len(lines[j]) - len(lines[j].lstrip())
                
                # The next line should be indented more than the if statement
                if next_indent <= if_indent:
                    # Fix it - add 4 spaces
                    lines[j] = ' ' * (if_indent + 4) + lines[j].strip() + '\n'
                    print(f"Fixed indentation at line {j + 1}: {lines[j].strip()[:60]}...")
                    fixed_count += 1
    
    # Save the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Fixed {fixed_count} indentation errors")
    
    # Test syntax
    import subprocess
    import time
    
    # Give the file system a moment to sync
    time.sleep(0.1)
    
    result = subprocess.run(['python3', '-m', 'py_compile', filepath], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SYNTAX IS VALID!")
        return True
    else:
        # Try to extract the specific error
        if result.stderr:
            for line in result.stderr.split('\n'):
                if 'line' in line.lower():
                    print(f"❌ Still has error: {line}")
        return False

if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "app/api/v1/endpoints/esrs_e1_full.py"
    
    # Keep trying until all errors are fixed (max 5 attempts)
    attempts = 0
    while attempts < 5:
        attempts += 1
        print(f"\n--- Attempt {attempts} ---")
        
        if fix_all_indentation_errors(filepath):
            print("\n🎉 Success! All syntax errors fixed!")
            print("\n🧪 Your iXBRL generator is ready to test!")
            break
        
        if attempts >= 5:
            print("\n❌ Max attempts reached. Manual intervention needed.")
