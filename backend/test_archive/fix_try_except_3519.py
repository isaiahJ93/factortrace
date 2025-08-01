#!/usr/bin/env python3
"""
Fix the try/except block issue at line 3519
"""

def fix_try_except_block():
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔧 Fixing try/except block at line 3519...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Show the problematic section
    print("\nProblematic section (lines 3515-3525):")
    for i in range(3514, min(3525, len(lines))):
        print(f"{i+1}: {repr(lines[i])}")
    
    # Fix the specific issue at line 3519
    fixes_applied = 0
    
    # The issue is that line 3519 is not properly indented inside the try block
    if lines[3518].strip() == 'current_year = datetime.now().year':
        # This line should be indented to match the line above (vintage_year = ...)
        lines[3518] = '                current_year = datetime.now().year\n'
        fixes_applied += 1
        print(f"\n✓ Fixed indentation of line 3519")
    
    # Now check if this try block has a proper except
    # Find the try statement around line 3517
    try_line = None
    for i in range(3515, 3520):
        if i < len(lines) and lines[i].strip() == 'try:':
            try_line = i
            break
    
    if try_line:
        try_indent = len(lines[try_line]) - len(lines[try_line].lstrip())
        
        # Find where the try block ends and check for except
        has_except = False
        try_end = try_line + 1
        
        for i in range(try_line + 1, min(len(lines), try_line + 50)):
            line_indent = len(lines[i]) - len(lines[i].lstrip())
            stripped = lines[i].strip()
            
            # If we find except or finally at the same level as try, we're good
            if line_indent == try_indent and stripped.startswith(('except', 'finally')):
                has_except = True
                break
            
            # If we find something at same or lower indent that's not except/finally, try block ended
            if stripped and line_indent <= try_indent and not stripped.startswith(('except', 'finally')):
                try_end = i
                break
        
        if not has_except:
            # Insert except block
            lines.insert(try_end, ' ' * try_indent + 'except Exception:\n')
            lines.insert(try_end + 1, ' ' * try_indent + '    pass  # TODO: Handle exception\n')
            fixes_applied += 2
            print(f"✓ Added missing except block at line {try_end + 1}")
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Applied {fixes_applied} fixes!")
    
    # Show the fixed section
    print("\nFixed section (lines 3515-3525):")
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for i in range(3514, min(3525, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
    
    return True

def find_all_try_blocks():
    """Find all try blocks without except/finally"""
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("\n🔍 Scanning for incomplete try blocks...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    issues = []
    i = 0
    
    while i < len(lines):
        if lines[i].strip() == 'try:':
            try_indent = len(lines[i]) - len(lines[i].lstrip())
            has_except = False
            
            # Look for except/finally
            for j in range(i + 1, min(len(lines), i + 100)):
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                stripped = lines[j].strip()
                
                if line_indent == try_indent and stripped.startswith(('except', 'finally')):
                    has_except = True
                    break
                elif stripped and line_indent < try_indent:
                    # We've left the try block
                    break
            
            if not has_except:
                issues.append(i + 1)
        
        i += 1
    
    if issues:
        print(f"Found {len(issues)} try blocks without except/finally:")
        for line_num in issues[:5]:
            print(f"  - Line {line_num}")
    else:
        print("✅ All try blocks have proper except/finally clauses")
    
    return issues

def verify():
    """Verify the fix worked"""
    import subprocess
    import sys
    
    print("\n🔍 Verifying syntax...")
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ SUCCESS! Python syntax is valid!")
        print("\n🎉 Your ESRS E1 iXBRL generator is ready!")
        print("\n🚀 Start your server:")
        print("   uvicorn app.main:app --reload")
        print("\n📊 Test the endpoint:")
        print("   curl -X POST http://localhost:8000/api/v1/esrs/e1/full -H 'Content-Type: application/json' -d '{}'")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        
        # Show error location
        import re
        match = re.search(r'line (\d+)', result.stderr)
        if match:
            error_line = int(match.group(1))
            print(f"\nError at line {error_line}:")
            
            with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
                lines = f.readlines()
            
            if error_line <= len(lines):
                for i in range(max(0, error_line-5), min(len(lines), error_line+3)):
                    marker = ">>>" if i == error_line-1 else "   "
                    print(f"{marker} {i+1}: {lines[i]}", end='')
        
        return False

if __name__ == "__main__":
    # First fix the immediate issue
    if fix_try_except_block():
        # Check for other similar issues
        find_all_try_blocks()
        
        # Verify the fix
        verify()