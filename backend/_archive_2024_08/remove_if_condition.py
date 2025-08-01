import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Count how many times this pattern appears
pattern = r'if cat_key in scope3_breakdown and scope3_breakdown\[cat_key\] > 0:'
matches = re.findall(pattern, content)
print(f"Found {len(matches)} occurrences of the if condition")

# Replace ONLY in the create_scope3_disclosure function
# Remove the if condition and de-indent the code block
old_block = """        for cat_num in range(1, 16):
            cat_key = f'category_{cat_num}'
            if cat_key in scope3_breakdown and scope3_breakdown[cat_key] > 0:
                tr = ET.SubElement(tbody, 'tr')"""

new_block = """        for cat_num in range(1, 16):
            cat_key = f'category_{cat_num}'
            emissions_value = scope3_breakdown.get(cat_key, 0)
            tr = ET.SubElement(tbody, 'tr')"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)  # Only replace ONCE
    print("✅ Removed the if condition - will now show ALL categories")
else:
    print("❌ Could not find the exact pattern to replace")

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)
