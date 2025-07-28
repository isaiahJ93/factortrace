#!/usr/bin/env python3
"""Check if all dependencies are installed."""

dependencies = [
    "pytest",
    "lxml", 
    "cryptography",
    "asn1crypto",
    "requests",
    "httpx",
    "click"
]

print("Checking dependencies...\n")

for dep in dependencies:
    try:
        __import__(dep)
        print(f"✅ {dep}")
    except ImportError:
        print(f"❌ {dep} - NOT INSTALLED")

print("\nRun: poetry add <missing_package> to install")
