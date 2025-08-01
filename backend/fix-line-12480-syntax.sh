#!/bin/bash

echo "🔧 Fixing syntax error at line 12480..."

# First, let's see what's around line 12480
echo "Current content around line 12480:"
sed -n '12470,12485p' app/api/v1/endpoints/esrs_e1_full.py

# Now fix it by adding the except block before line 12480
# We need to add it at line 12479 (one before 12480)
sed -i '' '12479 i\
        except Exception as e:\
            logger.error(f"Error in iXBRL structure creation: {e}")\
            raise\
' app/api/v1/endpoints/esrs_e1_full.py

echo -e "\n✅ Added except block before line 12480"

# Verify the fix
echo -e "\nContent after fix:"
sed -n '12470,12490p' app/api/v1/endpoints/esrs_e1_full.py

# Test syntax
echo -e "\nTesting syntax..."
python3 -m py_compile app/api/v1/endpoints/esrs_e1_full.py 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Syntax is valid! The file compiles successfully."
    
    echo -e "\n🧪 Now test the endpoint:"
    echo 'curl -X POST http://localhost:8000/api/v1/esrs-e1/export/esrs-e1-world-class \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '\''{'
    echo '    "company_name": "Test Corp",'
    echo '    "lei": "12345678901234567890",'
    echo '    "reporting_period": "2024",'
    echo '    "sector": "Manufacturing",'
    echo '    "primary_nace_code": "C28",'
    echo '    "consolidation_scope": "financial_control",'
    echo '    "emissions": {'
    echo '      "scope1": 1000,'
    echo '      "scope2_location": 1800,'
    echo '      "scope3": 3000'
    echo '    },'
    echo '    "scope3_detailed": {'
    echo '      "category_1": {"emissions_tco2e": 3000, "excluded": false},'
    echo '      "category_2": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_3": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_4": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_5": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_6": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_7": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_8": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_9": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_10": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_11": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_12": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_13": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_14": {"excluded": true, "exclusion_reason": "Not applicable"},'
    echo '      "category_15": {"excluded": true, "exclusion_reason": "Not applicable"}'
    echo '    },'
    echo '    "targets": {'
    echo '      "base_year": 2020,'
    echo '      "targets": [{"year": 2030, "reduction": 50}]'
    echo '    },'
    echo '    "transition_plan": {'
    echo '      "net_zero_target_year": 2050,'
    echo '      "adopted": true,'
    echo '      "description": "Comprehensive net-zero transition plan"'
    echo '    },'
    echo '    "governance": {'
    echo '      "board_oversight": true,'
    echo '      "management_responsibility": true,'
    echo '      "climate_expertise": true'
    echo '    },'
    echo '    "climate_policy": {'
    echo '      "has_climate_policy": true,'
    echo '      "climate_policy_description": "Comprehensive climate policy aligned with Paris Agreement"'
    echo '    },'
    echo '    "financial_effects": {'
    echo '      "risks": [{"type": "physical", "amount": 5000000, "description": "Physical climate risks"}],'
    echo '      "opportunities": [{"type": "products", "amount": 10000000, "description": "Low-carbon products"}]'
    echo '    },'
    echo '    "energy": {'
    echo '      "total_consumption": 25000,'
    echo '      "renewable_percentage": 30'
    echo '    }'
    echo '  }'\'' | jq -r '\''.xhtml_content'\'' | grep -c '\''ix:nonFraction'\'''
else
    echo "❌ Syntax error still present. Showing detailed error:"
    python3 -c "
import ast
try:
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
        ast.parse(f.read())
except SyntaxError as e:
    print(f'Error at line {e.lineno}: {e.msg}')
    print(f'Text: {e.text}')
"
fi