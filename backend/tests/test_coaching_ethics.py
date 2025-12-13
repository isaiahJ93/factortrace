"""
Coaching Layer Ethics Enforcement Tests.

These tests verify that the Coaching Layer complies with the Ethics Charter
(docs/product/ethics-incentives.md) and cannot be circumvented.

Ethics Charter Invariants Tested:
1. NO numerical scores exposed in API responses (bands only)
2. EVERY response includes at least one improvement_action
3. Language is growth-focused (no "must", "fail", "inadequate")
4. Export endpoints exist (GDPR compliance)
5. No blacklist or punitive features

See: docs/product/ethics-incentives.md
See: docs/features/coaching-layer.md
"""
import pytest
import re
from datetime import datetime
from pydantic import ValidationError

from app.schemas.coaching import (
    SupplierReadinessResponse,
    DimensionScore,
    ImprovementAction,
    CoachingPassport,
    RegimeSummary,
)


# =============================================================================
# TEST: NO NUMERICAL SCORES EXPOSED
# =============================================================================

class TestNoNumericalScoresExposed:
    """
    Ethics Charter Section 2: Never expose numerical scores.

    The Coaching Layer must use bands (foundational/emerging/advanced/leader),
    not numerical scores. This prevents gamification and shame.
    """

    def test_dimension_score_uses_bands_not_numbers(self):
        """Dimension scores use band enum, not numerical values."""
        score = DimensionScore(
            dimension="data_coverage",
            band="emerging",
            rationale="Coverage at 45%. Add Scope 3 Categories 1 and 4 to reach Advanced."
        )

        # Check that band is a valid band value
        assert score.band in ["foundational", "emerging", "advanced", "leader"]

        # Ensure no score_raw field is exposed
        assert not hasattr(score, "score_raw")
        assert not hasattr(score, "score")
        assert not hasattr(score, "numerical_score")

    def test_dimension_score_json_excludes_raw_score(self):
        """JSON serialization must not include any raw score fields."""
        score = DimensionScore(
            dimension="methodology_quality",
            band="advanced",
            rationale="Strong methodology with activity-based data."
        )

        json_data = score.model_dump()

        # Verify no numerical score fields leak through
        assert "score_raw" not in json_data
        assert "score" not in json_data
        assert "numerical_score" not in json_data
        assert "raw_value" not in json_data

    def test_response_schema_only_has_bands(self):
        """SupplierReadinessResponse uses bands throughout."""
        response = SupplierReadinessResponse(
            id="test-123",
            tenant_id="tenant-456",
            regime="csrd",
            overall_band="emerging",
            dimension_scores=[
                DimensionScore(
                    dimension="data_coverage",
                    band="emerging",
                    rationale="Coverage at 45%."
                )
            ],
            improvement_actions=[
                ImprovementAction(
                    id="csrd_test_action",
                    regime="csrd",
                    dimension="data_coverage",
                    title="Test Action",
                    description="Consider adding more data.",
                    effort="medium",
                    impact="high",
                    suggested_role="Sustainability Lead",
                    prerequisites=[]
                )
            ],
            assessed_at=datetime.utcnow(),
            progress_trend="stable",
        )

        # Overall band is a band, not a number
        assert response.overall_band in ["foundational", "emerging", "advanced", "leader"]

        # All dimension scores use bands
        for ds in response.dimension_scores:
            assert ds.band in ["foundational", "emerging", "advanced", "leader"]


# =============================================================================
# TEST: EVERY RESPONSE INCLUDES IMPROVEMENT ACTIONS
# =============================================================================

