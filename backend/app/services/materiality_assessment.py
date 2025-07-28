# backend/app/services/materiality_assessment.py

MATERIALITY_THRESHOLDS = {
    'Manufacturing': 0.05,
    'Retail': 0.10,
    'Technology': 0.03,
    'Finance': 0.15,
    'Energy': 0.08,
    'Healthcare': 0.06,
    'Transportation': 0.07,
}

def assess_scope3_materiality(
    sector: str,
    category: str,
    total_emissions: Decimal,
    category_emissions: Decimal
) -> Dict[str, Any]:
    """Assess if a Scope 3 category is material for reporting"""
    
    threshold = MATERIALITY_THRESHOLDS.get(sector, 0.05)
    percentage = (category_emissions / total_emissions) if total_emissions > 0 else 0
    
    # SBTi criteria
    is_material = (
        percentage >= threshold or
        category in get_mandatory_categories(sector) or
        category_emissions > Decimal('1000')  # 1000 tCO2e absolute threshold
    )
    
    return {
        'is_material': is_material,
        'percentage': float(percentage * 100),
        'threshold': float(threshold * 100),
        'reason': determine_materiality_reason(is_material, percentage, threshold)
    }