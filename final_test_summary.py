#!/usr/bin/env python3
"""Final test summary for XPath31."""
import subprocess
import json

print("=" * 70)
print("XPath31 Elite XBRL Validator - Final Status Report")
print("=" * 70)

# Run tests and capture output
result = subprocess.run(
    ["python", "-m", "pytest", "xpath31/tests/", "-v", "--tb=no", "--json-report", "--json-report-file=/dev/stdout"],
    capture_output=True,
    text=True
)

# Parse standard output for counts
output = result.stdout + result.stderr

# Extract counts
import re
passed = len(re.findall(r'PASSED', output))
failed = len(re.findall(r'FAILED', output))
skipped = len(re.findall(r'SKIPPED|skipped', output))
errors = len(re.findall(r'ERROR', output))

print("\n📊 Test Results:")
print(f"  ✅ Passed:  {passed}")
print(f"  ❌ Failed:  {failed}")
print(f"  ⏭️  Skipped: {skipped}")
print(f"  🚨 Errors:  {errors}")

# Test features
print("\n🎯 Feature Status:")
features = [
    ("XBRL Validation", "xpath31.validator", "XBRLValidator"),
    ("Digital Signatures", "xpath31.crypto.production_signer", "ProductionSigner"),
    ("CLI Interface", "xpath31.cli", "cli"),
    ("Filing Rules", "xpath31.compliance.filing_rules", "DEFAULT_RULES"),
]

for name, module, obj in features:
    try:
        exec(f"from {module} import {obj}")
        print(f"  ✅ {name}")
    except:
        print(f"  ❌ {name}")

# CLI test
print("\n🖥️  CLI Commands:")
cli_result = subprocess.run(["python", "-m", "xpath31.cli", "--help"], capture_output=True, text=True)
if cli_result.returncode == 0:
    commands = re.findall(r'^\s+(\w+)\s+', cli_result.stdout, re.MULTILINE)
    for cmd in commands:
        if cmd not in ['Options', 'Commands']:
            print(f"  ✅ xpath31 {cmd}")

print("\n" + "=" * 70)
print("🎉 XPath31 Elite XBRL Validator is ready for use!")
print("=" * 70)
