import re

with open('src/app/emissions/new/page.tsx', 'r') as f:
    content = f.read()

# Look for the scope button section
# It should have buttons for Scope 1, 2, 3 but seems to show "detail"

# First, let's check what's there
if 'Scope detail' in content or '>detail<' in content:
    print("Found 'detail' in the file - this is the problem")
    
    # Replace any instance of >detail< with proper scope numbers
    # This is a targeted fix for the button labels
    
    # Look for button patterns
    button_pattern = r'(Scope\s*)detail'
    content = re.sub(button_pattern, r'\g<1>{scope}', content)
    
    # If the buttons are in a map/loop, fix the array
    if '[1, 2, 3].map' not in content and 'scope in [1, 2, 3]' not in content:
        print("Need to add scope array")

# Show what we found
detail_matches = re.findall(r'.{30}detail.{30}', content)
for match in detail_matches[:3]:
    print(f"Found: {match}")

