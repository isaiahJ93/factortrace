#!/usr/bin/env python3
"""
Generic Emission Factor Ingestion Script
=========================================
Ingests emission factors from various sources (DEFRA, EPA, EXIOBASE, etc.)
using YAML mapping configuration files.

Usage:
    poetry run python scripts/ingest_factors_generic.py --dataset defra_2024
    poetry run python scripts/ingest_factors_generic.py --dataset defra_2024 --dry-run
    poetry run python scripts/ingest_factors_generic.py --dataset defra_2024 --csv data/raw/defra_2024_full.csv

Requires:
    - data/raw/{dataset}.csv      - Raw CSV data file (or custom via --csv)
    - data/mappings/{dataset}.yml - Mapping configuration

Output:
    - Upserts factors into emission_factors table
    - Logs inserted/updated/skipped counts

Enhanced features:
    - filters.include_scopes: only process rows with these scopes
    - filters.include_categories: only process rows with these categories
    - filters.exclude_patterns: skip rows matching these patterns
    - transforms.activity_type_rules: template-based activity_type generation
"""

import argparse
import csv
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, text

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
MAPPINGS_DIR = DATA_DIR / "mappings"


def load_mapping(dataset: str) -> dict[str, Any]:
    """Load mapping configuration from YAML file."""
    mapping_path = MAPPINGS_DIR / f"{dataset}.yml"
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    with open(mapping_path, "r") as f:
        return yaml.safe_load(f)


