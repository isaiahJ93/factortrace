#!/bin/bash

# For macOS, we need to use different sed syntax

# Fix location 1 - After ghg_breakdown
sed -i '' -e '/data\['"'"'ghg_breakdown'"'"'\] = calc_response.ghg_breakdown.dict()/{
a\
\                # Update uncertainty analysis if available
a\
\                if hasattr(calc_response, '"'"'uncertainty_analysis'"'"') and calc_response.uncertainty_analysis:
a\
\                    data['"'"'uncertainty_analysis'"'"'] = calc_response.uncertainty_analysis
}' app/api/v1/endpoints/esrs_e1_full.py

# Fix location 2 - After emissions calculation
sed -i '' -e '/logger.info(f"Calculated emissions: {data\['"'"'emissions'"'"'\]}")/{
a\
\                # Add uncertainty analysis
a\
\                if hasattr(calc_response, '"'"'uncertainty_analysis'"'"') and calc_response.uncertainty_analysis:
a\
\                    data['"'"'uncertainty_analysis'"'"'] = calc_response.uncertainty_analysis
}' app/api/v1/endpoints/esrs_e1_full.py

echo "Uncertainty analysis integration added!"
