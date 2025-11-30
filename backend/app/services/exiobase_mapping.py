"""
EXIOBASE Sector Mapping Service
================================
Maps user-friendly sector labels to EXIOBASE 3 sector names.
Also provides country code to ROW region fallback logic.
"""
import logging
from pathlib import Path
from typing import Optional, Dict
import yaml

logger = logging.getLogger(__name__)

# Base path for mappings
MAPPINGS_DIR = Path(__file__).parent.parent.parent / "data" / "mappings"
USER_SECTOR_MAPPING_FILE = MAPPINGS_DIR / "user_sector_to_exiobase.yml"

# Cache for loaded mappings
_sector_mapping_cache: Optional[Dict[str, str]] = None


def _load_sector_mapping() -> Dict[str, str]:
    """Load user sector to EXIOBASE mapping from YAML file."""
    global _sector_mapping_cache

    if _sector_mapping_cache is not None:
        return _sector_mapping_cache

    if not USER_SECTOR_MAPPING_FILE.exists():
        logger.warning(f"Sector mapping file not found: {USER_SECTOR_MAPPING_FILE}")
        _sector_mapping_cache = {}
        return _sector_mapping_cache

    try:
        with open(USER_SECTOR_MAPPING_FILE, "r", encoding="utf-8") as f:
            _sector_mapping_cache = yaml.safe_load(f) or {}
        logger.info(f"Loaded {len(_sector_mapping_cache)} sector mappings from {USER_SECTOR_MAPPING_FILE}")
    except Exception as e:
        logger.error(f"Error loading sector mapping: {e}")
        _sector_mapping_cache = {}

    return _sector_mapping_cache


def map_sector_label_to_exiobase(sector_label: str) -> Optional[str]:
    """
    Map a user-friendly sector label to an EXIOBASE sector name.

    Args:
        sector_label: User-friendly sector label (e.g., "IT Services")

    Returns:
        EXIOBASE sector name if mapping found, None otherwise.

    Examples:
        >>> map_sector_label_to_exiobase("IT Services")
        'Computer programming, consultancy and related activities'

        >>> map_sector_label_to_exiobase("Unknown Sector")
        None
    """
    mapping = _load_sector_mapping()

    # Try exact match first
    if sector_label in mapping:
        return mapping[sector_label]

    # Try case-insensitive match
    label_lower = sector_label.lower().strip()
    for key, value in mapping.items():
        if key.lower().strip() == label_lower:
            return value

    return None


