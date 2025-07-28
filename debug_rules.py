from lxml import etree
from xpath31.compliance.filing_rules import UnitHarmonizationRule, WhitespaceNormalizationRule

# Load and parse the bad filing
with open('bad_filing.xhtml', 'rb') as f:
    doc = etree.parse(f)

print("=== Direct Rule Testing ===\n")

# Test Unit Harmonization
print("1. Testing UnitHarmonizationRule:")
unit_rule = UnitHarmonizationRule()
unit_results = unit_rule.validate(doc)
print(f"   Found {len(unit_results)} issues")
for r in unit_results:
    print(f"   - {r.severity}: {r.message}")

# Test Whitespace
print("\n2. Testing WhitespaceNormalizationRule:")
ws_rule = WhitespaceNormalizationRule()
ws_results = ws_rule.validate(doc)
print(f"   Found {len(ws_results)} issues")
for r in ws_results:
    print(f"   - {r.severity}: {r.message}")

# Debug: Check what elements the rules are finding
print("\n=== Debug Info ===")
namespaces = {'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
elements = doc.xpath('//ix:nonFraction', namespaces=namespaces)
print(f"Found {len(elements)} ix:nonFraction elements")
for elem in elements:
    print(f"  - {elem.get('name')} = '{elem.text}' (unit: {elem.get('unitRef')})")