def load_csv_data(csv_path: Path, mapping: dict | None = None) -> list[dict[str, str]]:
    """Load CSV data, skipping comment lines.

    Args:
        csv_path: Path to the CSV file
        mapping: Optional mapping config for dataset-specific parsing

    Returns:
        List of row dictionaries
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows = []
    epa_specific = mapping.get("epa_specific", {}) if mapping else {}

    with open(csv_path, "r", encoding="utf-8") as f:
        # Skip comment lines (starting with #)
        lines = [line for line in f if not line.strip().startswith("#")]

    # Parse as CSV
    reader = csv.DictReader(lines)

    # For EPA-specific parsing, we need to track column indices
    # since DictReader can't handle duplicate column names properly
    if epa_specific.get("use_factor_column_index"):
        # Re-read with column indices preserved
        rows = []
        lines_iter = iter(lines)
        header_line = next(lines_iter, None)
        if header_line:
            # Parse header to get column names
            header_reader = csv.reader([header_line])
            header_cols = next(header_reader)

            # Parse remaining rows
            for line in lines_iter:
                row_reader = csv.reader([line])
                row_values = next(row_reader, [])

                # Build row dict with column names, but also store raw values
                row = {}
                for i, col in enumerate(header_cols):
                    if i < len(row_values):
                        row[col] = row_values[i]
                    else:
                        row[col] = ""

                # Store raw column values for positional access
                row["__raw_values__"] = row_values
                rows.append(row)
    else:
        for row in reader:
            rows.append(row)

    return rows


def matches_pattern(key: str, pattern: str) -> bool:
    """
    Check if key matches pattern with wildcard support.
    Pattern format: "Category|Subcategory" with * wildcards.
    """
    pattern_parts = pattern.split("|")
    key_parts = key.split("|")

    # Pad to same length
    while len(pattern_parts) < len(key_parts):
        pattern_parts.append("*")
    while len(key_parts) < len(pattern_parts):
        key_parts.append("")

    for p, k in zip(pattern_parts, key_parts):
        if p == "*":
            continue
        if p.endswith("*") and p.startswith("*"):
            # *text* - contains
            if p[1:-1] not in k:
                return False
        elif p.endswith("*"):
            # text* - starts with
            if not k.startswith(p[:-1]):
                return False
        elif p.startswith("*"):
            # *text - ends with
            if not k.endswith(p[1:]):
                return False
        elif p != k:
            return False

    return True


def should_include_row(row: dict, mapping: dict) -> bool:
    """
    Check if row should be included based on filters.
    Returns True if row passes all filters, False otherwise.
    """
    filters = mapping.get("filters", {})
    columns = mapping.get("columns", {})

    # Get raw values
    raw_scope = row.get(columns.get("raw_scope", ""), "").strip()
    raw_category = row.get(columns.get("raw_category", ""), "").strip()

    # Check include_scopes filter
    include_scopes = filters.get("include_scopes", [])
    if include_scopes and raw_scope not in include_scopes:
        return False

    # Check include_categories filter
    include_categories = filters.get("include_categories", [])
    if include_categories and raw_category not in include_categories:
        return False

    # Check include_values filter (generic column value filtering)
    # Format: {"column_name": ["value1", "value2"]}
    include_values = filters.get("include_values", {})
    for col_name, allowed_values in include_values.items():
        col_value = row.get(col_name, "").strip()
        if allowed_values and col_value not in allowed_values:
            return False

    # Check exclude_patterns filter
    exclude_patterns = filters.get("exclude_patterns", [])
    if exclude_patterns:
        raw_subcategory = row.get(columns.get("raw_subcategory", ""), "").strip()
        key = f"{raw_category}|{raw_subcategory}"
        for pattern in exclude_patterns:
            if matches_pattern(key, pattern):
                return False

    return True


def should_skip_row(row: dict, mapping: dict) -> bool:
    """Check if row should be skipped based on skip_patterns and EPA-specific rules."""
    skip_patterns = mapping.get("skip_patterns", [])
    columns = mapping.get("columns", {})
    epa_specific = mapping.get("epa_specific", {})

    # Build the category|subcategory key
    raw_category = row.get(columns.get("raw_category", ""), "").strip()
    raw_subcategory = row.get(columns.get("raw_subcategory", ""), "").strip()
    key = f"{raw_category}|{raw_subcategory}"

    for pattern in skip_patterns:
        if matches_pattern(key, pattern):
            return True

    # EPA-specific skip rules
    if epa_specific:
        # Skip rows with empty fuel type
        if epa_specific.get("skip_empty_fuel_type"):
            fuel_type = row.get("Fuel Type", "").strip()
            if not fuel_type:
                return True

        # Skip group header rows (check both original and stripped values)
        skip_group_headers = epa_specific.get("skip_group_headers", [])
        if skip_group_headers:
            fuel_type = row.get("Fuel Type", "").strip()
            # Check if fuel_type matches any group header (with stripped comparison)
            for header in skip_group_headers:
                if fuel_type == header or fuel_type == header.strip():
                    # Group headers have no factor value in column 4 (per mmBtu)
                    # Real fuel rows have a factor value, so check this to distinguish
                    raw_values = row.get("__raw_values__", [])
                    if len(raw_values) > 4:
                        factor_col = raw_values[4].strip() if raw_values[4] else ""
                        # If factor column is empty, this is a group header
                        if not factor_col:
                            return True
                    else:
                        # If we can't check, skip if it matches a known header exactly
                        return True
                    break

        # Skip units rows (where Heat Content column contains unit description)
        skip_units_pattern = epa_specific.get("skip_units_row_pattern")
        if skip_units_pattern:
            heat_content = row.get("Heat Content (HHV)", "").strip()
            if skip_units_pattern in heat_content:
                return True

    return False


def apply_activity_type_rules(
    canonical_category: str,
    raw_values: dict[str, str],
    mapping: dict
) -> str | None:
    """
    Apply activity_type_rules to generate activity_type from template.

    Args:
        canonical_category: The mapped canonical category name
        raw_values: Dict with raw_category, raw_subcategory, raw_activity
        mapping: Full mapping config

    Returns:
        Generated activity_type string, or None if no rule matches
    """
    rules = mapping.get("transforms", {}).get("activity_type_rules", {})

    # Get rule for this category, or fall back to default
    template = rules.get(canonical_category) or rules.get("default")

    if not template:
        return None

    # Replace placeholders in template
    result = template
    for key, value in raw_values.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, value)

    return result


def parse_epa_number(value: str) -> float | None:
    """Parse EPA-style numbers with commas, spaces, and quotes."""
    if not value:
        return None
    # Remove quotes, commas, and whitespace
    cleaned = value.replace('"', '').replace(',', '').strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def transform_row(row: dict, mapping: dict) -> dict[str, Any] | None:
    """Transform a raw CSV row to EmissionFactor fields using mapping config.

    Supports two modes:
    1. Standard mode: Uses category_map to transform raw CSV columns
    2. Passthrough mode: For pre-normalized CSVs (like EXIOBASE) where columns
       map directly to EmissionFactor fields. Enabled by passthrough: true in YAML.
    """
    columns = mapping.get("columns", {})
    defaults = mapping.get("defaults", {})
    transforms = mapping.get("transforms", {})
    epa_specific = mapping.get("epa_specific", {})
    passthrough = mapping.get("passthrough", False)

    # PASSTHROUGH MODE: For pre-normalized CSVs (EXIOBASE, etc.)
    # CSV columns map directly to EmissionFactor fields
    if passthrough:
        try:
            # Get values directly from CSV columns
            scope = row.get(columns.get("raw_scope", "scope"), "").strip()
            category = row.get(columns.get("raw_category", "category"), "").strip()
            activity_type = row.get(columns.get("raw_activity_type", "activity_type"), "").strip()
            country_code = row.get(columns.get("raw_country", "country_code"), "").strip()
            raw_factor = row.get(columns.get("raw_factor", "factor"), "").strip()
            raw_unit = row.get(columns.get("raw_unit", "unit"), "").strip()
            raw_external_id = row.get(columns.get("raw_external_id", ""), "").strip()

            # Parse factor value
            factor_str = raw_factor.replace(",", "")
            factor_value = float(factor_str)

            # Get year from row or defaults
            raw_year = row.get(columns.get("raw_year", "year"), "")
            if raw_year:
                year = int(raw_year)
            else:
                year = defaults.get("year", 2024)

            # Apply defaults for missing values
            if not scope:
                scope = defaults.get("scope", "SCOPE_3")
            if not category:
                category = defaults.get("category", "spend_based")
            if not country_code:
                country_code = defaults.get("country_code", "GLOBAL")

            return {
                "scope": scope,
                "category": category,
                "activity_type": activity_type,
                "country_code": country_code,
                "year": year,
                "dataset": mapping.get("dataset", "UNKNOWN"),
                "external_id": raw_external_id or None,
                "factor": factor_value,
                "unit": raw_unit or defaults.get("unit", "kgCO2e"),
                "source": defaults.get("source", ""),
                "method": defaults.get("method", "average_data"),
                "regulation": defaults.get("regulation", "GHG_PROTOCOL"),
                "valid_from": datetime(year, 1, 1),
                "valid_to": datetime(year, 12, 31),
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing passthrough row: {e}")
            return None

    # STANDARD MODE: Transform using category_map
    # Get raw values
    raw_scope = row.get(columns.get("raw_scope", ""), "").strip()
    raw_category = row.get(columns.get("raw_category", ""), "").strip()
    raw_subcategory = row.get(columns.get("raw_subcategory", ""), "").strip()
    raw_activity = row.get(columns.get("raw_activity", ""), "").strip()
    raw_activity_detail = row.get(columns.get("raw_activity_detail", ""), "").strip()
    raw_external_id = row.get(columns.get("raw_external_id", ""), "").strip()

    # Handle factor value - EPA-specific uses column index
    if epa_specific.get("use_factor_column_index"):
        factor_col_idx = epa_specific.get("use_factor_column_index")
        raw_values_list = row.get("__raw_values__", [])
        if factor_col_idx < len(raw_values_list):
            raw_factor = raw_values_list[factor_col_idx]
        else:
            raw_factor = ""
    else:
        raw_factor = row.get(columns.get("raw_factor", ""), "").strip()

    # Handle unit - EPA-specific uses fixed unit
    if epa_specific.get("fixed_unit"):
        raw_unit = epa_specific.get("fixed_unit")
    else:
        raw_unit = row.get(columns.get("raw_unit", ""), "").strip()

    # Transform scope
    scope_map = transforms.get("scope_map", {})
    scope = scope_map.get(raw_scope)
    if not scope:
        # Try default scope for datasets like EXIOBASE and EPA
        scope = scope_map.get("default")
    if not scope:
        logger.warning(f"Unknown scope: '{raw_scope}' - skipping row")
        return None

    # Transform category/activity_type
    category_map = transforms.get("category_map", {})
    category_key = f"{raw_category}|{raw_subcategory}"
    category_info = category_map.get(category_key)

    # Prepare raw values dict for activity_type_rules
    raw_values = {
        "raw_category": raw_category,
        "raw_subcategory": raw_subcategory,
        "raw_activity": raw_activity,
        "raw_activity_detail": raw_activity_detail,
    }

    if category_info:
        # Use explicit mapping
        canonical_category = category_info["category"]
        activity_type = category_info.get("activity_type")

        # If activity_type not in mapping, try rules
        if not activity_type:
            activity_type = apply_activity_type_rules(canonical_category, raw_values, mapping)

        # Apply placeholder substitution to activity_type
        if activity_type:
            for key, value in raw_values.items():
                placeholder = "{" + key + "}"
                activity_type = activity_type.replace(placeholder, value)

        if not activity_type:
            logger.debug(f"No activity_type for category: '{category_key}' - skipping row")
            return None
    else:
        # No explicit mapping - try to use activity_type_rules with a default category
        # This is useful for datasets where we want to auto-generate
        logger.debug(f"No mapping for category: '{category_key}' - skipping row")
        return None

    # Parse factor value
    if epa_specific:
        # Use EPA-specific number parsing (handles commas, spaces, quotes)
        factor_value = parse_epa_number(raw_factor)
        if factor_value is None:
            logger.warning(f"Invalid factor value: '{raw_factor}' - skipping row")
            return None
    else:
        try:
            # Handle various number formats
            factor_str = raw_factor.replace(",", "")  # Remove thousands separator
            factor_value = float(factor_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid factor value: '{raw_factor}' - skipping row")
            return None

    # Build output record
    year = defaults.get("year", 2024)
    return {
        "scope": scope,
        "category": canonical_category,
        "activity_type": activity_type,
        "country_code": defaults.get("country_code", "GLOBAL"),
        "year": year,
        "dataset": mapping.get("dataset", "UNKNOWN"),
        "external_id": raw_external_id or None,
        "factor": factor_value,
        "unit": raw_unit,
        "source": defaults.get("source", ""),
        "method": defaults.get("method", "average_data"),
        "regulation": defaults.get("regulation", "GHG_PROTOCOL"),
        "valid_from": datetime(year, 1, 1),
        "valid_to": datetime(year, 12, 31),
    }


def get_database_url() -> str:
    """Get database URL from environment or .env file."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    env_path = BASE_DIR / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")

    return 'sqlite:///./factortrace.db'


