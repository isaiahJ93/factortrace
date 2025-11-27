#!/usr/bin/env python3
"""
Golden Path Seed Script - Production Database

Populates the emission_factors table with the specific test values
required for the multi-country test suite.

All factors use method='average_data' as the default.

Usage:
    python scripts/seed_production_db.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# SaaS-Ready Production Dataset
PRODUCTION_FACTORS = [
    # =========================================================================
    # SCOPE 1 - Direct Emissions (Mobile Combustion)
    # =========================================================================
    {
        "scope": "SCOPE_1",
        "category": "Mobile Combustion",
        "activity_type": "Diesel",
        "country_code": "DE",
        "year": 2024,
        "factor": 2.65,
        "unit": "kgCO2e/liter",
        "source": "DEFRA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
    {
        "scope": "SCOPE_1",
        "category": "Mobile Combustion",
        "activity_type": "Diesel",
        "country_code": "GLOBAL",
        "year": 2024,
        "factor": 2.70,
        "unit": "kgCO2e/liter",
        "source": "IPCC_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },

    # =========================================================================
    # SCOPE 2 - Indirect Emissions (Purchased Electricity - Grid Mixes)
    # =========================================================================
    {
        "scope": "SCOPE_2",
        "category": "Purchased Electricity",
        "activity_type": "Electricity",
        "country_code": "DE",
        "year": 2024,
        "factor": 0.35,
        "unit": "kgCO2e/kWh",
        "source": "IEA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
    {
        "scope": "SCOPE_2",
        "category": "Purchased Electricity",
        "activity_type": "Electricity",
        "country_code": "FR",
        "year": 2024,
        "factor": 0.08,
        "unit": "kgCO2e/kWh",
        "source": "IEA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
    {
        "scope": "SCOPE_2",
        "category": "Purchased Electricity",
        "activity_type": "Electricity",
        "country_code": "PL",
        "year": 2024,
        "factor": 0.70,
        "unit": "kgCO2e/kWh",
        "source": "IEA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
    {
        "scope": "SCOPE_2",
        "category": "Purchased Electricity",
        "activity_type": "Electricity",
        "country_code": "US",
        "year": 2024,
        "factor": 0.38,
        "unit": "kgCO2e/kWh",
        "source": "EPA_eGRID_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },

    # =========================================================================
    # SCOPE 3 - Value Chain Emissions
    # =========================================================================
    # Category 6: Business Travel
    {
        "scope": "SCOPE_3",
        "category": "Business Travel",
        "activity_type": "Flight",
        "country_code": "DE",
        "year": 2024,
        "factor": 0.15,
        "unit": "kgCO2e/km",
        "source": "DEFRA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
    # Category 5: Waste Generated in Operations
    {
        "scope": "SCOPE_3",
        "category": "Waste Generated",
        "activity_type": "Landfill",
        "country_code": "DE",
        "year": 2024,
        "factor": 0.50,
        "unit": "kgCO2e/kg",
        "source": "DEFRA_2024",
        "method": "average_data",
        "regulation": "GHG_PROTOCOL"
    },
]


def get_database_url():
    """Get database URL from environment or .env file."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")

    return 'sqlite:///./factortrace.db'


def main():
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}   SaaS-READY PRODUCTION DATA SEED{RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")

    db_url = get_database_url()
    is_sqlite = db_url.startswith("sqlite")

    print(f"Database: {db_url[:50]}...")

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if is_sqlite else {}
    )

    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for factor in PRODUCTION_FACTORS:
            # Check if factor already exists
            check_sql = text("""
                SELECT id FROM emission_factors
                WHERE scope = :scope
                  AND category = :category
                  AND activity_type = :activity_type
                  AND country_code = :country_code
                  AND year = :year
                  AND method = :method
            """)

            result = conn.execute(check_sql, {
                'scope': factor['scope'],
                'category': factor['category'],
                'activity_type': factor['activity_type'],
                'country_code': factor['country_code'],
                'year': factor['year'],
                'method': factor['method']
            })

            if result.fetchone():
                skipped += 1
                print(f"   {YELLOW}SKIP{RESET} {factor['scope']} | {factor['activity_type']} | {factor['country_code']} (exists)")
                continue

            # Insert new factor
            insert_sql = text("""
                INSERT INTO emission_factors
                (scope, category, activity_type, country_code, year, factor, unit, source, method, regulation, created_at, updated_at)
                VALUES
                (:scope, :category, :activity_type, :country_code, :year, :factor, :unit, :source, :method, :regulation, :created_at, :updated_at)
            """)

            now = datetime.utcnow()
            conn.execute(insert_sql, {
                'scope': factor['scope'],
                'category': factor['category'],
                'activity_type': factor['activity_type'],
                'country_code': factor['country_code'],
                'year': factor['year'],
                'factor': factor['factor'],
                'unit': factor['unit'],
                'source': factor['source'],
                'method': factor['method'],
                'regulation': factor['regulation'],
                'created_at': now,
                'updated_at': now,
            })
            inserted += 1
            print(f"   {GREEN}INSERT{RESET} {factor['scope']} | {factor['activity_type']} | {factor['country_code']} -> {factor['factor']}")

        conn.commit()

    print(f"\n{GREEN}✓ Seeding complete!{RESET}")
    print(f"   Inserted: {inserted}")
    print(f"   Skipped: {skipped}")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM emission_factors"))
        total = result.fetchone()[0]
        print(f"   Total factors in database: {total}")

        print(f"\n{CYAN}All factors in database:{RESET}")
        result = conn.execute(text("""
            SELECT scope, category, activity_type, country_code, factor, unit, method
            FROM emission_factors
            ORDER BY scope, category, country_code
        """))
        for row in result:
            print(f"   {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} {row[5]} | {row[6]}")

    print(f"\n{BOLD}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()
