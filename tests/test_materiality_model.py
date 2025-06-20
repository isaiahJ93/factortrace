from datetime import date
from factortrace.models.materiality import MaterialityAssessment, MaterialityType

def test_materiality_parsing():
    m = MaterialityAssessment(
        assessment_date=date(2025, 6, 12),
        materiality_type=MaterialityType.double_materiality,
        impact_score=3.5,
        impact_magnitude=3.5,
        impact_likelihood=0.8,
        impact_scope="ENVIRONMENTAL",
        financial_score=2.8,
        financial_impact=1_500_000.0,
        financial_likelihood=0.6,
        financial_time_horizon="MEDIUM_TERM",
        materiality_threshold=0.7,
        is_material=True,
        justification="High climate impact risk",
        time_horizon="LONG_TERM",
        affected_stakeholders=["investors", "NGOs"],
        risk_type="PHYSICAL",
        reporting_period="2025"
    assert m.is_material is True