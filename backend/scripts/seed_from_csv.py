#!/usr/bin/env python3
"""
Seed Emission Factors from CSV to Database

Reads emission factors from data/emission_factors.csv and inserts them
into the emission_factors database table using upsert logic.

Usage:
    python scripts/seed_from_csv.py

Features:
- Upsert logic: inserts new records, skips existing (based on unique constraint)
- Loads from the hardcoded fallback dictionary if CSV has limited data
- Can be run multiple times safely
"""
import csv
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, Text, Numeric

# ANSI colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# Hardcoded fallback data (same as in emission_factors.py service)
FALLBACK_FACTORS = [
    # Scope 2 - Purchased Electricity (kgCO2e/kWh)
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "DE", "year": 2024, "factor": 0.35, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "FR", "year": 2024, "factor": 0.08, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "PL", "year": 2024, "factor": 0.70, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "US", "year": 2024, "factor": 0.42, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "UK", "year": 2024, "factor": 0.23, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Electricity", "activity_type": "Electricity", "country_code": "GLOBAL", "year": 2024, "factor": 0.45, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},

    # Scope 2 - Purchased Heat (kgCO2e/kWh)
    {"scope": "SCOPE_2", "category": "Purchased Heat", "activity_type": "District Heating", "country_code": "DE", "year": 2024, "factor": 0.22, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_2", "category": "Purchased Heat", "activity_type": "District Heating", "country_code": "GLOBAL", "year": 2024, "factor": 0.25, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},

    # Scope 3 - Water Supply (kgCO2e/m3)
    {"scope": "SCOPE_3", "category": "Water Supply", "activity_type": "Water", "country_code": "DE", "year": 2024, "factor": 0.30, "unit": "kgCO2e/m3", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Water Supply", "activity_type": "Water", "country_code": "GLOBAL", "year": 2024, "factor": 0.34, "unit": "kgCO2e/m3", "source": "Hardcoded_Fallback"},

    # Scope 3 - Business Travel (kgCO2e/km)
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Flight", "country_code": "DE", "year": 2024, "factor": 0.15, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Flight", "country_code": "US", "year": 2024, "factor": 0.12, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Flight", "country_code": "GLOBAL", "year": 2024, "factor": 0.255, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Train", "country_code": "DE", "year": 2024, "factor": 0.03, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Train", "country_code": "GLOBAL", "year": 2024, "factor": 0.04, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Car", "country_code": "DE", "year": 2024, "factor": 0.21, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Business Travel", "activity_type": "Car", "country_code": "GLOBAL", "year": 2024, "factor": 0.20, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},

    # Scope 3 - Employee Commuting (kgCO2e/km)
    {"scope": "SCOPE_3", "category": "Employee Commuting", "activity_type": "Car", "country_code": "GLOBAL", "year": 2024, "factor": 0.21, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_3", "category": "Employee Commuting", "activity_type": "Public Transit", "country_code": "GLOBAL", "year": 2024, "factor": 0.05, "unit": "kgCO2e/km", "source": "Hardcoded_Fallback"},

    # Scope 1 - Mobile Combustion (kgCO2e/liter)
    {"scope": "SCOPE_1", "category": "Mobile Combustion", "activity_type": "Diesel", "country_code": "DE", "year": 2024, "factor": 2.31, "unit": "kgCO2e/liter", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_1", "category": "Mobile Combustion", "activity_type": "Diesel", "country_code": "GLOBAL", "year": 2024, "factor": 2.40, "unit": "kgCO2e/liter", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_1", "category": "Mobile Combustion", "activity_type": "Petrol", "country_code": "DE", "year": 2024, "factor": 2.10, "unit": "kgCO2e/liter", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_1", "category": "Mobile Combustion", "activity_type": "Petrol", "country_code": "GLOBAL", "year": 2024, "factor": 2.20, "unit": "kgCO2e/liter", "source": "Hardcoded_Fallback"},

    # Scope 1 - Stationary Combustion (kgCO2e/kWh)
    {"scope": "SCOPE_1", "category": "Stationary Combustion", "activity_type": "Natural Gas", "country_code": "DE", "year": 2024, "factor": 0.20, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
    {"scope": "SCOPE_1", "category": "Stationary Combustion", "activity_type": "Natural Gas", "country_code": "GLOBAL", "year": 2024, "factor": 0.21, "unit": "kgCO2e/kWh", "source": "Hardcoded_Fallback"},
]


def normalize_scope(scope: str | int) -> str:
    """Normalize scope to string format (e.g., 1 -> 'SCOPE_1')"""
    if isinstance(scope, int):
        return f"SCOPE_{scope}"
    if isinstance(scope, str):
        scope_upper = scope.upper().strip()
        if scope_upper.startswith("SCOPE_"):
            return scope_upper
        if scope_upper.isdigit():
            return f"SCOPE_{scope_upper}"
        return scope_upper
    return str(scope)


def normalize_country_code(country_code: str | None) -> str:
    """Normalize country code to uppercase, default to GLOBAL"""
    if not country_code:
        return "GLOBAL"
    return country_code.upper().strip()


def load_csv_factors(csv_path: Path) -> list[dict]:
    """Load factors from CSV file."""
    factors = []
    if not csv_path.exists():
        print(f"{YELLOW}CSV file not found: {csv_path}{RESET}")
        return factors

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            factor_data = {
                "scope": normalize_scope(row['scope']),
                "category": row['category'].strip(),
                "activity_type": row['activity_type'].strip(),
                "country_code": normalize_country_code(row.get('country_code')),
                "year": int(row.get('year', 2024)),
                "factor": float(row['factor']),
                "unit": row.get('unit', 'kgCO2e/unit'),
                "source": row.get('source', 'CSV_Import'),
            }
            factors.append(factor_data)

    return factors


def get_database_url():
    """Get database URL from environment or settings."""
    # Try environment variable first
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    # Try to load from .env file
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")

    # Default to SQLite
    return 'sqlite:///./factortrace.db'


def main():
    print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
    print(f"{CYAN}{BOLD}   EMISSION FACTOR DATABASE SEEDER{RESET}")
    print(f"{CYAN}{BOLD}   Populating from CSV and fallback data{RESET}")
    print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")

    # Setup database connection
    db_url = get_database_url()
    is_sqlite = db_url.startswith("sqlite")

    print(f"Database: {db_url[:50]}...")

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if is_sqlite else {}
    )

    # Load factors from CSV
    csv_path = Path(__file__).parent.parent / "data" / "emission_factors.csv"
    csv_factors = load_csv_factors(csv_path)
    print(f"\nLoaded {len(csv_factors)} factors from CSV")

    # Combine with fallback factors
    all_factors = FALLBACK_FACTORS.copy()

    # Add CSV factors (they'll be de-duplicated by the upsert logic)
    for csv_factor in csv_factors:
        # Check if this factor already exists in fallback (by unique key)
        key = (csv_factor['scope'], csv_factor['category'], csv_factor['activity_type'],
               csv_factor['country_code'], csv_factor['year'])
        exists = any(
            (f['scope'], f['category'], f['activity_type'], f['country_code'], f['year']) == key
            for f in all_factors
        )
        if not exists:
            all_factors.append(csv_factor)

    print(f"Total factors to process: {len(all_factors)}")

    # Insert factors using raw SQL
    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for factor_data in all_factors:
            # Check if factor already exists
            check_sql = text("""
                SELECT id FROM emission_factors
                WHERE scope = :scope
                  AND category = :category
                  AND activity_type = :activity_type
                  AND country_code = :country_code
                  AND year = :year
            """)

            result = conn.execute(check_sql, {
                'scope': factor_data['scope'],
                'category': factor_data['category'],
                'activity_type': factor_data['activity_type'],
                'country_code': factor_data['country_code'],
                'year': factor_data['year']
            })

            if result.fetchone():
                skipped += 1
                continue

            # Insert new factor
            insert_sql = text("""
                INSERT INTO emission_factors
                (scope, category, activity_type, country_code, year, factor, unit, source, is_active, created_at, updated_at)
                VALUES
                (:scope, :category, :activity_type, :country_code, :year, :factor, :unit, :source, 1, :created_at, :updated_at)
            """)

            now = datetime.utcnow()
            conn.execute(insert_sql, {
                'scope': factor_data['scope'],
                'category': factor_data['category'],
                'activity_type': factor_data['activity_type'],
                'country_code': factor_data['country_code'],
                'year': factor_data['year'],
                'factor': factor_data['factor'],
                'unit': factor_data['unit'],
                'source': factor_data['source'],
                'created_at': now,
                'updated_at': now,
            })
            inserted += 1

        conn.commit()

    print(f"\n{GREEN}✓ Seeding complete!{RESET}")
    print(f"   Inserted: {inserted}")
    print(f"   Skipped (already exists): {skipped}")

    # Verify by counting
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM emission_factors"))
        total = result.fetchone()[0]
        print(f"   Total factors in database: {total}")

        # Show a sample
        print(f"\n{CYAN}Sample factors in database:{RESET}")
        result = conn.execute(text("SELECT scope, category, activity_type, country_code, factor, unit FROM emission_factors LIMIT 5"))
        for row in result:
            print(f"   {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} {row[5]}")

    print(f"\n{BOLD}{'='*70}{RESET}\n")


if __name__ == "__main__":
    main()