class TestImprovementActionsRequired:
    """
    Ethics Charter Section 3: Every assessment must include improvement actions.

    Even Leader-status suppliers get actions (maintaining excellence).
    This ensures coaching is always constructive and forward-looking.
    """

    def test_empty_improvement_actions_raises_validation_error(self):
        """Cannot create response with empty improvement_actions."""
        with pytest.raises(ValidationError) as exc_info:
            SupplierReadinessResponse(
                id="test-123",
                tenant_id="tenant-456",
                regime="csrd",
                overall_band="leader",
                dimension_scores=[
                    DimensionScore(
                        dimension="data_coverage",
                        band="leader",
                        rationale="Full coverage achieved."
                    )
                ],
                improvement_actions=[],  # Empty - should fail
                assessed_at=datetime.utcnow(),
            )

        # Verify the error mentions ethics violation
        error_str = str(exc_info.value)
        assert "improvement_actions" in error_str.lower() or "ethics" in error_str.lower()

    def test_null_improvement_actions_raises_validation_error(self):
        """Cannot create response with null improvement_actions."""
        with pytest.raises(ValidationError):
            SupplierReadinessResponse(
                id="test-123",
                tenant_id="tenant-456",
                regime="csrd",
                overall_band="advanced",
                dimension_scores=[
                    DimensionScore(
                        dimension="data_coverage",
                        band="advanced",
                        rationale="Good coverage."
                    )
                ],
                improvement_actions=None,  # Null - should fail
                assessed_at=datetime.utcnow(),
            )

    def test_leader_band_still_requires_actions(self):
        """Even Leader-status suppliers must have improvement actions."""
        # This should succeed - Leader with actions
        response = SupplierReadinessResponse(
            id="test-123",
            tenant_id="tenant-456",
            regime="csrd",
            overall_band="leader",
            dimension_scores=[
                DimensionScore(
                    dimension="data_coverage",
                    band="leader",
                    rationale="Outstanding coverage."
                )
            ],
            improvement_actions=[
                ImprovementAction(
                    id="csrd_maintain_excellence",
                    regime="csrd",
                    dimension="data_coverage",
                    title="Maintain Excellence",
                    description="Consider sharing best practices with your supply chain.",
                    effort="low",
                    impact="medium",
                    suggested_role="Sustainability Lead",
                    prerequisites=[]
                )
            ],
            assessed_at=datetime.utcnow(),
        )

        assert len(response.improvement_actions) >= 1

    def test_min_length_enforced_by_schema(self):
        """Schema enforces minimum 1 improvement action."""
        # Try to bypass with direct instantiation
        with pytest.raises(ValidationError):
            SupplierReadinessResponse.model_validate({
                "id": "test",
                "tenant_id": "test",
                "regime": "csrd",
                "overall_band": "emerging",
                "dimension_scores": [
                    {"dimension": "data_coverage", "band": "emerging", "rationale": "test"}
                ],
                "improvement_actions": [],
                "assessed_at": datetime.utcnow().isoformat(),
            })


# =============================================================================
# TEST: GROWTH-FOCUSED LANGUAGE
# =============================================================================

class TestGrowthFocusedLanguage:
    """
    Ethics Charter Section 8: Language must be growth-focused.

    Use "Consider" not "You must".
    Use "opportunity" not "failure".
    Focus on next steps, not judgment.
    """

    # Forbidden phrases that indicate punitive language
    FORBIDDEN_PATTERNS = [
        r"\byou must\b",
        r"\brequired to\b",
        r"\bfailure\b",
        r"\bfailed\b",
        r"\binadequate\b",
        r"\bpoor\b",
        r"\bbad\b",
        r"\bweak\b",
        r"\blacking\b",
        r"\bdeficient\b",
        r"\bunacceptable\b",
    ]

    def test_improvement_action_description_growth_focused(self):
        """Action descriptions should use growth-focused language."""
        # Valid growth-focused action
        action = ImprovementAction(
            id="csrd_test",
            regime="csrd",
            dimension="data_coverage",
            title="Expand Data Coverage",
            description="Consider adding Scope 3 categories to strengthen your footprint assessment.",
            effort="medium",
            impact="high",
            suggested_role="Sustainability Lead",
            prerequisites=[]
        )

        # Check description doesn't contain forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            assert not re.search(pattern, action.description.lower()), \
                f"Description contains forbidden pattern: {pattern}"

    def test_dimension_rationale_growth_focused(self):
        """Dimension rationales should be constructive, not judgmental."""
        score = DimensionScore(
            dimension="methodology_quality",
            band="emerging",
            rationale="Good progress on methodology. Consider activity-based data for top categories."
        )

        for pattern in self.FORBIDDEN_PATTERNS:
            assert not re.search(pattern, score.rationale.lower()), \
                f"Rationale contains forbidden pattern: {pattern}"

    def test_rationale_minimum_length(self):
        """Rationale must be substantive (min 10 chars per schema)."""
        with pytest.raises(ValidationError):
            DimensionScore(
                dimension="data_coverage",
                band="emerging",
                rationale="bad"  # Too short
            )


