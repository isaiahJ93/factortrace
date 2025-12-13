#!/usr/bin/env python
"""Simple ethics enforcement tests - standalone."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pydantic import ValidationError

from app.schemas.coaching import (
    SupplierReadinessResponse,
    DimensionScore,
    ImprovementAction,
    CoachingPassport,
    RegimeSummary,
)

print("=== Testing Ethics Charter Compliance ===")

# Test 1: Empty improvement_actions should fail
print("Test 1: Empty improvement_actions validation...", end=" ")
try:
    SupplierReadinessResponse(
        id="test",
        tenant_id="test",
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
    print("FAIL - Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print("PASS")

# Test 2: Valid response with actions
print("Test 2: Valid response with actions...", end=" ")
try:
    response = SupplierReadinessResponse(
        id="test",
        tenant_id="test",
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
                title="Test Action",
                description="Consider adding more data.",
                effort="medium",
                impact="high",
                suggested_role="Sustainability Lead",
                prerequisites=[]
            )
        ],
        assessed_at=datetime.utcnow(),
    )
    print("PASS")
except Exception as e:
    print(f"FAIL - {e}")
    sys.exit(1)

# Test 3: No score_raw in JSON output
print("Test 3: No score_raw in JSON output...", end=" ")
json_data = response.model_dump()
found_score = False
for key in json_data.keys():
    if "score" in key.lower() and key != "dimension_scores":
        found_score = True
        break
if found_score:
    print("FAIL - score field found")
else:
    print("PASS")

# Test 4: Invalid band rejected
print("Test 4: Invalid band rejected...", end=" ")
try:
    SupplierReadinessResponse(
        id="test",
        tenant_id="test",
        regime="csrd",
        overall_band="super_excellent",  # Invalid
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
    print("FAIL - Should have rejected invalid band")
    sys.exit(1)
except ValidationError:
    print("PASS")

# Test 5: Rationale minimum length enforced
print("Test 5: Rationale minimum length enforced...", end=" ")
try:
    DimensionScore(
        dimension="data_coverage",
        band="emerging",
        rationale="bad"  # Too short
    )
    print("FAIL - Should have rejected short rationale")
    sys.exit(1)
except ValidationError:
    print("PASS")

# Test 6: Valid effort/impact levels
print("Test 6: Invalid effort level rejected...", end=" ")
try:
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
    print("FAIL - Should have rejected invalid effort")
    sys.exit(1)
except ValidationError:
    print("PASS")

# Test 7: CoachingPassport serializable
print("Test 7: CoachingPassport serializable...", end=" ")
passport = CoachingPassport(
    tenant_id="test",
    regimes=[
        RegimeSummary(regime="csrd", band="emerging", trend="improving"),
    ],
    overall_maturity="emerging",
)
json_output = passport.model_dump_json()
if json_output and len(json_output) > 0:
    print("PASS")
else:
    print("FAIL - Empty JSON output")
    sys.exit(1)

# Test 8: All valid bands accepted
print("Test 8: All valid bands accepted...", end=" ")
valid_bands = ["foundational", "emerging", "advanced", "leader"]
for band in valid_bands:
    try:
        DimensionScore(
            dimension="data_coverage",
            band=band,
            rationale=f"Testing {band} band acceptance."
        )
    except ValidationError:
        print(f"FAIL - Band {band} rejected")
        sys.exit(1)
print("PASS")

print()
print("=== All Ethics Tests Passed ===")
