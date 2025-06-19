from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid

# ─────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────

@dataclass
class ItemResult:
    activity_id: str
    original_input: Dict[str, Any]
    factor_id: str
    factor_source: str
    method_used: str
    co2e: float
    unit: str = "kgCO2e"
    confidence: float = 1.0
    is_fallback: bool = False


@dataclass
class CalcResult:
    calc_uuid: str
    generated_at: str
    total_co2e: float
    line_items: List[ItemResult]
    fallback_used: bool
    factor_dataset_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ─────────────────────────────────────────────────────────────
# Main calculator class
# ─────────────────────────────────────────────────────────────

class TraceCalc:
    def __init__(self, factor_loader: "EmissionFactorLoader") -> None:
        self.factor_loader = factor_loader

    def calculate(self, items: List[Dict[str, Any]], method: str = "auto") -> CalcResult:
        results: List[ItemResult] = []
        total = 0.0
        fallback_flag = False

        for idx, item in enumerate(items):
            factor_record = self.factor_loader.lookup(item, method)
            co2e = factor_record.apply(item, method)
            if factor_record.is_fallback:
                fallback_flag = True

            results.append(
                ItemResult(
                    activity_id=item.get("activity", f"item-{idx+1}"),
                    original_input=item,
                    factor_id=factor_record.id,
                    factor_source=factor_record.source,
                    method_used=factor_record.method_used,
                    co2e=co2e,
                    confidence=factor_record.confidence,
                    is_fallback=factor_record.is_fallback,
                )
            )
            total += co2e

        return CalcResult(
            calc_uuid=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_co2e=round(total, 6),
            line_items=results,
            fallback_used=fallback_flag,
            factor_dataset_version=self.factor_loader.version,
        )

# ─────────────────────────────────────────────────────────────
# CLI / Test Runner
# ─────────────────────────────────────────────────────────────

@dataclass
class ItemResult:
    activity_id: str
    original_input: Dict[str, Any]
    factor_id: str
    factor_source: str
    method_used: str
    co2e: float
    unit: str = "kgCO2e"
    confidence: float = 1.0
    is_fallback: bool = False


@dataclass
class CalcResult:
    calc_uuid: str
    generated_at: str
    total_co2e: float
    line_items: List[ItemResult]
    fallback_used: bool
    factor_dataset_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TraceCalc:
    def __init__(self, factor_loader: "EmissionFactorLoader") -> None:
        self.factor_loader = factor_loader

    def calculate(self, items: List[Dict[str, Any]], method: str = "auto") -> CalcResult:
        results: List[ItemResult] = []
        total = 0.0
        fallback_flag = False

        for idx, item in enumerate(items):
            factor_record = self.factor_loader.lookup(item, method)
            co2e = factor_record.apply(item, method)
            if factor_record.is_fallback:
                fallback_flag = True

            results.append(
                ItemResult(
                    activity_id=item.get("activity", f"item-{idx+1}"),
                    original_input=item,
                    factor_id=factor_record.id,
                    factor_source=factor_record.source,
                    method_used=factor_record.method_used,
                    co2e=co2e,
                    confidence=factor_record.confidence,
                    is_fallback=factor_record.is_fallback,
                )
            )
            total += co2e

        return CalcResult(
            calc_uuid=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_co2e=round(total, 6),
            line_items=results,
            fallback_used=fallback_flag,
            factor_dataset_version=self.factor_loader.version,
        )

if __name__ == "__main__":
    from factor_loader import EmissionFactorLoader

    loader = EmissionFactorLoader("data/raw/test_factors_v2025-06-04.csv")

    demo_items = [
    {"activity": "cotton_fabric", "quantity": 100, "unit": "kg", "region": "EU"},
    {"activity": "diesel_transport", "distance": 500, "unit": "km", "region": "MENA"},
    {"activity": "cotton_fabric", "quantity": 50, "unit": "kg", "region": "BR"},
]