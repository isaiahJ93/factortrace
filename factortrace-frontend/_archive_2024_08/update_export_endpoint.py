#!/usr/bin/env python3
import re

# Read the file
with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
    content = f.read()

# Find and replace the ESRS endpoint with the compliance endpoint
old_endpoint = r"\$\{API_URL\}/api/v1/esrs-e1/export/esrs-e1-world-class"
new_endpoint = "${API_URL}/api/v1/compliance/export"

# Update the endpoint
content = re.sub(old_endpoint, new_endpoint, content)

# Also update the export data structure to match what compliance endpoint expects
# Find the exportAsIXBRL function and update it
pattern = r'const response = await fetch\(`\$\{API_URL\}/api/v1/compliance/export`, \{[^}]+\}\);'

# Update how the data is structured for the compliance endpoint
old_export_data = r'const response = await fetch.*?\n.*?body: JSON\.stringify\(exportData\)'
new_export_data = '''const response = await fetch(`${API_URL}/api/v1/compliance/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: 'ixbrl',
          data: {
            entity_name: companyName || 'Organization',
            reporting_period: reportingPeriod,
            emissions: {
              scope1: (results?.summary?.scope1_emissions || 0) / 1000, // Convert kg to tons
              scope2: (results?.summary?.scope2_location_based || 0) / 1000,
              scope3: (results?.summary?.scope3_emissions || 0) / 1000
            }
          }
        })'''

# Replace the fetch call
content = re.sub(
    r'const response = await fetch\(`\$\{API_URL\}/api/v1/compliance/export`.*?\}\);',
    new_export_data + '\n      });',
    content,
    flags=re.DOTALL
)

# Update how the response is handled
old_download = r'const blob = new Blob\(\[result\.xhtml_content\], \{ type: \'application/xhtml\+xml\' \}\);'
new_download = r'const blob = new Blob([result.content], { type: \'application/xhtml+xml\' });'
content = re.sub(old_download, new_download, content)

# Update the filename
old_filename = r'a\.download = `ESRS_E1_Report_\$\{result\.document_id\}\.xhtml`;'
new_filename = r'a.download = result.filename || `emissions_report_${reportingPeriod}_ixbrl.html`;'
content = re.sub(old_filename, new_filename, content)

# Save the updated file
with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
    f.write(content)

print("✅ Updated EliteGHGCalculator.tsx to use compliance export endpoint")
