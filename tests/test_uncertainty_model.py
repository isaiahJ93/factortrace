from factortrace.models import UncertaintyAssessment
from factortrace.shared_enums import UncertaintyDistributionEnum

u = UncertaintyAssessment(
    uncertainty_percentage=10.0,
    confidence_level=95.0,
    distribution=UncertaintyDistributionEnum.LOGNORMAL,
    method="Monte Carlo"

assert u.uncertainty_percentage == 10.0
assert u.confidence_level == 95.0
assert u.distribution == UncertaintyDistributionEnum.LOGNORMAL
assert u.method == "Monte Carlo"