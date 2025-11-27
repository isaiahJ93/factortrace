
# =====================================================
# EMISSION CALCULATION VALIDATION
# =====================================================

def validate_emission_calculation(activity_type: str, quantity: float, unit: str, factor: dict) -> dict:
    """Validate emission calculation for GHG Protocol compliance"""
    
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "data_quality_tier": 1
    }
    
    # Check unit compatibility
    if unit.lower() != factor.get("unit", "").lower():
        # Check if conversion is possible
        if activity_type == "natural_gas" and unit == "m³" and factor["unit"] == "kWh":
            validation_result["warnings"].append(
                f"Unit conversion applied: {unit} to {factor['unit']} (factor: 10.55)"
            )
        elif activity_type == "natural_gas" and unit == "kWh" and factor["unit"] == "m³":
            validation_result["warnings"].append(
                f"Unit conversion applied: {unit} to {factor['unit']} (factor: 0.0948)"
            )
        else:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                f"Unit mismatch: activity uses {unit}, factor expects {factor['unit']}"
            )
    
    # Check for negative values
    if quantity < 0:
        validation_result["is_valid"] = False
        validation_result["errors"].append("Negative quantity not allowed")
    
    if factor.get("factor", 0) < 0 and "avoided" not in activity_type.lower():
        validation_result["warnings"].append("Negative emission factor detected")
    
    # Check factor age (if source year is available)
    source = factor.get("source", "")
    if "2024" in source:
        validation_result["data_quality_tier"] = 1
    elif "2023" in source:
        validation_result["data_quality_tier"] = 2
    else:
        validation_result["data_quality_tier"] = 3
        validation_result["warnings"].append("Emission factor may be outdated")
    
    # Check uncertainty
    uncertainty = factor.get("uncertainty", 0)
    if uncertainty > 50:
        validation_result["warnings"].append(f"High uncertainty factor: {uncertainty}%")
    
    return validation_result

def ensure_category_3_calculation(scope1_2_activities: list) -> list:
    """Ensure Category 3 emissions are calculated for all fuel and energy"""
    
    category_3_activities = []
    
    for activity in scope1_2_activities:
        activity_type = activity.get("activity_type", "").lower()
        
        # Check if this activity should generate Category 3 emissions
        if any(fuel in activity_type for fuel in ["natural_gas", "diesel", "petrol", "fuel_oil", "propane"]):
            # This is a fuel combustion activity - needs WTT
            wtt_activity = {
                "activity_type": f"{activity_type}_wtt",
                "quantity": activity["quantity"],
                "unit": activity["unit"],
                "scope": 3,
                "category": 3,
                "parent_activity": activity_type,
                "calculation_method": "automatic_wtt"
            }
            category_3_activities.append(wtt_activity)
            
        elif any(energy in activity_type for fuel in ["electricity", "heating", "cooling", "steam"]):
            # This is purchased energy - needs T&D losses
            td_activity = {
                "activity_type": f"{activity_type}_td",
                "quantity": activity["quantity"],
                "unit": activity["unit"],
                "scope": 3,
                "category": 3,
                "parent_activity": activity_type,
                "calculation_method": "automatic_td"
            }
            category_3_activities.append(td_activity)
    
    return category_3_activities

def get_data_quality_score(activity: dict, factor: dict, calculation_result: dict) -> dict:
    """Calculate data quality score per ESRS E1 requirements"""
    
    scores = {
        "temporal_correlation": 5,  # 1-5 scale
        "geographical_correlation": 5,
        "technological_correlation": 5,
        "completeness": 5,
        "reliability": 5
    }
    
    # Temporal correlation
    if "2024" in factor.get("source", ""):
        scores["temporal_correlation"] = 5
    elif "2023" in factor.get("source", ""):
        scores["temporal_correlation"] = 4
    else:
        scores["temporal_correlation"] = 3
    
    # Geographical correlation
    if activity.get("location", "").lower() == factor.get("region", "").lower():
        scores["geographical_correlation"] = 5
    elif factor.get("region", "").lower() in ["global", "average"]:
        scores["geographical_correlation"] = 3
    else:
        scores["geographical_correlation"] = 2
    
    # Completeness
    if activity.get("data_coverage", 100) >= 95:
        scores["completeness"] = 5
    elif activity.get("data_coverage", 100) >= 80:
        scores["completeness"] = 4
    else:
        scores["completeness"] = 3
    
    # Calculate overall DQR
    dqr = sum(scores.values()) / len(scores)
    
    return {
        "overall_score": round(dqr, 2),
        "tier": 1 if dqr >= 4.5 else (2 if dqr >= 3.5 else 3),
        "scores": scores,
        "methodology": "ESRS E1 DQR Matrix"
    }
