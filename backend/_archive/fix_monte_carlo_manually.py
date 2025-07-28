import re

# Read the file
with open('ghg_monte_carlo_api.py', 'r') as f:
    lines = f.readlines()

# Find the last endpoint (should be calculate-with-monte-carlo)
last_endpoint_line = -1
for i, line in enumerate(lines):
    if '@app.post("/api/v1/calculate-with-monte-carlo")' in line:
        # Find the end of this function
        brace_count = 0
        for j in range(i, len(lines)):
            if '{' in lines[j]:
                brace_count += lines[j].count('{')
            if '}' in lines[j]:
                brace_count -= lines[j].count('}')
            if 'return' in lines[j] and brace_count == 0:
                # Found the return statement
                # Look for the closing of the function
                for k in range(j, len(lines)):
                    if lines[k].strip() and not lines[k].startswith(' ') and not lines[k].startswith('\t'):
                        last_endpoint_line = k
                        break
                break

# Add the summary endpoint after the last endpoint
if last_endpoint_line > 0:
    summary_endpoint = '''
@app.get("/api/v1/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary for dashboard"""
    return {
        "scope1_total": 0,
        "scope2_total": 0,
        "scope3_total": 0,
        "total_emissions": 0,
        "last_updated": None,
        "calculation_id": None
    }

'''
    lines.insert(last_endpoint_line, summary_endpoint)

# Write back
with open('ghg_monte_carlo_api.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed!")
