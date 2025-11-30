#!/usr/bin/env python3
"""
EXIOBASE 3 Spend-Based Emission Factor Preparation Script
==========================================================
Processes EXIOBASE 3 IOT_2020_pxp data to generate spend-based emission factors
(kgCO2e per EUR of final demand) for each country-sector combination.

Usage:
    source venv/bin/activate
    python scripts/prepare_exiobase_spend_2020.py

Input:
    data/raw/IOT_2020_pxp.zip - EXIOBASE 3.9.4 product-by-product IO tables

Output:
    data/raw/exiobase3_spend_2020.csv - Normalized CSV for generic ingest pipeline

The M matrix from PyMRIO provides total emissions (direct + indirect) per unit
of final demand. Since EXIOBASE values are in millions of EUR (M.EUR), we
convert to kgCO2e per EUR by dividing by 1,000,000.

CO2e calculation:
    CO2e = CO2 + (CH4 * 28) + (N2O * 265)
    Using AR5 GWP values: CH4=28, N2O=265
"""

import csv
import logging
import sys
from pathlib import Path

import pymrio
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

# Input/output files
INPUT_ZIP = RAW_DIR / "IOT_2020_pxp.zip"
OUTPUT_CSV = RAW_DIR / "exiobase3_spend_2020.csv"

# GWP values from AR5 (100-year)
GWP_CH4 = 28
GWP_N2O = 265

# EXIOBASE region to ISO2 mapping
# Most EXIOBASE 3 regions are already ISO2, but some need mapping
EXIO_TO_ISO2 = {
    # EU countries (already ISO2)
    "AT": "AT", "BE": "BE", "BG": "BG", "CY": "CY", "CZ": "CZ",
    "DE": "DE", "DK": "DK", "EE": "EE", "ES": "ES", "FI": "FI",
    "FR": "FR", "GR": "GR", "HR": "HR", "HU": "HU", "IE": "IE",
    "IT": "IT", "LT": "LT", "LU": "LU", "LV": "LV", "MT": "MT",
    "NL": "NL", "PL": "PL", "PT": "PT", "RO": "RO", "SE": "SE",
    "SI": "SI", "SK": "SK",
    # Other major countries (already ISO2)
    "GB": "GB", "US": "US", "JP": "JP", "CN": "CN", "CA": "CA",
    "KR": "KR", "BR": "BR", "IN": "IN", "MX": "MX", "RU": "RU",
    "AU": "AU", "CH": "CH", "TR": "TR", "TW": "TW", "NO": "NO",
    "ID": "ID", "ZA": "ZA",
    # Rest-of-world regions - map to descriptive codes
    "WA": "ROW_ASIA",      # Rest of World - Asia and Pacific
    "WL": "ROW_LATAM",     # Rest of World - Latin America
    "WE": "ROW_EUROPE",    # Rest of World - Europe
    "WF": "ROW_AFRICA",    # Rest of World - Africa
    "WM": "ROW_MIDEAST",   # Rest of World - Middle East
}


def get_ghg_stressor_indices(stressor_list: list) -> dict:
    """
    Find indices of CO2, CH4, and N2O stressors in the F/M matrix.

    Returns dict with keys 'co2', 'ch4', 'n2o' mapping to list of matching stressor names.
    We aggregate all CO2/CH4/N2O variants (combustion, non-combustion, agriculture, etc.)
    """
    indices = {"co2": [], "ch4": [], "n2o": []}

    for stressor in stressor_list:
        s_lower = stressor.lower()
        # CO2 - include biogenic since it's still carbon
        # But exclude CO2_bio for now as it's often counted separately in carbon accounting
        if "co2 -" in s_lower and "co2_bio" not in s_lower:
            indices["co2"].append(stressor)
        elif "ch4 -" in s_lower:
            indices["ch4"].append(stressor)
        elif "n2o -" in s_lower:
            indices["n2o"].append(stressor)

    return indices


