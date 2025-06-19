import csv
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict

# Configure logging for audit trail
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FactorRecord:
    factor: float
    unit: str
    confidence: float
    is_fallback: bool
    id: str
    source: str
    method_used: str
    activity_id: str
    region: str
    fallback_reason: Optional[str] = None

    def apply(self, item: Dict, method: str) -> float:
        if method == "quantity":
            quantity = item.get("quantity", 0)
        elif method == "spend":
            quantity = item.get("spend", 0)
        elif method == "distance":
            quantity = item.get("distance", 0)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if quantity <= 0:
            logger.warning(f"Zero or negative quantity for {item.get('activity', 'unknown')}: {quantity}")
            return 0.0

        normalized_quantity = self._normalize_units(quantity, item, method)
        co2e = normalized_quantity * self.factor

        logger.info(f"CO2e calculation: {normalized_quantity} x {self.factor} = {co2e} "
                    f"(activity: {self.activity_id}, region: {self.region}, "
                    f"confidence: {self.confidence}, fallback: {self.is_fallback})")
        return co2e

    def _normalize_units(self, quantity: float, item: Dict, method: str) -> float:
        input_unit = item.get("unit", "").lower()
        factor_unit = self.unit.lower()

        conversions = {
            ("t", "kg"): 1000,
            ("kg", "t"): 0.001,
            ("lb", "kg"): 0.453592,
            ("kg", "lb"): 2.20462,
            ("mi", "km"): 1.60934,
            ("km", "mi"): 0.621371,
            ("ft", "m"): 0.3048,
            ("m", "ft"): 3.28084,
            ("usd", "eur"): 1.0,
            ("eur", "usd"): 1.0,
        }

        factor_base_unit = self._extract_base_unit(factor_unit)

        if input_unit and factor_base_unit and input_unit != factor_base_unit:
            conversion_key = (input_unit, factor_base_unit)
            if conversion_key in conversions:
                converted_quantity = quantity * conversions[conversion_key]
                logger.info(f"Unit conversion: {quantity} {input_unit} -> {converted_quantity} {factor_base_unit}")
                return converted_quantity
            else:
                logger.warning(f"No conversion available for {input_unit} to {factor_base_unit}")

        return quantity

    def _extract_base_unit(self, factor_unit: str) -> str:
        unit_clean = re.sub(r'(kg|t|g)?co2e?/?', '', factor_unit)
        if '/' in unit_clean:
            return unit_clean.split('/')[-1].strip()
        return unit_clean.strip()

import csv
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional  # 👈 Add these

logger = logging.getLogger(__name__)


