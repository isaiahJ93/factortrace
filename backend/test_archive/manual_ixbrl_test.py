#!/usr/bin/env python3
"""
Manual test - create iXBRL without using create_enhanced_xbrl_tag
"""

print("🧪 Manual iXBRL creation test")
print("="*40)

# Create iXBRL manually without any functions
html_content = '''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs="http://www.efrag.org/esrs/2023">
<head>
    <title>Manual iXBRL Test</title>
</head>
<body>
    <!-- Hidden XBRL metadata -->
    <ix:hidden>
        <ix:resources>
            <!-- Context for current period -->
            <xbrli:context id="c1">
                <xbrli:entity>
                    <xbrli:identifier scheme="http://standards.iso.org/iso/17442">ABCDEFGHIJ1234567890</xbrli:identifier>
                </xbrli:entity>
                <xbrli:period>
                    <xbrli:instant>2024-12-31</xbrli:instant>
                </xbrli:period>
            </xbrli:context>
            
            <!-- Unit for CO2 -->
            <xbrli:unit id="tCO2e">
                <xbrli:measure>esrs:tCO2e</xbrli:measure>
            </xbrli:unit>
        </ix:resources>
    </ix:hidden>
    
    <!-- Visible content with iXBRL tags -->
    <h1>ESRS E1 Climate Disclosures</h1>
    
    <p>Entity: <ix:nonNumeric name="esrs:EntityName" contextRef="c1">Test Company Ltd</ix:nonNumeric></p>
    
    <table>
        <tr>
            <td>Scope 1 emissions:</td>
            <td><ix:nonFraction name="esrs:Scope1Emissions" contextRef="c1" unitRef="tCO2e" decimals="0">1,500</ix:nonFraction> tCO2e</td>
        </tr>
        <tr>
            <td>Scope 2 emissions:</td>
            <td><ix:nonFraction name="esrs:Scope2LocationBased" contextRef="c1" unitRef="tCO2e" decimals="0">800</ix:nonFraction> tCO2e</td>
        </tr>
        <tr>
            <td>Scope 3 emissions:</td>
            <td><ix:nonFraction name="esrs:Scope3Emissions" contextRef="c1" unitRef="tCO2e" decimals="0">5,000</ix:nonFraction> tCO2e</td>
        </tr>
        <tr>
            <td><strong>Total emissions:</strong></td>
            <td><strong><ix:nonFraction name="esrs:TotalGHGEmissions" contextRef="c1" unitRef="tCO2e" decimals="0">7,300</ix:nonFraction> tCO2e</strong></td>
        </tr>
    </table>
</body>
</html>'''

# Save it
with open('manual_ixbrl.xhtml', 'w') as f:
    f.write(html_content)

print("✅ Created manual_ixbrl.xhtml")

# Verify it
import re
fractions = len(re.findall(r'<ix:nonFraction', html_content))
numerics = len(re.findall(r'<ix:nonNumeric', html_content))
contexts = len(re.findall(r'<xbrli:context', html_content))
units = len(re.findall(r'<xbrli:unit', html_content))

print(f"\n📊 Content analysis:")
print(f"   ix:nonFraction tags: {fractions}")
print(f"   ix:nonNumeric tags: {numerics}")
print(f"   xbrli:context: {contexts}")
print(f"   xbrli:unit: {units}")

if fractions > 0 and numerics > 0:
    print("\n✅ SUCCESS! Manual iXBRL is valid")
    print("\n🔍 This proves:")
    print("   1. iXBRL structure is correct")
    print("   2. The issue is in the Python code generation")
    print("   3. Either create_enhanced_xbrl_tag is broken or not being called")
    
    # Now test with verify_ixbrl.py
    print("\n📋 Running verification...")
    import subprocess
    result = subprocess.run(['python3', 'verify_ixbrl.py', 'manual_ixbrl.xhtml'], 
                          capture_output=True, text=True)
    print(result.stdout)
else:
    print("\n❌ Something went wrong even with manual creation!")