def resolve_exiobase_sector(
    exiobase_sector: Optional[str] = None,
    sector_label: Optional[str] = None,
    activity_type: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve the EXIOBASE sector name from various inputs.

    Priority order:
    1. Direct exiobase_sector if provided
    2. Map sector_label if provided
    3. Try to map activity_type as a fallback

    Args:
        exiobase_sector: Direct EXIOBASE sector name
        sector_label: User-friendly sector label to map
        activity_type: Activity type string to try mapping

    Returns:
        EXIOBASE sector name or None if no mapping found.
    """
    # 1. Direct sector name takes priority
    if exiobase_sector:
        return exiobase_sector

    # 2. Try mapping sector_label
    if sector_label:
        mapped = map_sector_label_to_exiobase(sector_label)
        if mapped:
            return mapped

    # 3. Try mapping activity_type as fallback
    if activity_type:
        mapped = map_sector_label_to_exiobase(activity_type)
        if mapped:
            return mapped
        # If activity_type looks like an EXIOBASE sector already, use it directly
        # (EXIOBASE sectors typically have commas or are longer than 20 chars)
        if len(activity_type) > 20 or "," in activity_type:
            return activity_type

    return None


# Country code to ROW region mapping for EXIOBASE fallbacks
COUNTRY_TO_ROW_REGION: Dict[str, str] = {
    # Asia-Pacific
    "CN": "ROW_ASIA", "JP": "ROW_ASIA", "KR": "ROW_ASIA", "TW": "ROW_ASIA",
    "IN": "ROW_ASIA", "ID": "ROW_ASIA", "MY": "ROW_ASIA", "TH": "ROW_ASIA",
    "SG": "ROW_ASIA", "PH": "ROW_ASIA", "VN": "ROW_ASIA", "BD": "ROW_ASIA",
    "PK": "ROW_ASIA", "NZ": "ROW_ASIA",  # NZ grouped with Asia-Pacific

    # Latin America
    "BR": "ROW_LATAM", "MX": "ROW_LATAM", "AR": "ROW_LATAM", "CL": "ROW_LATAM",
    "CO": "ROW_LATAM", "PE": "ROW_LATAM", "VE": "ROW_LATAM", "EC": "ROW_LATAM",

    # Europe (non-EU/EXIOBASE countries)
    "UA": "ROW_EUROPE", "RS": "ROW_EUROPE", "BY": "ROW_EUROPE", "MD": "ROW_EUROPE",
    "IS": "ROW_EUROPE", "AL": "ROW_EUROPE", "MK": "ROW_EUROPE", "BA": "ROW_EUROPE",
    "ME": "ROW_EUROPE",

    # Africa
    "ZA": "ROW_AFRICA", "NG": "ROW_AFRICA", "EG": "ROW_AFRICA", "KE": "ROW_AFRICA",
    "MA": "ROW_AFRICA", "DZ": "ROW_AFRICA", "GH": "ROW_AFRICA", "TZ": "ROW_AFRICA",
    "ET": "ROW_AFRICA", "UG": "ROW_AFRICA",

    # Middle East
    "SA": "ROW_MIDEAST", "AE": "ROW_MIDEAST", "IL": "ROW_MIDEAST", "QA": "ROW_MIDEAST",
    "KW": "ROW_MIDEAST", "OM": "ROW_MIDEAST", "BH": "ROW_MIDEAST", "JO": "ROW_MIDEAST",
    "LB": "ROW_MIDEAST", "IQ": "ROW_MIDEAST", "IR": "ROW_MIDEAST",
}

# Countries that are directly in EXIOBASE (no fallback needed)
EXIOBASE_DIRECT_COUNTRIES = {
    # EU-27 + UK
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK", "GB",
    # Other EXIOBASE countries
    "US", "JP", "CN", "CA", "KR", "BR", "IN", "MX", "RU",
    "AU", "CH", "TR", "TW", "NO", "ID", "ZA",
}


def get_country_fallback_chain(country_code: str) -> list[str]:
    """
    Get the country code fallback chain for EXIOBASE factor lookup.

    Returns a list of country codes to try, in order:
    1. Original country code (if in EXIOBASE directly)
    2. ROW region fallback
    3. GLOBAL fallback

    Args:
        country_code: ISO2 country code

    Returns:
        List of country codes to try in order.

    Examples:
        >>> get_country_fallback_chain("DE")
        ['DE', 'GLOBAL']

        >>> get_country_fallback_chain("SA")
        ['ROW_MIDEAST', 'GLOBAL']

        >>> get_country_fallback_chain("XX")
        ['GLOBAL']
    """
    fallback_chain = []

    # Normalize country code
    country_code = country_code.upper().strip() if country_code else "GLOBAL"

    # If country is directly in EXIOBASE, try it first
    if country_code in EXIOBASE_DIRECT_COUNTRIES:
        fallback_chain.append(country_code)
    elif country_code.startswith("ROW_"):
        # Already a ROW region
        fallback_chain.append(country_code)
    elif country_code in COUNTRY_TO_ROW_REGION:
        # Map to ROW region
        fallback_chain.append(COUNTRY_TO_ROW_REGION[country_code])

    # Always include GLOBAL as final fallback
    if "GLOBAL" not in fallback_chain:
        fallback_chain.append("GLOBAL")

    return fallback_chain


def reload_mappings():
    """Force reload of sector mappings from disk. Useful for testing."""
    global _sector_mapping_cache
    _sector_mapping_cache = None
    _load_sector_mapping()
