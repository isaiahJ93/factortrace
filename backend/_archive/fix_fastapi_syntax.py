# Read the broken file
with open('ghg_monte_carlo_api.py', 'r') as f:
    content = f.read()

# Remove the misplaced code
content = content.replace('''# Initialize state for storing results
from types import SimpleNamespace
app.state = SimpleNamespace()
app.state.last_calculation = None''', '')

# Fix the FastAPI initialization
content = content.replace('''app = FastAPI(
    title="GHG Calculator with Monte Carlo - Fixed",''', 
'''app = FastAPI(
    title="GHG Calculator with Monte Carlo - Fixed",''')

# Find where FastAPI() call ends (look for the closing parenthesis)
# and add the initialization after it
import re
pattern = r'(app = FastAPI\([^)]+\))'
match = re.search(pattern, content, re.DOTALL)

if match:
    fastapi_end = match.end()
    # Add the initialization after FastAPI()
    init_code = '''

# Initialize state for storing results
from types import SimpleNamespace
app.state = SimpleNamespace()
app.state.last_calculation = None
'''
    content = content[:fastapi_end] + init_code + content[fastapi_end:]

# Also need to move the import to the top
if 'from types import SimpleNamespace' not in content[:1000]:  # Check if not already in imports
    # Add after other imports
    import_pos = content.find('import uvicorn')
    if import_pos > 0:
        content = content[:import_pos] + 'from types import SimpleNamespace\n' + content[import_pos:]

# Write the fixed file
with open('ghg_monte_carlo_api_fixed.py', 'w') as f:
    f.write(content)

print("✅ Fixed! Check ghg_monte_carlo_api_fixed.py")