def upsert_factor(conn, factor_data: dict) -> tuple[bool, bool]:
    """
    Upsert emission factor using the unique constraint key.
    Uses raw SQL to avoid ORM model graph issues.

    Returns:
        (inserted, updated) - True/False for each operation
    """
    now = datetime.utcnow()

    # Query by unique key: (scope, category, activity_type, country_code, year, dataset)
    check_sql = text("""
        SELECT id FROM emission_factors
        WHERE scope = :scope
          AND category = :category
          AND activity_type = :activity_type
          AND country_code = :country_code
          AND year = :year
          AND dataset = :dataset
    """)

    result = conn.execute(check_sql, {
        'scope': factor_data['scope'],
        'category': factor_data['category'],
        'activity_type': factor_data['activity_type'],
        'country_code': factor_data['country_code'],
        'year': factor_data['year'],
        'dataset': factor_data['dataset'],
    })

    existing = result.fetchone()

    if existing:
        # Update existing record
        update_sql = text("""
            UPDATE emission_factors SET
                factor = :factor,
                unit = :unit,
                source = :source,
                method = :method,
                regulation = :regulation,
                valid_from = :valid_from,
                valid_to = :valid_to,
                external_id = :external_id,
                updated_at = :updated_at
            WHERE id = :id
        """)
        conn.execute(update_sql, {
            'factor': factor_data['factor'],
            'unit': factor_data['unit'],
            'source': factor_data['source'],
            'method': factor_data['method'],
            'regulation': factor_data['regulation'],
            'valid_from': factor_data['valid_from'],
            'valid_to': factor_data['valid_to'],
            'external_id': factor_data['external_id'],
            'updated_at': now,
            'id': existing[0],
        })
        return (False, True)
    else:
        # Insert new record
        insert_sql = text("""
            INSERT INTO emission_factors
            (scope, category, activity_type, country_code, year, dataset, external_id,
             factor, unit, source, method, regulation, valid_from, valid_to, created_at, updated_at)
            VALUES
            (:scope, :category, :activity_type, :country_code, :year, :dataset, :external_id,
             :factor, :unit, :source, :method, :regulation, :valid_from, :valid_to, :created_at, :updated_at)
        """)
        conn.execute(insert_sql, {
            'scope': factor_data['scope'],
            'category': factor_data['category'],
            'activity_type': factor_data['activity_type'],
            'country_code': factor_data['country_code'],
            'year': factor_data['year'],
            'dataset': factor_data['dataset'],
            'external_id': factor_data['external_id'],
            'factor': factor_data['factor'],
            'unit': factor_data['unit'],
            'source': factor_data['source'],
            'method': factor_data['method'],
            'regulation': factor_data['regulation'],
            'valid_from': factor_data['valid_from'],
            'valid_to': factor_data['valid_to'],
            'created_at': now,
            'updated_at': now,
        })
        return (True, False)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest emission factors from CSV using YAML mapping"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset name (e.g., 'defra_2024'). Must have matching .yml mapping file",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Custom CSV file path (default: data/raw/{dataset}.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and transform data without writing to database",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    args = parser.parse_args()

    dataset = args.dataset.lower()
    dry_run = args.dry_run

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("GENERIC EMISSION FACTOR INGESTION")
    logger.info(f"Dataset: {dataset}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info("=" * 60)

    # Load mapping configuration
    try:
        mapping = load_mapping(dataset)
        logger.info(f"Loaded mapping: {MAPPINGS_DIR / f'{dataset}.yml'}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Determine CSV path
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.is_absolute():
            csv_path = BASE_DIR / csv_path
    else:
        csv_path = RAW_DIR / f"{dataset}.csv"

    # Load CSV data (pass mapping for EPA-specific parsing)
    try:
        rows = load_csv_data(csv_path, mapping)
        logger.info(f"Loaded CSV: {csv_path} ({len(rows)} rows)")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Log filter configuration
    filters = mapping.get("filters", {})
    if filters.get("include_scopes"):
        logger.info(f"Filter: include_scopes = {filters['include_scopes']}")
    if filters.get("include_categories"):
        logger.info(f"Filter: include_categories = {filters['include_categories']}")
    if filters.get("include_values"):
        logger.info(f"Filter: include_values = {filters['include_values']}")

    # Process rows
    inserted = 0
    updated = 0
    skipped_filter = 0
    skipped_pattern = 0
    skipped_transform = 0
    errors = 0

    # Set up database connection if not dry run
    engine = None
    if not dry_run:
        db_url = get_database_url()
        is_sqlite = db_url.startswith("sqlite")
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if is_sqlite else {}
        )
        logger.info(f"Database: {db_url[:50]}...")

    try:
        conn = engine.connect() if engine else None

        # EPA-specific: get stop markers for early termination
        epa_specific = mapping.get("epa_specific", {})
        stop_markers = epa_specific.get("stop_at_markers", [])
        stopped_early = False

        for i, row in enumerate(rows, start=1):
            cols = mapping.get("columns", {})
            raw_scope = row.get(cols.get("raw_scope", ""), "").strip()
            raw_category = row.get(cols.get("raw_category", ""), "").strip()
            raw_subcategory = row.get(cols.get("raw_subcategory", ""), "").strip()

            # EPA-specific: check for stop markers (e.g., "Table 2", "Source:")
            if stop_markers:
                # Check if any cell in the row contains a stop marker
                raw_values = row.get("__raw_values__", list(row.values()))
                for cell in raw_values:
                    cell_str = str(cell).strip() if cell else ""
                    for marker in stop_markers:
                        if marker in cell_str:
                            logger.info(f"Row {i}: Hit stop marker '{marker}' - stopping processing")
                            stopped_early = True
                            break
                    if stopped_early:
                        break
                if stopped_early:
                    break

            # Check filters first (include_scopes, include_categories)
            if not should_include_row(row, mapping):
                skipped_filter += 1
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Row {i} FILTERED: scope='{raw_scope}', "
                        f"category='{raw_category}', subcategory='{raw_subcategory}'"
                    )
                continue

            # Check skip patterns
            if should_skip_row(row, mapping):
                skipped_pattern += 1
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Row {i} SKIP_PATTERN: scope='{raw_scope}', "
                        f"category='{raw_category}', subcategory='{raw_subcategory}'"
                    )
                continue

            # Transform row
            factor_data = transform_row(row, mapping)
            if factor_data is None:
                skipped_transform += 1
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Row {i} NO_MAP: scope='{raw_scope}', "
                        f"category='{raw_category}', subcategory='{raw_subcategory}'"
                    )
                continue

            if dry_run:
                logger.info(
                    f"[DRY RUN] Row {i}: "
                    f"{factor_data['scope']} / {factor_data['category']} / "
                    f"{factor_data['activity_type']} = {factor_data['factor']} {factor_data['unit']}"
                )
                inserted += 1
            else:
                try:
                    was_inserted, was_updated = upsert_factor(conn, factor_data)
                    if was_inserted:
                        inserted += 1
                    elif was_updated:
                        updated += 1
                except Exception as e:
                    logger.error(f"Row {i}: Error upserting factor: {e}")
                    errors += 1

        # Commit if not dry run
        if conn:
            conn.commit()
            logger.info("Database changes committed")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error during ingestion: {e}")
        raise
    finally:
        if conn:
            conn.close()

    # Summary
    total_skipped = skipped_filter + skipped_pattern + skipped_transform
    logger.info("")
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Dataset:           {dataset}")
    logger.info(f"  Inserted:          {inserted}")
    logger.info(f"  Updated:           {updated}")
    logger.info(f"  Skipped (filter):  {skipped_filter}")
    logger.info(f"  Skipped (pattern): {skipped_pattern}")
    logger.info(f"  Skipped (no map):  {skipped_transform}")
    logger.info(f"  Errors:            {errors}")
    logger.info(f"  Total processed:   {inserted + updated + total_skipped + errors}")
    logger.info("=" * 60)

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
