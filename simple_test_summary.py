#!/usr/bin/env python3
"""Simple test summary."""
import subprocess
import os

print("=" * 60)
print("XPath31 Test Summary")
print("=" * 60)

# Run pytest and get results
result = subprocess.run(
    ["python", "-m", "pytest", "xpath31/tests/", "-v", "--tb=no"],
    capture_output=True,
    text=True
)

output = result.stdout + result.stderr

# Simple counts
if "passed" in output:
    print("✅ Tests are running")
    
    # Extract the summary line
    for line in output.split('\n'):
        if 'passed' in line and ('failed' in line or 'skipped' in line):
            print(f"\nTest Results: {line.strip()}")
            break
else:
    print("❌ Tests failed to run")
    
# Check imports
print("\n📦 Module Status:")
modules = [
    ("xpath31", "Core Package"),
    ("xpath31.validator", "Validator"),
    ("xpath31.crypto.production_signer", "Crypto"),
    ("xpath31.compliance.filing_rules", "Rules"),
]

for module, name in modules:
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except Exception as e:
        print(f"  ❌ {name}: {str(e)[:50]}...")

# Check CLI
print("\n🖥️ CLI Status:")
cli_result = subprocess.run(
    ["python", "-m", "xpath31.cli", "--help"],
    capture_output=True,
    text=True
)

if cli_result.returncode == 0:
    print("  ✅ CLI is working")
else:
    print(f"  ❌ CLI error: {cli_result.stderr[:100]}...")

print("=" * 60)
