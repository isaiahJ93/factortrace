with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix line 5928 (index 5927)
if len(lines) > 5927:
    # Check and fix the indentation
    if 'measure_tco2e.text' in lines[5927]:
        # Get the indentation from the previous line
        prev_line = lines[5926]
        if 'measure_tco2e = ' in prev_line:
            indent = len(prev_line) - len(prev_line.lstrip())
            lines[5927] = ' ' * indent + "measure_tco2e.text = 'esrs:metricTonnesCO2e'\n"
        else:
            # Default to 4 spaces
            lines[5927] = "    measure_tco2e.text = 'esrs:metricTonnesCO2e'\n"

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed indentation on line 5928")
