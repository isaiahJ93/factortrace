# app/services/coaching_engine.py
"""
Coaching Engine Service.

Core assessment logic for supplier readiness evaluation.
Loads rules from YAML configs and calculates maturity bands.

Ethics Charter Compliance:
- NEVER expose score_raw to external consumers (bands only)
- ALWAYS include improvement_actions in assessments
- Use growth-focused language in rationales

See docs/features/coaching-layer.md for specification.
See docs/product/ethics-incentives.md for binding constraints.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache

import yaml
from sqlalchemy.orm import Session

from app.models.coaching import (
    ReadinessBand,
    DimensionType,
    ProgressTrend,
    SupplierReadiness,
    CoachingAcknowledgment,
    ActionStatus,
)
from app.schemas.coaching import (
    DimensionScore,
    ImprovementAction,
    SupplierReadinessResponse,
    CoachingPassport,
    RegimeSummary,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

SUPPORTED_REGIMES = ["csrd", "cbam", "eudr", "issb"]
BAND_ORDER = ["foundational", "emerging", "advanced", "leader"]
CONFIGS_DIR = Path(__file__).parent.parent.parent / "configs" / "coaching"


# =============================================================================
# YAML LOADER
# =============================================================================

@lru_cache(maxsize=10)
def _load_regime_rules(regime: str) -> Optional[Dict[str, Any]]:
    """
    Load and cache YAML config for a regime.

    Returns None if config doesn't exist.
    """
    config_path = CONFIGS_DIR / f"{regime}.yaml"
    if not config_path.exists():
        logger.warning(f"No coaching config found for regime: {regime}")
        return None

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded coaching rules for {regime} v{config.get('version', '?')}")
        return config
    except Exception as e:
        logger.error(f"Failed to load coaching config for {regime}: {e}")
        return None


def clear_rules_cache():
    """Clear the rules cache (useful for testing or hot-reloading)."""
    _load_regime_rules.cache_clear()


# =============================================================================
# METRICS COLLECTION
# =============================================================================

def _collect_supplier_metrics(
    db: Session,
    tenant_id: str,
    regime: str,
) -> Dict[str, float]:
    """
    Collect metrics for a supplier's data for assessment.

    This is a placeholder that should be connected to actual
    data sources (wizard sessions, emissions, etc.)

    Returns dict of metric_name -> value (0.0 to 1.0 normalized)
    """
    # TODO: Connect to real data sources
    # For now, return placeholder metrics for demonstration

    # In production, this would query:
    # - WizardSession for data coverage
    # - EmissionRecord for methodology analysis
    # - Evidence documents for audit trail
    # - Tenant settings for governance maturity

    # Placeholder implementation
    metrics = {
        # Data coverage
        "scope1_complete": 0.0,
        "scope2_complete": 0.0,
        "scope3_coverage": 0.0,

        # Methodology
        "spend_based_pct": 1.0,  # 100% spend-based by default
        "activity_based_pct": 0.0,
        "supplier_specific_pct": 0.0,

        # Governance
        "has_assigned_owner": 0.0,
        "has_review_process": 0.0,
        "has_approval_workflow": 0.0,
        "has_training_program": 0.0,

        # Audit trail
        "evidence_attached_pct": 0.0,
        "source_documented_pct": 0.0,
        "lineage_complete_pct": 0.0,
    }

    # Try to fetch actual data from wizard sessions
    try:
        from app.models.wizard import ComplianceWizardSession, WizardStatus

        sessions = (
            db.query(ComplianceWizardSession)
            .filter(
                ComplianceWizardSession.tenant_id == tenant_id,
                ComplianceWizardSession.status == WizardStatus.COMPLETED,
            )
            .all()
        )

        if sessions:
            # Analyze completed sessions for metrics
            for session in sessions:
                if session.calculated_emissions:
                    emissions = session.calculated_emissions
                    # Check scope coverage
                    if emissions.get("scope1_tco2e", 0) > 0:
                        metrics["scope1_complete"] = 1.0
                    if emissions.get("scope2_tco2e", 0) > 0:
                        metrics["scope2_complete"] = 1.0
                    if emissions.get("scope3_tco2e", 0) > 0:
                        metrics["scope3_coverage"] = 0.5  # Partial coverage

                    # Check for evidence (signature = evidence of completion)
                    if session.signature:
                        metrics["evidence_attached_pct"] = 0.3

    except Exception as e:
        logger.warning(f"Error collecting metrics from wizard sessions: {e}")

    return metrics


# =============================================================================
# ASSESSMENT LOGIC
# =============================================================================

def _calculate_dimension_score(
    dimension_config: Dict[str, Any],
    metrics: Dict[str, float],
) -> Tuple[ReadinessBand, float, str]:
    """
    Calculate band for a single dimension.

    Returns (band, raw_score, rationale)
    """
    thresholds = dimension_config.get("thresholds", {})
    dimension_metrics = dimension_config.get("metrics", [])

    # Calculate weighted average of dimension metrics
    total_weight = 0.0
    weighted_sum = 0.0

    for metric_def in dimension_metrics:
        metric_name = metric_def.get("name")
        weight = metric_def.get("weight", 1.0)
        invert = metric_def.get("invert", False)

        value = metrics.get(metric_name, 0.0)
        if invert:
            value = 1.0 - value

        weighted_sum += value * weight
        total_weight += weight

    # Calculate raw score (0.0 to 1.0)
    raw_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Determine band from thresholds
    band = ReadinessBand.FOUNDATIONAL
    for band_name in ["leader", "advanced", "emerging", "foundational"]:
        threshold = thresholds.get(band_name, 0.0)
        if raw_score >= threshold:
            band = ReadinessBand(band_name)
            break

    # Apply any rules that override bands
    rules = dimension_config.get("rules", [])
    for rule in rules:
        condition = rule.get("condition")
        # Evaluate condition based on metrics
        if _evaluate_rule_condition(condition, metrics):
            if "max_band" in rule:
                max_band = ReadinessBand(rule["max_band"])
                if BAND_ORDER.index(band.value) > BAND_ORDER.index(max_band.value):
                    band = max_band
            if "min_band" in rule:
                min_band = ReadinessBand(rule["min_band"])
                if BAND_ORDER.index(band.value) < BAND_ORDER.index(min_band.value):
                    band = min_band

    # Generate rationale
    rationale = _generate_rationale(
        dimension_config,
        band,
        raw_score,
        metrics,
    )

    return band, raw_score, rationale


def _evaluate_rule_condition(condition: str, metrics: Dict[str, float]) -> bool:
    """Evaluate a rule condition against metrics."""
    if condition == "all_spend_based":
        return metrics.get("spend_based_pct", 0) >= 0.9
    elif condition == "has_activity_data":
        return metrics.get("activity_based_pct", 0) > 0.1
    elif condition == "majority_activity_based":
        return metrics.get("activity_based_pct", 0) >= 0.5
    elif condition == "has_supplier_specific":
        return metrics.get("supplier_specific_pct", 0) > 0.1
    else:
        return False


def _generate_rationale(
    dimension_config: Dict[str, Any],
    band: ReadinessBand,
    raw_score: float,
    metrics: Dict[str, float],
) -> str:
    """
    Generate human-readable rationale for a dimension score.

    Uses templates from config if available, otherwise generates default.
    """
    templates = dimension_config.get("rationale_templates", {})
    template = templates.get(band.value, "")

    if template:
        # Fill in placeholders
        coverage_pct = int(raw_score * 100)
        activity_pct = int(metrics.get("activity_based_pct", 0) * 100)
        evidence_pct = int(metrics.get("evidence_attached_pct", 0) * 100)

        return template.format(
            coverage=coverage_pct,
            activity_pct=activity_pct,
            evidence_pct=evidence_pct,
        ).strip()

    # Default rationale
    return f"Currently at {band.value} level. See improvement actions for next steps."


def _calculate_overall_band(
    dimension_scores: List[DimensionScore],
    config: Dict[str, Any],
) -> ReadinessBand:
    """
    Calculate overall band from dimension scores.

    Uses weighted average of dimension bands.
    """
    dimensions_config = config.get("dimensions", {})

    total_weight = 0.0
    weighted_sum = 0.0

    for dim_score in dimension_scores:
        dim_config = dimensions_config.get(dim_score.dimension, {})
        weight = dim_config.get("weight", 0.25)

        band_index = BAND_ORDER.index(dim_score.band)
        weighted_sum += band_index * weight
        total_weight += weight

    avg_index = weighted_sum / total_weight if total_weight > 0 else 0
    overall_index = min(int(avg_index), len(BAND_ORDER) - 1)

    return ReadinessBand(BAND_ORDER[overall_index])


def _get_applicable_actions(
    config: Dict[str, Any],
    dimension_scores: List[DimensionScore],
    completed_actions: List[str],
) -> List[ImprovementAction]:
    """
    Filter and prioritize improvement actions based on current bands.

    Returns actions that are:
    - Triggered by current band
    - Not yet completed
    - Have prerequisites met
    """
    actions_config = config.get("actions", [])
    dimension_bands = {ds.dimension: ds.band for ds in dimension_scores}

    applicable = []

    for action_def in actions_config:
        action_id = action_def.get("id")

        # Skip completed actions
        if action_id in completed_actions:
            continue

        # Check if action is triggered by current band
        trigger_band = action_def.get("trigger_band")
        dimension = action_def.get("dimension")

        current_band = dimension_bands.get(dimension, ReadinessBand.FOUNDATIONAL)
        if current_band.value != trigger_band:
            continue

        # Check prerequisites
        prerequisites = action_def.get("prerequisites", [])
        if not all(p in completed_actions for p in prerequisites):
            continue

        # Create action object
        action = ImprovementAction(
            id=action_id,
            regime=config.get("regime", "unknown"),
            dimension=dimension,
            title=action_def.get("title", ""),
            description=action_def.get("description", "").strip(),
            effort=action_def.get("effort", "medium"),
            impact=action_def.get("impact", "medium"),
            suggested_role=action_def.get("suggested_role", "Team Lead"),
            prerequisites=prerequisites,
        )
        applicable.append(action)

    # Sort by impact (critical > high > medium > low)
    impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    applicable.sort(key=lambda a: impact_order.get(a.impact, 2))

    return applicable


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================

class CoachingEngine:
    """
    Core coaching engine for supplier readiness assessment.

    Ethics-compliant: Only exposes bands, never raw scores.
    """

    def __init__(self):
        self._rules_cache = {}

    def load_rules(self, regime: str) -> Optional[Dict[str, Any]]:
        """Load rules for a regime (cached)."""
        return _load_regime_rules(regime)

    def assess_supplier(
        self,
        db: Session,
        *,
        tenant_id: str,
        regime: str,
    ) -> Optional[SupplierReadinessResponse]:
        """
        Perform full readiness assessment for a supplier.

        Returns SupplierReadinessResponse with bands and actions.
        Never returns raw scores (Ethics Charter compliance).
        """
        if regime not in SUPPORTED_REGIMES:
            logger.warning(f"Unsupported regime for assessment: {regime}")
            return None

        # Load rules
        config = self.load_rules(regime)
        if not config:
            logger.error(f"No config available for regime: {regime}")
            return None

        # Collect metrics
        metrics = _collect_supplier_metrics(db, tenant_id, regime)

        # Calculate dimension scores
        dimension_scores: List[DimensionScore] = []
        dimensions_config = config.get("dimensions", {})

        for dim_name, dim_config in dimensions_config.items():
            band, raw_score, rationale = _calculate_dimension_score(
                dim_config, metrics
            )
            dimension_scores.append(DimensionScore(
                dimension=dim_name,
                band=band.value,
                rationale=rationale,
            ))

        # Calculate overall band
        overall_band = _calculate_overall_band(dimension_scores, config)

        # Get completed actions for this tenant
        completed_actions = self._get_completed_actions(db, tenant_id, regime)

        # Get applicable improvement actions
        actions = _get_applicable_actions(config, dimension_scores, completed_actions)

        # Ensure at least one action (Ethics Charter requirement)
        if not actions:
            # Add a default "maintain excellence" action for leaders
            actions = [ImprovementAction(
                id=f"{regime}_maintain_excellence",
                regime=regime,
                dimension="data_coverage",
                title="Maintain Excellence",
                description="Continue your excellent practices and consider mentoring other suppliers in your network.",
                effort="low",
                impact="medium",
                suggested_role="Sustainability Lead",
                prerequisites=[],
            )]

        # Get previous assessment for trend
        previous = self._get_previous_assessment(db, tenant_id, regime)
        previous_band = previous.overall_band if previous else None
        progress_trend = self._calculate_trend(overall_band, previous_band)

        # Create and store assessment
        assessment = SupplierReadiness(
            tenant_id=tenant_id,
            regime=regime,
            overall_band=overall_band,
            previous_band=previous_band,
            progress_trend=progress_trend,
            dimension_scores=[ds.model_dump() for ds in dimension_scores],
            improvement_actions=[a.model_dump() for a in actions],
            methodology_version=config.get("version", "1.0"),
            confidence_level="medium",
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        # Return response (without raw scores)
        return SupplierReadinessResponse(
            id=str(assessment.id),
            tenant_id=tenant_id,
            regime=regime,
            overall_band=overall_band.value,
            dimension_scores=dimension_scores,
            improvement_actions=actions,
            assessed_at=assessment.assessed_at,
            previous_band=previous_band.value if previous_band else None,
            progress_trend=progress_trend.value,
            methodology_version=config.get("version"),
            confidence_level="medium",
        )

    def _get_completed_actions(
        self,
        db: Session,
        tenant_id: str,
        regime: str,
    ) -> List[str]:
        """Get list of completed action IDs for a tenant."""
        completed = (
            db.query(CoachingAcknowledgment.action_id)
            .filter(
                CoachingAcknowledgment.tenant_id == tenant_id,
                CoachingAcknowledgment.regime == regime,
                CoachingAcknowledgment.status == ActionStatus.COMPLETED,
            )
            .all()
        )
        return [c[0] for c in completed]

    def _get_previous_assessment(
        self,
        db: Session,
        tenant_id: str,
        regime: str,
    ) -> Optional[SupplierReadiness]:
        """Get most recent previous assessment."""
        return (
            db.query(SupplierReadiness)
            .filter(
                SupplierReadiness.tenant_id == tenant_id,
                SupplierReadiness.regime == regime,
            )
            .order_by(SupplierReadiness.assessed_at.desc())
            .first()
        )

    def _calculate_trend(
        self,
        current_band: ReadinessBand,
        previous_band: Optional[ReadinessBand],
    ) -> ProgressTrend:
        """Calculate progress trend from band comparison."""
        if previous_band is None:
            return ProgressTrend.STABLE

        current_idx = BAND_ORDER.index(current_band.value)
        previous_idx = BAND_ORDER.index(previous_band.value)

        if current_idx > previous_idx:
            return ProgressTrend.IMPROVING
        elif current_idx < previous_idx:
            return ProgressTrend.DECLINING
        else:
            return ProgressTrend.STABLE

    def get_coaching_passport(
        self,
        db: Session,
        *,
        tenant_id: str,
    ) -> CoachingPassport:
        """
        Get multi-regime coaching passport for a supplier.

        Shows readiness across all supported regimes.
        """
        regime_summaries = []

        for regime in SUPPORTED_REGIMES:
            assessment = self._get_previous_assessment(db, tenant_id, regime)

            if assessment:
                regime_summaries.append(RegimeSummary(
                    regime=regime,
                    band=assessment.overall_band.value,
                    trend=assessment.progress_trend.value if assessment.progress_trend else None,
                    last_assessed=assessment.assessed_at,
                ))
            else:
                regime_summaries.append(RegimeSummary(
                    regime=regime,
                    band=None,
                    trend=None,
                    last_assessed=None,
                ))

        # Calculate overall maturity (from assessed regimes)
        assessed = [r for r in regime_summaries if r.band]
        overall_maturity = None
        last_assessed = None

        if assessed:
            bands = [r.band for r in assessed]
            # Use lowest band as overall (conservative)
            band_indices = [BAND_ORDER.index(b) for b in bands]
            overall_maturity = BAND_ORDER[min(band_indices)]
            last_assessed = max(r.last_assessed for r in assessed if r.last_assessed)

        return CoachingPassport(
            tenant_id=tenant_id,
            regimes=regime_summaries,
            overall_maturity=overall_maturity,
            last_assessed=last_assessed,
        )


# =============================================================================
# SINGLETON
# =============================================================================

_coaching_engine: Optional[CoachingEngine] = None


def get_coaching_engine() -> CoachingEngine:
    """Get singleton coaching engine instance."""
    global _coaching_engine
    if _coaching_engine is None:
        _coaching_engine = CoachingEngine()
    return _coaching_engine


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CoachingEngine",
    "get_coaching_engine",
    "clear_rules_cache",
    "SUPPORTED_REGIMES",
]
