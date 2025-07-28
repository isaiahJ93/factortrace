# In app/services/esrs_aggregation_service.py
async def aggregate_energy_consumption(
    organization_id: str,
    reporting_year: int,
    db: AsyncSession
) -> Dict[str, float]:
    """Aggregate energy consumption from Scope 2 emissions"""
    
    # Query electricity emissions
    electricity_result = await db.execute(
        select(func.sum(Emission.activity_data))
        .where(
            Emission.organization_id == organization_id,
            Emission.scope == 2,
            Emission.category.in_(['electricity_grid', 'electricity_renewable']),
            extract('year', Emission.reporting_date) == reporting_year
        )
    )
    
    electricity_kwh = electricity_result.scalar() or 0
    electricity_mwh = electricity_kwh / 1000
    
    # Similar queries for other energy types
    return {
        "electricity_mwh": electricity_mwh,
        # ... other energy types
    }
    