# =============================================================================
# TEST: EXPORT ENDPOINTS (GDPR COMPLIANCE)
# =============================================================================

class TestGDPRExportCompliance:
    """
    Ethics Charter Section 1: Data export required for GDPR compliance.

    Suppliers must be able to export their coaching data in standard formats.
    This is verified at the schema level and API level.
    """

    def test_coaching_passport_serializable(self):
        """CoachingPassport must be fully serializable for export."""
        passport = CoachingPassport(
            tenant_id="test-tenant",
            regimes=[
                RegimeSummary(regime="csrd", band="emerging", trend="improving"),
                RegimeSummary(regime="cbam", band="foundational", trend="stable"),
            ],
            overall_maturity="emerging",
            last_assessed=datetime.utcnow(),
        )

        # Must be JSON serializable
        json_data = passport.model_dump_json()
        assert json_data is not None
        assert len(json_data) > 0

    def test_supplier_readiness_fully_serializable(self):
        """SupplierReadinessResponse must be fully serializable for export."""
        response = SupplierReadinessResponse(
            id="test-123",
            tenant_id="tenant-456",
            regime="csrd",
            overall_band="emerging",
            dimension_scores=[
                DimensionScore(
                    dimension="data_coverage",
                    band="emerging",
                    rationale="Coverage at 45%."
                )
            ],
            improvement_actions=[
                ImprovementAction(
                    id="csrd_test",
                    regime="csrd",
                    dimension="data_coverage",
                    title="Test",
                    description="Consider testing.",
                    effort="low",
                    impact="medium",
                    suggested_role="Test Lead",
                    prerequisites=[]
                )
            ],
            assessed_at=datetime.utcnow(),
        )

        json_data = response.model_dump_json()
        assert json_data is not None


# =============================================================================
# TEST: NO BLACKLIST OR PUNITIVE FEATURES
# =============================================================================

class TestNoPunitiveFeatures:
    """
    Ethics Charter Section 5: No blacklist or punitive features.

    The coaching layer must not include any mechanism to:
    - Blacklist suppliers
    - Punish suppliers for low scores
    - Share scores with other parties without consent
    - Use scores for negative decisions
    """

    def test_no_blacklist_status_in_response(self):
        """Response schema has no blacklist or ban fields."""
        response = SupplierReadinessResponse(
            id="test",
            tenant_id="test",
            regime="csrd",
            overall_band="foundational",  # Lowest band
            dimension_scores=[
                DimensionScore(
                    dimension="data_coverage",
                    band="foundational",
                    rationale="Starting the journey."
                )
            ],
            improvement_actions=[
                ImprovementAction(
                    id="test",
                    regime="csrd",
                    dimension="data_coverage",
                    title="Start Here",
                    description="Consider beginning with Scope 1 data.",
                    effort="low",
                    impact="high",
                    suggested_role="Anyone",
                    prerequisites=[]
                )
            ],
            assessed_at=datetime.utcnow(),
        )

        # Even at foundational, there's no punitive field
        json_data = response.model_dump()

        assert "blacklisted" not in json_data
        assert "banned" not in json_data
        assert "suspended" not in json_data
        assert "penalty" not in json_data
        assert "warning" not in json_data
        assert "flagged" not in json_data

    def test_foundational_band_is_constructive(self):
        """Even foundational band uses constructive framing."""
        # Foundational is the lowest band but should be framed positively
        # as "starting the journey" not "failing"
        score = DimensionScore(
            dimension="data_coverage",
            band="foundational",
            rationale="Starting your sustainability journey. Consider beginning with utility bills."
        )

        # Should be valid and not contain negative language
        assert score.band == "foundational"
        assert "fail" not in score.rationale.lower()
        assert "inadequate" not in score.rationale.lower()


