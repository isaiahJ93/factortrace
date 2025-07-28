#!/usr/bin/env python3
"""Better test summary."""
import subprocess
import sys
import re

print("=" * 70)
print("XPath31 Elite XBRL Validator - Test Suite Summary")
print("=" * 70)

# Run pytest with JSON output for better parsing
result = subprocess.run(
    [sys.executable, "-m", "pytest", "xpath31/tests/", "-v", "--tb=short", "-k", "not (final_integration or tsl_validation)"],
    capture_output=True,
    text=True
)

output = result.stdout + result.stderr

# Parse test results
passed = len(re.findall(r'PASSED', output))
failed = len(re.findall(r'FAILED', output))
skipped = len(re.findall(r'SKIPPED', output))
errors = len(re.findall(r'ERROR', output))

# Find individual test results
test_lines = [line for line in output.split('\n') if '::' in line and ('PASSED' in line or 'FAILED' in line)]

print("\nTest Results by File:")
print("-" * 70)

current_file = None
for line in test_lines:
    if '::' in line:
        parts = line.split('::')
        file_part = parts[0].strip()
        test_part = parts[1].strip() if len(parts) > 1 else ""
        
        # Extract just the filename
        if '/' in file_part:
            filename = file_part.split('/')[-1]
        else:
            filename = file_part
            
        if filename != current_file:
            current_file = filename
            print(f"\n{filename}:")
            
        # Extract test name and result
        if 'PASSED' in test_part:
            status = "✅ PASS"
        elif 'FAILED' in test_part:
            status = "❌ FAIL"
        else:
            status = "⚠️  UNKNOWN"
            
        test_name = test_part.split()[0]
        print(f"  {status} {test_name}")

print("\n" + "-" * 70)
print(f"Summary: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
print("=" * 70)

# Show any error details
if errors > 0:
    print("\nErrors encountered:")
    error_lines = [line for line in output.split('\n') if 'ImportError' in line or 'ModuleNotFoundError' in line]
    for line in error_lines[:5]:  # Show first 5 errors
        print(f"  - {line.strip()}")
