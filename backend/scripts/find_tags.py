#!/usr/bin/env python3
"""
EFRAG Taxonomy Tag Finder

Searches the official ESRS taxonomy Excel file to find the correct
XBRL tag names for GHG emissions reporting.

Usage:
    python scripts/find_tags.py
"""
import pandas as pd
from pathlib import Path
import sys

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

TAXONOMY_FILE = Path(__file__).parent.parent / "data" / "esrs_taxonomy.xlsx"


def main():
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}   EFRAG TAXONOMY TAG FINDER{RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")

    if not TAXONOMY_FILE.exists():
        print(f"Error: Taxonomy file not found at {TAXONOMY_FILE}")
        sys.exit(1)

    print(f"Loading: {TAXONOMY_FILE}")

    # First, let's see what sheets are available
    xl = pd.ExcelFile(TAXONOMY_FILE)
    print(f"\n{BOLD}Available sheets:{RESET}")
    for sheet in xl.sheet_names:
        print(f"  - {sheet}")

    # Read the PresentationLinkbase sheet which has the actual taxonomy elements
    print(f"\n{BOLD}Reading PresentationLinkbase sheet...{RESET}\n")

    try:
        df = pd.read_excel(TAXONOMY_FILE, sheet_name='PresentationLinkbase')
        print(f"{YELLOW}Columns in 'PresentationLinkbase':{RESET}")
        for col in df.columns:
            print(f"  - {col}")
        print(f"\nTotal rows: {len(df)}")
        print(f"\n{BOLD}First 5 rows:{RESET}")
        print(df.head(5).to_string())
    except Exception as e:
        print(f"Error reading PresentationLinkbase: {e}")

    # Search for GHG-related terms
    print(f"\n{GREEN}{BOLD}{'='*70}{RESET}")
    print(f"{GREEN}{BOLD}   SEARCHING FOR GHG EMISSION TAGS{RESET}")
    print(f"{GREEN}{BOLD}{'='*70}{RESET}\n")

    # Search terms for finding emission-related elements
    search_patterns = [
        ("Gross Scope 1", "scope 1"),
        ("Gross Scope 2 Location", "scope 2.*location|location.*scope 2"),
        ("Gross Scope 2 Market", "scope 2.*market|market.*scope 2"),
        ("Gross Scope 3", "scope 3"),
        ("Total GHG", "total.*ghg|ghg.*total|total.*greenhouse"),
    ]

    for label, pattern in search_patterns:
        print(f"{BOLD}Searching for: {label}{RESET}")

        for col in df.columns:
            if df[col].dtype == object:
                mask = df[col].astype(str).str.lower().str.contains(pattern, regex=True, na=False)
                matches = df[mask]

                if len(matches) > 0:
                    print(f"  Found {len(matches)} matches in column '{col}':")
                    for idx, row in matches.head(5).iterrows():  # Limit to 5 per column
                        # Print all columns for this row
                        row_data = []
                        for c in df.columns:
                            val = row[c]
                            if pd.notna(val) and str(val).strip():
                                row_data.append(f"{c}: {val}")
                        print(f"    {CYAN}Row {idx}:{RESET}")
                        for item in row_data[:5]:  # Limit columns shown
                            print(f"      {item}")
                        print()
        print()

    # Special search: Look for element names that look like XBRL tags (CamelCase)
    print(f"\n{GREEN}{BOLD}{'='*70}{RESET}")
    print(f"{GREEN}{BOLD}   LOOKING FOR XBRL-STYLE ELEMENT NAMES{RESET}")
    print(f"{GREEN}{BOLD}{'='*70}{RESET}\n")

    # Search for strings that look like XBRL element names (contain 'Scope' or 'GHG' or 'Greenhouse')
    xbrl_patterns = [
        r'[A-Z][a-z]+Scope[123]',  # CamelCase with Scope
        r'Gross.*Scope',
        r'GHG|GreenhouseGas',
        r'esrs:',
        r'E1-6',  # The ESRS E1-6 disclosure requirement
    ]

    for pattern in xbrl_patterns:
        print(f"{BOLD}Pattern: {pattern}{RESET}")
        for col in df.columns:
            if df[col].dtype == object:
                mask = df[col].astype(str).str.contains(pattern, regex=True, na=False)
                matches = df[mask]
                if len(matches) > 0:
                    print(f"  Column '{col}': {len(matches)} matches")
                    # Show unique values
                    unique_vals = matches[col].dropna().unique()[:10]
                    for val in unique_vals:
                        # Try to extract just the element name part
                        val_str = str(val)
                        if 'Scope' in val_str or 'GHG' in val_str or 'Greenhouse' in val_str:
                            print(f"    {CYAN}→{RESET} {val_str[:100]}")
        print()

    print(f"\n{BOLD}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()
