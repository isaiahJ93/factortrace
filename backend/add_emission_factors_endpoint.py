import re

with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Check if emission_factors is registered
if 'emission_factors' not in content or 'emission-factors' not in content:
    print("emission_factors endpoint not found in API router")
    
    # Find where to add it (after emissions endpoint)
    emissions_pos = content.find('name="emissions"')
    if emissions_pos > 0:
        # Find the end of this registration block
        next_loader = content.find('loader.register_endpoint', emissions_pos + 1)
        
        # Add emission_factors registration
        new_registration = '''
# Emission factors endpoint
loader.register_endpoint(
    name="emission_factors",
    module_path="emission_factors",
    prefix="/emission-factors",
    tags=["emissions", "factors"],
    description="Emission factors for calculations"
)
'''
        
        if next_loader > 0:
            content = content[:next_loader] + new_registration + '\n' + content[next_loader:]
        else:
            # Add at the end
            content = content + '\n' + new_registration
            
        with open('app/api/v1/api.py', 'w') as f:
            f.write(content)
            
        print("Added emission_factors endpoint to API")
else:
    print("emission_factors already in API")

