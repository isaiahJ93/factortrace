#!/usr/bin/env python3
"""
Surgical fix for specific syntax errors in esrs_e1_full.py
Targets exact line numbers from error messages
"""

import os
import shutil
from datetime import datetime

def fix_syntax_errors():
    """Fix specific syntax errors blocking production"""
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("🔧 SURGICAL SYNTAX FIX")
    print("=" * 60)
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_surgical_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup: {backup_path}")
    
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 File has {len(lines)} lines")
    
    # FIX 1: Line 4946 - Unmatched ')'
    print("\n🔍 Fix 1: Line 4946 - Unmatched ')'")
    if len(lines) > 4945:
        if lines[4945].strip() == ") -> ET.Element:":
            lines[4945] = ""  # Remove the line
            print("✅ Removed orphaned function signature at line 4946")
    
    # FIX 2: Line 4308 - Indentation error
    print("\n🔍 Fix 2: Line 4308 - Indentation error")
    if len(lines) > 4307:
        # Check line 4307 for if statement
        if "if" in lines[4306] and "raise ValueError" in lines[4307]:
            # Fix indentation
            lines[4307] = "        " + lines[4307].lstrip()
            print("✅ Fixed indentation at line 4308")
    
    # FIX 3: Line 8338 - Unclosed function
    print("\n🔍 Fix 3: Line 8338 - Unclosed function")
    if len(lines) > 8337:
        line_content = lines[8337].strip()
        if line_content == "def create_enhanced_xbrl_tag(":
            # Find the end of parameters and close it
            for i in range(8338, min(8348, len(lines))):
                if i < len(lines):
                    if ") ->" in lines[i] or "):" in lines[i]:
                        break
                    elif i == 8347:  # Safety - close it after 10 lines
                        lines[i] = lines[i].rstrip() + "):\n"
                        lines.insert(i + 1, "    \"\"\"Create enhanced XBRL tag\"\"\"\n")
                        lines.insert(i + 2, "    pass\n")
                        print(f"✅ Closed function at line {i+1}")
                        break
    
    # FIX 4: Remove any other orphaned ") -> ET.Element:" lines
    print("\n🔍 Fix 4: Removing all orphaned signatures")
    removed_count = 0
    i = 0
    while i < len(lines):
        if lines[i].strip() == ") -> ET.Element:":
            del lines[i]
            removed_count += 1
        else:
            i += 1
    print(f"✅ Removed {removed_count} orphaned signatures")
    
    # FIX 5: Add proper create_enhanced_xbrl_tag if missing
    print("\n🔍 Fix 5: Ensuring create_enhanced_xbrl_tag exists")
    has_function = any("def create_enhanced_xbrl_tag(" in line for line in lines)
    
    if not has_function:
        # Find a good place to insert (after imports)
        insert_pos = 0
        for i, line in enumerate(lines):
            if "from" in line or "import" in line:
                insert_pos = i + 1
        
        function_code = '''
def create_enhanced_xbrl_tag(
    parent,
    tag_name,
    value,
    context_ref,
    unit_ref=None,
    decimals=None,
    fact_id=None,
    escape=True
):
    """Create XBRL tag with proper namespacing"""
    import xml.etree.ElementTree as ET
    
    # Create the element
    elem = ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}nonFraction")
    elem.set("contextRef", context_ref)
    elem.set("name", f"esrs:{tag_name}")
    
    if unit_ref:
        elem.set("unitRef", unit_ref)
    if decimals is not None:
        elem.set("decimals", str(decimals))
    if fact_id:
        elem.set("id", fact_id)
    
    # Handle numeric formatting
    try:
        float(str(value).replace(',', ''))
        elem.set("format", "ixt:numdotdecimal")
    except:
        pass
    
    elem.text = str(value)
    return elem

'''
        lines.insert(insert_pos, function_code)
        print("✅ Added create_enhanced_xbrl_tag implementation")
    
    # Write fixed file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n🔍 Verifying syntax...")
    try:
        compile(''.join(lines), filepath, 'exec')
        print("✅ File compiles successfully!")
        return True
    except SyntaxError as e:
        print(f"❌ Still has error at line {e.lineno}: {e.msg}")
        if e.text:
            print(f"   Problem: {e.text.strip()}")
        return False
    except Exception as e:
        print(f"❌ Compilation error: {e}")
        return False

def quick_compile_check():
    """Quick syntax check"""
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "py_compile", "app/api/v1/endpoints/esrs_e1_full.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ File compiles!")
        return True
    else:
        print("❌ Compilation errors:")
        print(result.stderr)
        return False

def main():
    """Run the fix"""
    if not os.path.exists("app/api/v1/endpoints/esrs_e1_full.py"):
        print("❌ File not found!")
        return
    
    # Apply fixes
    success = fix_syntax_errors()
    
    if success:
        print("\n✅ ALL SYNTAX ERRORS FIXED!")
        print("\n📋 Next steps:")
        print("1. Restart FastAPI: pkill -f uvicorn && poetry run uvicorn app.main:app --reload")
        print("2. Test the API endpoint")
        print("3. Run: python3 fix_xml_duplicate_attr.py (for testing)")
    else:
        print("\n⚠️ Manual check needed")
        quick_compile_check()

if __name__ == "__main__":
    main()