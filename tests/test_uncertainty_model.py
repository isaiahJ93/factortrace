from factortrace.models.uncertainty_model import UncertaintyAssessment, UncertaintyDistributionEnum
def test_uncertainty_distribution():
    u = UncertaintyAssessment(
        uncertainty_percentage=10.0,
        confidence_level=95.0,
        distribution=UncertaintyDistributionEnum.LOGNORMAL,
        method="Monte Carlo"
    )
    assert u.uncertainty_percentage == 10.0
    assert u.confidence_level == 95