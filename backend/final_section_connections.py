import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix E1-4 to use add_targets_section
e1_4_stub_pattern = r'(def create_e1_4_targets\(body: ET\.Element, data: Dict\[str, Any\]\) -> None:[\s\S]*?)h2\.text = "E1-4: Targets related to climate change mitigation and adaptation"[\s\S]*?p\.text = "GHG emission reduction targets: 42% by 2030, Net-zero by 2050"'

e1_4_replacement = r'\1add_targets_section(body, data)'

content = re.sub(e1_4_stub_pattern, e1_4_replacement, content)

# Also ensure the stub functions are just calling the enhanced versions
# Clean up any remaining stub content
content = re.sub(
    r'(def create_e1_2_policies.*?\n.*?)section = ET\.SubElement.*?add_climate_policy_section_enhanced\(body, data\)',
    r'\1add_climate_policy_section_enhanced(body, data)',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'(def create_e1_3_actions_resources.*?\n.*?)section = ET\.SubElement.*?add_climate_actions_section_enhanced\(body, data\)',
    r'\1add_climate_actions_section_enhanced(body, data)',
    content,
    flags=re.DOTALL
)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ All sections now using proper enhanced functions:")
print("  - E1-2: add_climate_policy_section_enhanced")
print("  - E1-3: add_climate_actions_section_enhanced")
print("  - E1-4: add_targets_section")
