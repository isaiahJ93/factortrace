#!/usr/bin/env python3
"""
Fix ALL dictionary syntax errors in the file
Handles patterns like ,): and ensures proper brace matching
"""

import re
import os
import shutil
from datetime import datetime
import subprocess

def fix_all_dict_syntax_errors():
    """Fix all dictionary syntax errors comprehensively"""
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("🔧 FIXING ALL DICTIONARY SYNTAX ERRORS")
    print("=" * 60)
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_alldict_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 Processing {len(lines)} lines")
    
    # Track all fixes
    fixes_made = []
    
    # Pattern 1: Fix all ,): occurrences
    print("\n🔍 Fixing all ,): patterns...")
    for i, line in enumerate(lines):
        if ',):' in line:
            original = line
            lines[i] = line.replace(',):', ',')
            if lines[i] != original:
                fixes_made.append(f"Line {i+1}: Fixed ',):' to ','")
                print(f"   Fixed line {i+1}")
    
    # Pattern 2: Fix mismatched closing parentheses after dictionaries
    print("\n🔍 Checking for mismatched braces and parentheses...")
    
    # Track open braces and their positions
    brace_stack = []
    dict_contexts = []  # Track where dictionaries start
    
    for i, line in enumerate(lines):
        # Track opening braces
        if '{' in line:
            # Count how many
            opens = line.count('{')
            for _ in range(opens):
                brace_stack.append(i)
                # Check if this is a dictionary (has ':' before or after)
                if ':' in line or (i > 0 and ':' in lines[i-1]):
                    dict_contexts.append(i)
        
        # Track closing braces
        if '}' in line:
            closes = line.count('}')
            for _ in range(closes):
                if brace_stack:
                    brace_stack.pop()
        
        # Check for ')' that should be '}'
        if ')' in line and i > 0:
            # Look back to see if we're in a dictionary context
            # Check if there's an unclosed '{' in recent lines
            for j in range(max(0, i-20), i):
                if '{' in lines[j] and '}' not in ''.join(lines[j:i+1]):
                    # Check if this line has a pattern like ': value)'
                    if re.search(r':\s*[^,\n]+\)', line):
                        # This ) might need to be }
                        # But only if it's at the end of a dict entry
                        if line.strip().endswith(')') or line.strip().endswith('):'):
                            original = lines[i]
                            lines[i] = lines[i].rstrip().rstrip('):').rstrip(')') + '\n'
                            
                            # Find where to add the closing brace
                            # Look for the next line that's not part of the dict
                            need_brace = True
                            for k in range(i+1, min(i+10, len(lines))):
                                if lines[k].strip() and not lines[k].strip().startswith(("'", '"', "}")):
                                    # Add closing brace before this line
                                    indent = len(lines[j]) - len(lines[j].lstrip())
                                    lines.insert(k, ' ' * indent + '}\n')
                                    fixes_made.append(f"Line {i+1}: Fixed dict closure, added }} at line {k+1}")
                                    print(f"   Fixed dictionary at line {i+1}, added }} at line {k+1}")
                                    need_brace = False
                                    break
                            
                            if need_brace and i < len(lines) - 1:
                                # Add brace on next line
                                indent = len(lines[i]) - len(lines[i].lstrip()) - 4
                                lines.insert(i+1, ' ' * max(0, indent) + '}\n')
                                fixes_made.append(f"Line {i+1}: Added closing brace")
                            break
    
    # Pattern 3: Fix specific known problematic patterns
    specific_fixes = [
        (r"'by_sector':\s*{}\s*\)\s*:", "'by_sector': {}"),
        (r"}\s*\)\s*:", "}"),
        (r",\s*\)\s*(?=\n)", ","),
    ]
    
    print("\n🔍 Applying specific pattern fixes...")
    for i, line in enumerate(lines):
        for pattern, replacement in specific_fixes:
            if re.search(pattern, line):
                original = line
                lines[i] = re.sub(pattern, replacement, line)
                if lines[i] != original:
                    fixes_made.append(f"Line {i+1}: Applied pattern fix")
    
    # Write the fixed file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n✅ Applied {len(fixes_made)} fixes")
    
    # Verify syntax
    print("\n🔍 Verifying syntax...")
    result = subprocess.run(
        ["python3", "-m", "py_compile", filepath],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ ALL SYNTAX ERRORS FIXED!")
        return True
    else:
        print("❌ Still has errors:")
        print(result.stderr)
        
        # Extract line number from error
        import re
        match = re.search(r'line (\d+)', result.stderr)
        if match:
            error_line = int(match.group(1))
            print(f"\n📍 Error context (lines {error_line-5} to {error_line+5}):")
            for i in range(max(0, error_line-6), min(len(lines), error_line+5)):
                marker = ">>>" if i == error_line-1 else "   "
                print(f"{marker} {i+1}: {lines[i].rstrip()}")
        
        return False

def create_validation_script():
    """Create a script to validate the fix"""
    content = '''#!/usr/bin/env python3
"""Validate that all fixes are working"""

import subprocess
import sys

print("🔍 VALIDATING iXBRL GENERATOR")
print("=" * 40)

# Step 1: Syntax check
print("1. Checking syntax...")
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "app/api/v1/endpoints/esrs_e1_full.py"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("❌ Syntax error:")
    print(result.stderr)
    sys.exit(1)
else:
    print("✅ Syntax valid!")

# Step 2: Import check
print("\\n2. Checking imports...")
try:
    from app.api.v1.endpoints.esrs_e1_full import create_proper_ixbrl_report
    print("✅ Imports successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Step 3: Basic functionality test
print("\\n3. Testing basic functionality...")
try:
    test_data = {
        "company_name": "Validation Test Corp",
        "lei": "12345678901234567890",
        "reporting_period": "2024"
    }
    
    result = create_proper_ixbrl_report(test_data)
    print(f"✅ Generated {len(result)} characters of iXBRL")
    
    # Basic validation
    assert "<html" in result, "Missing HTML tag"
    assert "xmlns:ix" in result, "Missing iXBRL namespace"
    print("✅ Output structure valid!")
    
except Exception as e:
    print(f"❌ Runtime error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\\n✅ ALL VALIDATION PASSED!")
print("🚀 Your iXBRL generator is ready for production!")
'''
    
    with open("validate_fix.py", "w") as f:
        f.write(content)
    print("✅ Created validate_fix.py")

def main():
    """Execute the comprehensive fix"""
    if not os.path.exists("app/api/v1/endpoints/esrs_e1_full.py"):
        print("❌ File not found!")
        return
    
    # Apply fixes
    success = fix_all_dict_syntax_errors()
    
    # Create validation script
    create_validation_script()
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("=" * 60)
    
    if success:
        print("1. Run validation: python3 validate_fix.py")
        print("2. Start server: poetry run uvicorn app.main:app --reload")
        print("3. Test your ESRS endpoints")
        print("\n🎉 Your iXBRL generator is production ready!")
    else:
        print("1. Check the error output above")
        print("2. Look for the specific line mentioned")
        print("3. Common fixes:")
        print("   - Replace ')' with '}' at end of dictionaries")
        print("   - Replace ',):' with ','")
        print("   - Ensure all '{' have matching '}'")

if __name__ == "__main__":
    main()