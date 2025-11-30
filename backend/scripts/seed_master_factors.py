#!/usr/bin/env python3
"""
Master Seed Script for Emission Factors
========================================
Populates the emission_factors table with comprehensive country coverage.

Countries covered:
- Existing/Golden Path: DE, FR, PL, US, GLOBAL
- EU Expansion: IE, IT, NL, AT, CH, ES
- Global Expansion: CN, JP, GB, IN, BR, AU, CA

Scopes covered:
- Scope 2: Electricity (grid average)
- Scope 3: Business Travel (air, rail, car)

All factors use:
- year=2024
- method='average_data'
- regulation='GHG_PROTOCOL'
"""

import sqlite3
from datetime import datetime
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "factortrace.db")


# ============================================================================
# MASTER EMISSION FACTORS DATA
# ============================================================================

# Scope 2 Electricity Grid Factors (kgCO2e per kWh)
# Sources: IEA, EEA, EPA, national grid operators (2024 data)
ELECTRICITY_FACTORS = {
    # Existing / Golden Path
    "GLOBAL": 0.436,   # World average (IEA)
    "DE": 0.350,       # Germany - high renewables push
    "FR": 0.052,       # France - nuclear dominant
    "PL": 0.658,       # Poland - coal heavy
    "US": 0.386,       # US average (EPA eGRID)

    # EU Expansion
    "IE": 0.296,       # Ireland
    "IT": 0.315,       # Italy
    "NL": 0.328,       # Netherlands
    "AT": 0.087,       # Austria - hydro dominant
    "CH": 0.024,       # Switzerland - hydro/nuclear
    "ES": 0.198,       # Spain - high renewables

    # Global Expansion
    "CN": 0.555,       # China - coal heavy
    "JP": 0.457,       # Japan - mix
    "GB": 0.207,       # UK - gas/renewables
    "IN": 0.708,       # India - coal dominant
    "BR": 0.074,       # Brazil - hydro dominant
    "AU": 0.656,       # Australia - coal heavy
    "CA": 0.120,       # Canada - hydro dominant
}

# Scope 3 Business Travel - Air (kgCO2e per passenger-km)
AIR_TRAVEL_FACTORS = {
    "Air Travel - Short Haul": 0.255,   # <1500km flights
    "Air Travel - Medium Haul": 0.156,  # 1500-4000km
    "Air Travel - Long Haul": 0.195,    # >4000km (higher due to RFI)
}

# Scope 3 Business Travel - Rail (kgCO2e per passenger-km)
RAIL_FACTORS = {
    "GLOBAL": 0.041,
    "DE": 0.032,
    "FR": 0.006,
    "PL": 0.054,
    "US": 0.089,
    "IE": 0.045,
    "IT": 0.033,
    "NL": 0.021,
    "AT": 0.018,
    "CH": 0.008,
    "ES": 0.029,
    "CN": 0.027,
    "JP": 0.019,
    "GB": 0.035,
    "IN": 0.043,
    "BR": 0.051,
    "AU": 0.065,
    "CA": 0.072,
}

# Scope 3 Business Travel - Car (kgCO2e per km)
CAR_FACTORS = {
    "GLOBAL": 0.171,
    "DE": 0.168,
    "FR": 0.162,
    "PL": 0.175,
    "US": 0.202,
    "IE": 0.165,
    "IT": 0.158,
    "NL": 0.155,
    "AT": 0.162,
    "CH": 0.158,
    "ES": 0.159,
    "CN": 0.178,
    "JP": 0.142,
    "GB": 0.164,
    "IN": 0.168,
    "BR": 0.165,
    "AU": 0.195,
    "CA": 0.198,
}

# Scope 3 Employee Commuting (kgCO2e per passenger-km)
COMMUTE_FACTORS = {
    "Bus": 0.089,
    "Metro": 0.033,
    "Bicycle": 0.000,
}

