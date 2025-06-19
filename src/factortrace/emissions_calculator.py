class EliteEmissionsCalculator:
    def calculate_emissions(self, activity_data, activity_unit, emission_factor, scope):
        class Result:
            def get_central_estimate(self):
                return activity_data * 0.233  # dummy calculation for now
        return Result()
    
def calculate_emissions(activity_value: float, emission_factor: float) -> float:
    """
    Basic stub — multiply activity by emission factor to get CO2e.
    """
    return activity_value * emission_factor