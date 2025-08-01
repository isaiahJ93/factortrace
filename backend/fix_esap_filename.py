with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix the filename generation call around line 12472
old_format = '''filename = ESAP_FILE_NAMING_PATTERN.format(
        lei=lei,
        period=period,
        standard='ESRS-E1',
        language=language,
        version=version
    )'''

new_format = '''filename = ESAP_FILE_NAMING_PATTERN.format(
        lei=lei,
        year=period,  # period contains the year
        period='FY',  # Default to full year
        report_type='E1',  # From ESAP_CONFIG report_types
        language=language,
        version=version
    )'''

content = content.replace(old_format, new_format)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed ESAP filename generation parameters")
