#!/bin/bash

# Fix location 1 - After ghg_breakdown (around line 1720)
sed -i '/data\['\''ghg_breakdown'\''\] = calc_response.ghg_breakdown.dict()/a\
                # Update uncertainty analysis if available\
                if hasattr(calc_response, '\''uncertainty_analysis'\'') and calc_response.uncertainty_analysis:\
                    data['\''uncertainty_analysis'\''] = calc_response.uncertainty_analysis' \
    app/api/v1/endpoints/esrs_e1_full.py

# Fix location 2 - After emissions calculation (around line 1864)
sed -i '/logger.info(f"Calculated emissions: {data\['\''emissions'\''\]}")/a\
                # Add uncertainty analysis\
                if hasattr(calc_response, '\''uncertainty_analysis'\'') and calc_response.uncertainty_analysis:\
                    data['\''uncertainty_analysis'\''] = calc_response.uncertainty_analysis' \
    app/api/v1/endpoints/esrs_e1_full.py

echo "Uncertainty analysis integration added!"
