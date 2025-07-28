#!/usr/bin/env python3
"""Run all tests and show summary."""
import subprocess
import sys
import os

def run_test_file(test_file):
    """Run a single test file and return results."""
    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse results
    output = result.stdout + result.stderr
    if "passed" in output:
        if "failed" in output or "error" in output:
            return "PARTIAL", output
        return "PASS", output
    elif "error" in output.lower():
        return "ERROR", output
    elif "no tests ran" in output:
        return "EMPTY", output
    else:
        return "FAIL", output

print("=" * 60)
print("XPath31 Elite XBRL Validator - Test Results")
print("=" * 60)

test_files = [
    ("Basic Tests", "xpath31/tests/test_simple.py"),
    ("Setup Verification", "xpath31/tests/test_verify_setup.py"),
    ("Data Integrity", "xpath31/tests/test_data_integrity.py"),
    ("Crypto Validation", "xpath31/tests/test_crypto_validation.py"),
    ("Message Imprint", "xpath31/tests/test_message_imprint.py"),
    ("Unit Conversion", "xpath31/tests/test_unit_conversion_assistance.py"),
    ("External Mocks", "xpath31/tests/test_external_mocks.py"),
    ("Load Testing", "xpath31/tests/test_load_realistic.py"),
]

results = []
for name, test_file in test_files:
    if os.path.exists(test_file):
        status, output = run_test_file(test_file)
        
        # Count tests
        passed = output.count(" PASSED")
        
        if status == "PASS":
            icon = "✅"
        elif status == "PARTIAL":
            icon = "⚠️ "
        elif status == "ERROR":
            icon = "❌"
        elif status == "EMPTY":
            icon = "📭"
        else:
            icon = "❌"
            
        results.append((icon, name, status, passed))
        print(f"{icon} {name:<20} - {status:<8} ({passed} tests)")
    else:
        print(f"❓ {name:<20} - NOT FOUND")

print("=" * 60)
total_passed = sum(r[3] for r in results)
print(f"Total tests passed: {total_passed}")
print("=" * 60)