class EmissionFactorLoader:
    """
    Loads an emission-factor CSV and indexes it by activity-id → method.
    """

    def __init__(self, csv_path: Optional[Union[Path, str]] = None) -> None:
        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        # Accept str, Path or None
        if csv_path is None:
            csv_path = BASE_DIR / "data" / "raw" / "test_factors_v2025-06-04.csv"
        elif isinstance(csv_path, str):
            csv_path = Path(csv_path)

        self.csv_path: Path = csv_path

        if not self.csv_path.exists():
            raise FileNotFoundError(f"Emission factors CSV not found: {self.csv_path}")

        self.factors: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))
        self.global_averages: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))

        logger.info("Loading emission factors from: %s", self.csv_path)
        self._load_factors()
        logger.info(
            "Indexed %d activities across multiple regions and methods",
            len(self.factors)
        )

    # ───────────────────────────────────────────────────────────────
    # Helpers
    # ───────────────────────────────────────────────────────────────
    def _extract_version(self) -> str:
        """
        Extract ‘vYYYY-MM-DD’ or semver from filename, or fall back to file-mtime.
        """
        filename = self.csv_path.name
        m = re.search(r'v?\d{4}-\d{2}-\d{2}|v?\d+\.\d+\.\d+', filename)
        if m:
            return m.group()

        date_str = datetime.fromtimestamp(self.csv_path.stat().st_mtime).strftime("%Y-%m-%d")
        return f"v{date_str}"

    # ───────────────────────────────────────────────────────────────
    # Core loader
    # ───────────────────────────────────────────────────────────────
    def _load_factors(self) -> None:
        """
        Read the CSV and populate `self.factors` and `self.global_averages`.
        Expected columns: activity_id, region, method, factor, unit, [confidence]
        """
        with self.csv_path.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                activity_id = row['activity_id'].strip()
                region      = row['region'].strip().upper()
                method      = row['method'].strip().lower()
                factor_val  = float(row['factor'])
                unit        = row['unit'].strip()
                confidence  = float(row.get('confidence', 1.0))

                entry = {
                    "factor":     factor_val,
                    "unit":       unit,
                    "confidence": confidence,
                    "region":     region,
                    "method":     method,
                }

                # Index by activity_id ➜ method
                self.factors[activity_id][method].append(entry)

                # If global‐average, store separately
                if region in ("GLOBAL", "WORLD"):
                    self.global_averages[activity_id][method].append(entry)

    def lookup(self, item: Dict, method: str) -> FactorRecord:
        activity = item.get('activity', '').strip()
        region = item.get('region', '').strip().upper()
        method = method.lower()

        if not activity:
            raise ValueError("Item must include 'activity' field")

        factor_data = self._find_exact_match(activity, region, method)
        if factor_data:
            return self._create_factor_record(factor_data, activity, region, method, factor_data['confidence'], False)

        factor_data = self._find_regional_fallback(activity, region, method)
        if factor_data:
            return self._create_factor_record(factor_data, activity, region, method, 0.8, True,
                                              f"Regional fallback from {region} to {factor_data['region']}")

        factor_data = self._find_global_average(activity, method)
        if factor_data:
            return self._create_factor_record(factor_data, activity, region, method, factor_data['confidence'], True,
                                              f"Global average fallback (original region: {region})")

        raise ValueError(f"No emission factor found for activity '{activity}' with method '{method}' in region '{region}' or global averages")

    def _find_exact_match(self, activity: str, region: str, method: str) -> Optional[Dict]:
        if activity in self.factors and method in self.factors[activity]:
            for factor_data in self.factors[activity][method]:
                if factor_data['region'] == region:
                    return factor_data
        return None

    def _find_regional_fallback(self, activity: str, region: str, method: str) -> Optional[Dict]:
        regional_mapping = {
            'EU': ['EUROPE', 'EUR'],
            'US': ['NORTH_AMERICA', 'NAFTA'],
            'CN': ['ASIA', 'APAC'],
            'IN': ['ASIA', 'APAC'],
            'JP': ['ASIA', 'APAC'],
            'AU': ['OCEANIA', 'APAC'],
            'BR': ['SOUTH_AMERICA', 'LATAM'],
            'MX': ['NORTH_AMERICA', 'LATAM'],
            'ZA': ['AFRICA'],
            'NG': ['AFRICA'],
        }

        if activity in self.factors and method in self.factors[activity]:
            fallback_regions = regional_mapping.get(region, [])
            for factor_data in self.factors[activity][method]:
                if factor_data['region'] in fallback_regions:
                    logger.info(f"Regional fallback: {region} -> {factor_data['region']} for {activity}")
                    return factor_data
        return None

    def _find_global_average(self, activity: str, method: str) -> Optional[Dict]:
        if activity in self.global_averages and method in self.global_averages[activity]:
            return self.global_averages[activity][method][0]

        if activity in self.factors and method in self.factors[activity]:
            factors = self.factors[activity][method]
            if factors:
                avg_factor = sum(f['factor'] for f in factors) / len(factors)
                avg_confidence = sum(f['confidence'] for f in factors) / len(factors)
                logger.info(f"Calculated global average for {activity}: {avg_factor} (averaged from {len(factors)} regional factors)")
                return {
                    'factor': avg_factor,
                    'unit': factors[0]['unit'],
                    'confidence': avg_confidence,
                    'region': 'GLOBAL_CALCULATED',
                    'method': method
                }
        return None

    def _create_factor_record(self, factor_data: Dict, activity: str, region: str,
                              method: str, confidence: float, is_fallback: bool,
                              fallback_reason: Optional[str] = None) -> FactorRecord:
        record_id = str(uuid.uuid4())
        if is_fallback and fallback_reason:
            logger.warning(f"Fallback applied for {activity} ({region}, {method}): {fallback_reason}")

        return FactorRecord(
            factor=factor_data['factor'],
            unit=factor_data['unit'],
            confidence=confidence,
            is_fallback=is_fallback,
            id=record_id,
            source=str(self.csv_path),
            method_used=method,
            activity_id=activity,
            region=factor_data['region'],
            fallback_reason=fallback_reason
        )

    @property
    def version(self) -> str:
        return self._version

    @version.setter
    def version(self, value: str):
        self._version = value

    def get_available_activities(self) -> List[str]:
        return list(self.factors.keys())

    def get_coverage_report(self) -> Dict[str, Dict]:
        report = {}
        for activity in self.factors:
            report[activity] = {
                'methods': list(self.factors[activity].keys()),
                'regions': set()
            }
            for method in self.factors[activity]:
                for factor_data in self.factors[activity][method]:
                    report[activity]['regions'].add(factor_data['region'])
            report[activity]['regions'] = list(report[activity]['regions'])
        return report
    
import csv
from pathlib import Path
from typing import List, Dict


def load_factors(csv_path: str = "supplier_emissions.csv") -> List[Dict]:
    """
    Loads emission factors from a CSV file.
    Returns a list of dictionaries.
    """
    factors = []
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Emission factor file not found: {csv_path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            factors.append(row)

    return factors