#!/usr/bin/env python3
"""
Complete fix process - run everything in order
"""

import os
import subprocess
import sys

def run_step(description, command):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        if isinstance(command, str):
            # For Python scripts
            result = subprocess.run([sys.executable, command], capture_output=True, text=True)
        else:
            # For shell commands
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔧 COMPLETE iXBRL FIX PROCESS")
    print("="*60)
    
    steps = [
        ("Testing basic iXBRL generation", "minimal_ixbrl_test.py"),
        ("Creating fixed minimal test", "fix_minimal_test.py"),
        ("Verifying fixed minimal test", ["python3", "verify_ixbrl.py", "minimal_fixed.xhtml"]),
        ("Cleaning and fixing main function", "clean_fix_function.py"),
        ("Testing with valid data", "test_with_valid_lei.py"),
    ]
    
    success_count = 0
    for desc, cmd in steps:
        if run_step(desc, cmd):
            success_count += 1
            print("✅ Step completed successfully")
        else:
            print("⚠️  Step had issues but continuing...")
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL SUMMARY: {success_count}/{len(steps)} steps successful")
    
    # Check for output files
    print("\n📁 Generated files:")
    files_to_check = [
        "minimal_test.xhtml",
        "minimal_fixed.xhtml", 
        "esrs_fixed_output.xhtml",
        "esrs_report_world_class.xhtml"
    ]
    
    found_files = []
    for f in files_to_check:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"   ✅ {f} ({size:,} bytes)")
            found_files.append(f)
        else:
            print(f"   ❌ {f} (not found)")
    
    # Test the most recent ESRS file
    if found_files:
        latest = max([f for f in found_files if 'esrs' in f], 
                    key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
        
        print(f"\n🔍 Checking latest ESRS file: {latest}")
        
        with open(latest, 'r') as f:
            content = f.read()
        
        import re
        fractions = len(re.findall(r'<ix:nonFraction', content))
        numerics = len(re.findall(r'<ix:nonNumeric', content))
        
        print(f"   ix:nonFraction tags: {fractions}")
        print(f"   ix:nonNumeric tags: {numerics}")
        
        if fractions > 0 or numerics > 0:
            print(f"\n✅ SUCCESS! {latest} contains iXBRL tags!")
            print(f"   Run: python3 verify_ixbrl.py {latest}")
        else:
            print("\n❌ No iXBRL tags found in output")
            print("\nDebug steps:")
            print("1. Check if create_enhanced_xbrl_tag is defined correctly")
            print("2. Verify it's being called with 'nonFraction' or 'nonNumeric'")
            print("3. Make sure the function sets elem.text")

if __name__ == "__main__":
    main()