def compute_co2e_factors(exio) -> pd.DataFrame:
    """
    Compute CO2e emission factors from EXIOBASE M matrix.

    The M matrix contains emissions (kg) per M.EUR of final demand.
    We convert to kg CO2e per EUR and aggregate by country-sector.

    Returns:
        DataFrame with columns: region, sector, factor_kg_per_eur
    """
    ae = exio.air_emissions
    M = ae.M  # emissions per M.EUR of final demand

    # Get stressor indices
    stressor_indices = get_ghg_stressor_indices(list(M.index))
    logger.info(f"Found CO2 stressors: {len(stressor_indices['co2'])}")
    logger.info(f"Found CH4 stressors: {len(stressor_indices['ch4'])}")
    logger.info(f"Found N2O stressors: {len(stressor_indices['n2o'])}")

    # Log the stressors we're using
    for gas, stressors in stressor_indices.items():
        logger.debug(f"{gas.upper()} stressors: {stressors}")

    # Sum up all CO2 sources (kg per M.EUR)
    co2_total = M.loc[stressor_indices["co2"]].sum(axis=0) if stressor_indices["co2"] else pd.Series(0, index=M.columns)

    # Sum up all CH4 sources and convert to CO2e (kg per M.EUR)
    ch4_total = M.loc[stressor_indices["ch4"]].sum(axis=0) if stressor_indices["ch4"] else pd.Series(0, index=M.columns)
    ch4_co2e = ch4_total * GWP_CH4

    # Sum up all N2O sources and convert to CO2e (kg per M.EUR)
    n2o_total = M.loc[stressor_indices["n2o"]].sum(axis=0) if stressor_indices["n2o"] else pd.Series(0, index=M.columns)
    n2o_co2e = n2o_total * GWP_N2O

    # Total CO2e per M.EUR
    co2e_per_meur = co2_total + ch4_co2e + n2o_co2e

    # Convert to kg CO2e per EUR (divide by 1,000,000)
    co2e_per_eur = co2e_per_meur / 1_000_000

    # Build result DataFrame
    records = []
    for (region, sector), factor in co2e_per_eur.items():
        records.append({
            "region": region,
            "sector": sector,
            "factor_kg_per_eur": factor
        })

    df = pd.DataFrame(records)

    # Log summary statistics
    logger.info(f"Factor statistics:")
    logger.info(f"  Min: {df['factor_kg_per_eur'].min():.6f} kgCO2e/EUR")
    logger.info(f"  Max: {df['factor_kg_per_eur'].max():.6f} kgCO2e/EUR")
    logger.info(f"  Mean: {df['factor_kg_per_eur'].mean():.6f} kgCO2e/EUR")
    logger.info(f"  Median: {df['factor_kg_per_eur'].median():.6f} kgCO2e/EUR")

    return df


def map_region_to_iso2(region: str) -> str:
    """Map EXIOBASE region code to ISO2 country code."""
    return EXIO_TO_ISO2.get(region, f"UNKNOWN_{region}")


def generate_sector_code(sector: str) -> str:
    """
    Generate a short sector code from the sector name.
    Uses first 3 words, max 30 chars, snake_case.
    """
    # Clean and split
    words = sector.replace(",", "").replace("(", "").replace(")", "").split()
    # Take first 3 words
    short = "_".join(words[:3]).lower()
    # Limit to 30 chars
    return short[:30]


def main():
    logger.info("=" * 60)
    logger.info("EXIOBASE 3 SPEND-BASED FACTOR PREPARATION")
    logger.info("=" * 60)

    # Check input file
    if not INPUT_ZIP.exists():
        logger.error(f"Input file not found: {INPUT_ZIP}")
        sys.exit(1)

    logger.info(f"Input: {INPUT_ZIP}")
    logger.info(f"Output: {OUTPUT_CSV}")

    # Load EXIOBASE
    logger.info("Loading EXIOBASE (this takes ~30 seconds)...")
    exio = pymrio.parse_exiobase3(str(INPUT_ZIP))

    regions = list(exio.get_regions())
    sectors = list(exio.get_sectors())
    logger.info(f"Regions: {len(regions)}")
    logger.info(f"Sectors: {len(sectors)}")

    # Calculate the full system (Leontief inverse, multipliers, etc.)
    logger.info("Calculating system (Leontief inverse, multipliers)...")
    logger.info("This may take a few minutes...")
    exio.calc_all()

    # Compute CO2e factors
    logger.info("Computing CO2e emission factors...")
    df = compute_co2e_factors(exio)

    # Build output CSV
    logger.info("Building output CSV...")

    output_rows = []
    for _, row in df.iterrows():
        region = row["region"]
        sector = row["sector"]
        factor = row["factor_kg_per_eur"]

        # Skip zero/negative factors
        if factor <= 0:
            continue

        country_code = map_region_to_iso2(region)
        sector_code = generate_sector_code(sector)

        output_rows.append({
            "dataset": "EXIOBASE_2020",
            "scope": "SCOPE_3",
            "category": "spend_based",
            "activity_type": sector,
            "country_code": country_code,
            "year": 2020,
            "factor": round(factor, 8),  # 8 decimal places
            "unit": "kgCO2e_per_EUR",
            "method": "spend_based",
            "regulation": "EXIOBASE",
            "source": "EXIOBASE 3.9.4 IOT_2020_pxp",
            "sector_code": sector_code,
            "sector_name": sector,
        })

    logger.info(f"Generated {len(output_rows)} emission factors")

    # Write CSV
    fieldnames = [
        "dataset", "scope", "category", "activity_type",
        "country_code", "year", "factor", "unit",
        "method", "regulation", "source",
        "sector_code", "sector_name"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    logger.info(f"Wrote {len(output_rows)} rows to {OUTPUT_CSV}")

    # Print sample rows
    logger.info("")
    logger.info("Sample rows:")
    for i, row in enumerate(output_rows[:5]):
        logger.info(f"  {row['country_code']}/{row['sector_code']}: {row['factor']} {row['unit']}")

    # Summary by region
    logger.info("")
    logger.info("Factors per region:")
    from collections import Counter
    region_counts = Counter(r["country_code"] for r in output_rows)
    for region, count in sorted(region_counts.items()):
        logger.info(f"  {region}: {count}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("PREPARATION COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