# Scope 3 Freight Transport
FREIGHT_MODES = {
    "Road Freight": 0.105,
    "Rail Freight": 0.027,
    "Air Freight": 1.130,
    "Sea Freight": 0.016,
}


def upsert_factor(cursor, factor_data: dict) -> bool:
    """
    Insert or update an emission factor using raw SQL.
    Returns True if inserted, False if updated.
    """
    # Check if exists
    cursor.execute("""
        SELECT id FROM emission_factors
        WHERE scope = ? AND category = ? AND activity_type = ?
        AND country_code = ? AND year = ? AND method = ?
    """, (
        factor_data["scope"],
        factor_data["category"],
        factor_data["activity_type"],
        factor_data["country_code"],
        factor_data["year"],
        factor_data["method"],
    ))

    existing = cursor.fetchone()
    now = datetime.utcnow().isoformat()

    if existing:
        # Update existing
        cursor.execute("""
            UPDATE emission_factors SET
                factor = ?,
                unit = ?,
                source = ?,
                regulation = ?,
                valid_from = ?,
                valid_to = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            factor_data["factor"],
            factor_data["unit"],
            factor_data["source"],
            factor_data["regulation"],
            factor_data["valid_from"],
            factor_data["valid_to"],
            now,
            existing[0],
        ))
        return False
    else:
        # Insert new
        cursor.execute("""
            INSERT INTO emission_factors
            (scope, category, activity_type, country_code, year, method,
             factor, unit, source, regulation, valid_from, valid_to,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            factor_data["scope"],
            factor_data["category"],
            factor_data["activity_type"],
            factor_data["country_code"],
            factor_data["year"],
            factor_data["method"],
            factor_data["factor"],
            factor_data["unit"],
            factor_data["source"],
            factor_data["regulation"],
            factor_data["valid_from"],
            factor_data["valid_to"],
            now,
            now,
        ))
        return True


