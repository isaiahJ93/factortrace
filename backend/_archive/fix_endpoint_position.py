# Read the file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Remove the misplaced endpoint
content = content.replace('''@app.get("/api/v1/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary for dashboard"""
    return {
        "scope1_total": 0,
        "scope2_total": 0,
        "scope3_total": 0,
        "total_emissions": 0,
        "last_updated": None,
        "calculation_id": None
    }''', '')

# Add it in the right place (before main)
main_pos = content.find('if __name__ == "__main__":')
if main_pos > 0:
    endpoint = '''
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
    content = content[:main_pos] + endpoint + content[main_pos:]

# Write back
with open('ghg_monte_carlo_api.py', 'w') as f:
    f.write(content)

print("✅ Moved endpoint to correct position!")