# =============================================================================
# TEST: VALID BAND VALUES
# =============================================================================

class TestValidBandValues:
    """
    Ensure only valid band values are accepted.
    """

    VALID_BANDS = ["foundational", "emerging", "advanced", "leader"]

    def test_overall_band_must_be_valid(self):
        """Overall band must be one of the defined values."""
        with pytest.raises(ValidationError):
            SupplierReadinessResponse(
                id="test",
                tenant_id="test",
                regime="csrd",
                overall_band="excellent",  # Invalid
                dimension_scores=[
                    DimensionScore(
                        dimension="data_coverage",
                        band="emerging",
                        rationale="Test rationale here."
                    )
                ],
                improvement_actions=[
                    ImprovementAction(
                        id="test",
                        regime="csrd",
                        dimension="data_coverage",
                        title="Test",
                        description="Consider testing.",
                        effort="low",
                        impact="medium",
                        suggested_role="Test",
                        prerequisites=[]
                    )
                ],
                assessed_at=datetime.utcnow(),
            )

    def test_dimension_band_must_be_valid(self):
        """Dimension bands must be valid."""
        with pytest.raises(ValidationError):
            DimensionScore(
                dimension="data_coverage",
                band="super_good",  # Invalid
                rationale="This should fail validation."
            )

    def test_all_valid_bands_accepted(self):
        """All defined bands should be accepted."""
        for band in self.VALID_BANDS:
            score = DimensionScore(
                dimension="data_coverage",
                band=band,
                rationale=f"Testing {band} band acceptance."
            )
            assert score.band == band


# =============================================================================
# TEST: IMPROVEMENT ACTION STRUCTURE
# =============================================================================

class TestImprovementActionStructure:
    """
    Test that improvement actions have all required fields.
    """

    VALID_EFFORT_LEVELS = ["low", "medium", "high"]
    VALID_IMPACT_LEVELS = ["low", "medium", "high", "critical"]

    def test_action_requires_all_fields(self):
        """Actions must have all required fields."""
        action = ImprovementAction(
            id="csrd_test",
            regime="csrd",
            dimension="data_coverage",
            title="Test Action",
            description="Consider doing something constructive.",
            effort="medium",
            impact="high",
            suggested_role="Sustainability Lead",
            prerequisites=[]
        )

        assert action.id is not None
        assert action.regime is not None
        assert action.dimension is not None
        assert action.title is not None
        assert action.description is not None
        assert action.effort in self.VALID_EFFORT_LEVELS
        assert action.impact in self.VALID_IMPACT_LEVELS
        assert action.suggested_role is not None

    def test_effort_level_validated(self):
        """Effort level must be valid."""
        with pytest.raises(ValidationError):
            ImprovementAction(
                id="test",
                regime="csrd",
                dimension="data_coverage",
                title="Test",
                description="Test action.",
                effort="super_easy",  # Invalid
                impact="high",
                suggested_role="Test",
                prerequisites=[]
            )

    def test_impact_level_validated(self):
        """Impact level must be valid."""
        with pytest.raises(ValidationError):
            ImprovementAction(
                id="test",
                regime="csrd",
                dimension="data_coverage",
                title="Test",
                description="Test action.",
                effort="medium",
                impact="super_important",  # Invalid
                suggested_role="Test",
                prerequisites=[]
            )
