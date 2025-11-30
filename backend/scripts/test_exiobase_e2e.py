#!/usr/bin/env python3
"""
End-to-End Test: EXIOBASE Spend-Based Calculation
==================================================
This script tests the actual spend-based calculation against the live database.
Uses raw sqlite3 to avoid SQLAlchemy ORM complexity.

Usage:
    python scripts/test_exiobase_e2e.py
"""

import sqlite3
import sys
import os

# Add parent directory to path for app imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.exiobase_mapping import (
        map_sector_label_to_exiobase,
        get_country_fallback_chain,
    )
    HAS_APP_IMPORTS = True
except ImportError:
    HAS_APP_IMPORTS = False
    print("Note: Running without app imports (mapping tests will be skipped)")


def main():
    print("=" * 70)
    print("EXIOBASE Spend-Based Calculation - End-to-End Test")
    print("=" * 70)

    # Connect to the actual database using raw sqlite3
    conn = sqlite3.connect("./factortrace.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check how many EXIOBASE factors we have
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020'
    """)
    exio_count = cursor.fetchone()["cnt"]
    print(f"\n[1] EXIOBASE_2020 factors in database: {exio_count}")

    if exio_count == 0:
        print("    ERROR: No EXIOBASE_2020 factors found! Run the ingest first.")
        conn.close()
        return

    # 2. Get a sample factor for Germany
    cursor.execute("""
        SELECT * FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020' AND country_code = 'DE'
        LIMIT 1
    """)
    sample_factor = cursor.fetchone()

    if sample_factor:
        print(f"\n[2] Sample EXIOBASE factor for Germany:")
        print(f"    Activity Type: {sample_factor['activity_type']}")
        print(f"    Factor: {sample_factor['factor']} {sample_factor['unit']}")
        print(f"    Source: {sample_factor['source']}")

    # 3. List available sectors for Germany
    print(f"\n[3] Available EXIOBASE sectors for DE (first 10):")
    cursor.execute("""
        SELECT DISTINCT activity_type FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020' AND country_code = 'DE'
        ORDER BY activity_type
    """)
    sectors = [row["activity_type"] for row in cursor.fetchall()]
    for i, sector in enumerate(sectors[:10]):
        print(f"    {i+1}. {sector}")
    print(f"    ... and {len(sectors) - 10} more")

    # 4. Test the spend-based calculation manually
    print(f"\n[4] Testing spend-based calculation:")

    test_cases = [
        {
            "country_code": "DE",
            "activity_type": "Computer and related services (72)",
            "spend_amount_eur": 10000.0,
            "description": "IT Services in Germany",
        },
        {
            "country_code": "FR",
            "activity_type": "Motor vehicles, trailers and semi-trailers (34)",
            "spend_amount_eur": 50000.0,
            "description": "Motor vehicles in France",
        },
        {
            "country_code": "US",
            "activity_type": "Financial intermediation services, except insurance and pension funding services (65)",
            "spend_amount_eur": 25000.0,
            "description": "Financial services in US",
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n    Test {i}: {test['description']}")
        print(f"    Country: {test['country_code']}")
        print(f"    Spend: {test['spend_amount_eur']:,.2f} EUR")

        # Look up the factor
        cursor.execute("""
            SELECT * FROM emission_factors
            WHERE dataset = 'EXIOBASE_2020'
              AND method = 'spend_based'
              AND country_code = ?
              AND activity_type = ?
            LIMIT 1
        """, (test["country_code"], test["activity_type"]))

        factor_row = cursor.fetchone()

        if factor_row:
            factor_value = factor_row["factor"]
            emissions = test["spend_amount_eur"] * factor_value

            print(f"    ✓ Factor Found: {factor_value:.6f} {factor_row['unit']}")
            print(f"    ✓ Emissions: {emissions:,.2f} kgCO2e")
            print(f"    ✓ Source: {factor_row['source']}")

            # Check for outlier
            if factor_value > 100.0:
                print(f"    ⚠ OUTLIER WARNING: Factor > 100 kgCO2e/EUR")
        else:
            print(f"    ✗ No factor found for {test['country_code']}/{test['activity_type'][:40]}...")

    # 5. Test sector label mapping
    print(f"\n[5] Testing sector label mapping:")
    if HAS_APP_IMPORTS:
        labels_to_test = ["IT Services", "Car Manufacturing", "Office Supplies", "Banking"]
        for label in labels_to_test:
            mapped = map_sector_label_to_exiobase(label)
            print(f"    '{label}' -> '{mapped}'")
    else:
        print("    (skipped - app imports not available)")

    # 6. Test country fallback chain
    print(f"\n[6] Testing country fallback chain:")
    if HAS_APP_IMPORTS:
        countries_to_test = ["DE", "VN", "SA", "XX"]
        for country in countries_to_test:
            chain = get_country_fallback_chain(country)
            print(f"    '{country}' -> {chain}")
    else:
        print("    (skipped - app imports not available)")

    # 7. Show statistics
    print(f"\n[7] EXIOBASE dataset statistics:")
    cursor.execute("""
        SELECT country_code, COUNT(*) as cnt
        FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020'
        GROUP BY country_code
        ORDER BY cnt DESC
        LIMIT 10
    """)
    print("    Top 10 countries by factor count:")
    for row in cursor.fetchall():
        print(f"      {row['country_code']}: {row['cnt']} factors")

    # 8. Show factor range
    cursor.execute("""
        SELECT MIN(factor) as min_f, MAX(factor) as max_f, AVG(factor) as avg_f
        FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020'
    """)
    stats = cursor.fetchone()
    print(f"\n    Factor range:")
    print(f"      Min: {stats['min_f']:.6f} kgCO2e/EUR")
    print(f"      Max: {stats['max_f']:.6f} kgCO2e/EUR")
    print(f"      Avg: {stats['avg_f']:.6f} kgCO2e/EUR")

    # Count outliers
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM emission_factors
        WHERE dataset = 'EXIOBASE_2020' AND factor > 100.0
    """)
    outlier_count = cursor.fetchone()["cnt"]
    print(f"      Outliers (>100): {outlier_count} factors")

    print("\n" + "=" * 70)
    print("End-to-End Test Complete!")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
