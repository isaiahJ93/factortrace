import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the create_scope3_disclosure function
pattern = r'(for cat_num in range\(1, 16\):[\s\S]*?)(tbody\))'

# Replace with code that shows ALL categories
replacement = r'''for cat_num in range(1, 16):
            cat_key = f'category_{cat_num}'
            emissions_value = scope3_breakdown.get(cat_key, 0)
            
            # Category descriptions per GHG Protocol
            category_descriptions = {
                1: "Purchased goods and services",
                2: "Capital goods",
                3: "Fuel-and-energy-related activities",
                4: "Upstream transportation and distribution",
                5: "Waste generated in operations",
                6: "Business travel",
                7: "Employee commuting",
                8: "Upstream leased assets",
                9: "Downstream transportation and distribution",
                10: "Processing of sold products",
                11: "Use of sold products",
                12: "End-of-life treatment of sold products",
                13: "Downstream leased assets",
                14: "Franchises",
                15: "Investments"
            }
            
            tr = ET.SubElement(tbody, 'tr')
            
            # Category number
            td = ET.SubElement(tr, 'td')
            td.text = f"Category {cat_num}"
            
            # Description
            td = ET.SubElement(tr, 'td')
            td.text = category_descriptions[cat_num]
            
            # Emissions
            td = ET.SubElement(tr, 'td')
            emissions_element = ET.SubElement(td, f'{{{namespaces["ix"]}}}nonFraction', attrib={
                'name': f'esrs-e1:Scope3Category{cat_num}',
                'contextRef': 'current-period',
                'unitRef': 'tCO2e',
                'decimals': '1',
                'format': 'ixt:numdotdecimal'
            })
            emissions_element.text = f"{emissions_value:.0f}"
            
            # Percentage
            td = ET.SubElement(tr, 'td')
            percentage = (emissions_value / total_scope3 * 100) if total_scope3 > 0 else 0
            td.text = f"{percentage:.1f}%"
        
        \2'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed to show ALL 15 Scope 3 categories")