def seed_master_factors():
    """Main seeding function using raw SQLite."""
    print(f"Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        inserted = 0
        updated = 0

        # Common metadata for all factors
        base_meta = {
            "year": 2024,
            "method": "average_data",
            "regulation": "GHG_PROTOCOL",
            "valid_from": "2024-01-01",
            "valid_to": "2024-12-31",
        }

        print("=" * 60)
        print("MASTER EMISSION FACTORS SEED")
        print("=" * 60)

        # ====================================================================
        # SCOPE 2: ELECTRICITY
        # ====================================================================
        print("\n[Scope 2] Seeding Electricity factors...")
        for country, factor in ELECTRICITY_FACTORS.items():
            factor_data = {
                **base_meta,
                "scope": "SCOPE_2",
                "category": "electricity",
                "activity_type": "Electricity - Grid Average",
                "country_code": country,
                "factor": factor,
                "unit": "kWh",
                "source": "IEA/EEA/EPA 2024",
            }
            if upsert_factor(cursor, factor_data):
                inserted += 1
            else:
                updated += 1
        print(f"   Electricity: {len(ELECTRICITY_FACTORS)} countries")

        # ====================================================================
        # SCOPE 3: BUSINESS TRAVEL - AIR
        # ====================================================================
        print("\n[Scope 3] Seeding Air Travel factors...")
        for country in ELECTRICITY_FACTORS.keys():
            for flight_type, factor in AIR_TRAVEL_FACTORS.items():
                factor_data = {
                    **base_meta,
                    "scope": "SCOPE_3",
                    "category": "business_travel",
                    "activity_type": flight_type,
                    "country_code": country,
                    "factor": factor,
                    "unit": "passenger-km",
                    "source": "DEFRA/GHG Protocol 2024",
                }
                if upsert_factor(cursor, factor_data):
                    inserted += 1
                else:
                    updated += 1
        print(f"   Air Travel: {len(ELECTRICITY_FACTORS) * len(AIR_TRAVEL_FACTORS)} entries")

        # ====================================================================
        # SCOPE 3: BUSINESS TRAVEL - RAIL
        # ====================================================================
        print("\n[Scope 3] Seeding Rail Travel factors...")
        for country, factor in RAIL_FACTORS.items():
            factor_data = {
                **base_meta,
                "scope": "SCOPE_3",
                "category": "business_travel",
                "activity_type": "Rail Travel",
                "country_code": country,
                "factor": factor,
                "unit": "passenger-km",
                "source": "DEFRA/EEA 2024",
            }
            if upsert_factor(cursor, factor_data):
                inserted += 1
            else:
                updated += 1
        print(f"   Rail Travel: {len(RAIL_FACTORS)} countries")

        # ====================================================================
        # SCOPE 3: BUSINESS TRAVEL - CAR
        # ====================================================================
        print("\n[Scope 3] Seeding Car Travel factors...")
        for country, factor in CAR_FACTORS.items():
            factor_data = {
                **base_meta,
                "scope": "SCOPE_3",
                "category": "business_travel",
                "activity_type": "Car - Average",
                "country_code": country,
                "factor": factor,
                "unit": "km",
                "source": "DEFRA/EPA 2024",
            }
            if upsert_factor(cursor, factor_data):
                inserted += 1
            else:
                updated += 1
        print(f"   Car Travel: {len(CAR_FACTORS)} countries")

        # ====================================================================
        # SCOPE 3: EMPLOYEE COMMUTING
        # ====================================================================
        print("\n[Scope 3] Seeding Employee Commuting factors...")
        for country in ELECTRICITY_FACTORS.keys():
            for mode, factor in COMMUTE_FACTORS.items():
                factor_data = {
                    **base_meta,
                    "scope": "SCOPE_3",
                    "category": "employee_commuting",
                    "activity_type": mode,
                    "country_code": country,
                    "factor": factor,
                    "unit": "passenger-km",
                    "source": "DEFRA 2024",
                }
                if upsert_factor(cursor, factor_data):
                    inserted += 1
                else:
                    updated += 1
        print(f"   Commuting: {len(ELECTRICITY_FACTORS) * len(COMMUTE_FACTORS)} entries")

        # ====================================================================
        # SCOPE 3: UPSTREAM TRANSPORTATION (Freight)
        # ====================================================================
        print("\n[Scope 3] Seeding Freight Transport factors...")
        for country in ELECTRICITY_FACTORS.keys():
            for mode, factor in FREIGHT_MODES.items():
                factor_data = {
                    **base_meta,
                    "scope": "SCOPE_3",
                    "category": "upstream_transportation",
                    "activity_type": mode,
                    "country_code": country,
                    "factor": factor,
                    "unit": "tonne-km",
                    "source": "DEFRA/EPA 2024",
                }
                if upsert_factor(cursor, factor_data):
                    inserted += 1
                else:
                    updated += 1
        print(f"   Freight: {len(ELECTRICITY_FACTORS) * len(FREIGHT_MODES)} entries")

        # Commit all changes
        conn.commit()

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 60)
        print("SEED SUMMARY")
        print("=" * 60)
        print(f"  Inserted: {inserted}")
        print(f"  Updated:  {updated}")
        print(f"  Total:    {inserted + updated}")

        # Query unique countries
        cursor.execute("SELECT COUNT(DISTINCT country_code) FROM emission_factors")
        country_count = cursor.fetchone()[0]
        print(f"\n  Unique Countries: {country_count}")

        # List all countries
        cursor.execute("SELECT DISTINCT country_code FROM emission_factors ORDER BY country_code")
        countries = [row[0] for row in cursor.fetchall()]
        print(f"  Countries: {', '.join(countries)}")

        # Total factors in DB
        cursor.execute("SELECT COUNT(*) FROM emission_factors")
        total_factors = cursor.fetchone()[0]
        print(f"\n  Total factors in DB: {total_factors}")

        print("=" * 60)
        print("SEED COMPLETE!")
        print("=" * 60)

        return inserted + updated

    except Exception as e:
        conn.rollback()
        print(f"\n ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_master_factors()
