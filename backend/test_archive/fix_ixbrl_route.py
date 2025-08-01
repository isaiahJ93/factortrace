#!/usr/bin/env python3
"""
Fix iXBRL export route to match frontend expectations
"""

import os
import re

def add_ixbrl_route():
    """Add the missing /export/ixbrl route to api.py"""
    
    api_file = "app/api/v1/api.py"
    
    if not os.path.exists(api_file):
        print(f"❌ {api_file} not found!")
        return False
    
    # Read the file
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Check if route already exists
    if "/export/ixbrl" in content:
        print("✅ Route /export/ixbrl already exists")
        return True
    
    # Add the import if needed
    if "from typing import Dict, Any" not in content:
        import_line = "from typing import Dict, Any\n"
        # Add after other imports
        import_pos = content.find("from app.api.v1.endpoints")
        if import_pos > 0:
            content = content[:import_pos] + import_line + content[import_pos:]
    
    # Add the route function
    route_code = '''

# Direct iXBRL export route for frontend compatibility
@api_router.post("/export/ixbrl")
async def export_ixbrl_direct(data: Dict[str, Any] = Body(...)):
    """
    Direct iXBRL export endpoint that forwards to compliance export.
    This matches the URL that the frontend is expecting.
    """
    from app.api.v1.endpoints.compliance import export_ixbrl
    
    # Forward to the compliance endpoint with the correct format
    return await export_ixbrl({
        "format": "ixbrl",
        "data": data
    })
'''
    
    # Find a good place to insert - after the last include_router
    insert_pos = -1
    
    # Try to find the last include_router
    includes = list(re.finditer(r'api_router\.include_router\([^)]+\)', content))
    if includes:
        last_include = includes[-1]
        insert_pos = last_include.end()
        print(f"📍 Inserting after last include_router at position {insert_pos}")
    else:
        # Try to find where api_router is defined
        router_def = content.find("api_router = APIRouter()")
        if router_def > 0:
            # Find the next newline after that
            insert_pos = content.find("\n", router_def) + 1
            print(f"📍 Inserting after api_router definition")
    
    if insert_pos > 0:
        # Make sure we have the Body import
        if "from fastapi import" in content and "Body" not in content:
            # Add Body to existing fastapi import
            content = re.sub(
                r'from fastapi import ([^)]+)',
                lambda m: f"from fastapi import {m.group(1)}, Body",
                content,
                count=1
            )
        elif "from fastapi" not in content:
            # Add the import
            content = "from fastapi import Body\n" + content
        
        # Insert the route
        content = content[:insert_pos] + route_code + content[insert_pos:]
        
        # Save the file
        with open(api_file, 'w') as f:
            f.write(content)
        
        print("✅ Added /export/ixbrl route to api.py")
        return True
    else:
        print("❌ Could not find insertion point")
        return False

def test_new_route():
    """Test the new route"""
    print("\n🧪 Testing the new route...")
    
    import subprocess
    import json
    
    test_data = {
        "entity_name": "Test Company",
        "reporting_period": "2024",
        "emissions": {
            "scope1": 100,
            "scope2": 200,
            "scope3": 300
        }
    }
    
    cmd = [
        "curl", "-X", "POST",
        "http://localhost:8000/api/v1/export/ixbrl",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(test_data),
        "-s"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            response = json.loads(result.stdout)
            if "content" in response:
                print("✅ Route is working! Got iXBRL content")
                print(f"   Format: {response.get('format', 'N/A')}")
                print(f"   Content length: {len(response.get('content', ''))} chars")
            else:
                print("❓ Got response but no content:", response)
        else:
            print("❌ Request failed:", result.stderr)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("   Make sure the server is running!")

if __name__ == "__main__":
    print("🔧 Adding iXBRL export route...")
    
    if add_ixbrl_route():
        print("\n📋 Next steps:")
        print("1. Restart your FastAPI server")
        print("2. The frontend should now work with /api/v1/export/ixbrl")
        
        # Try to test it
        input("\nPress Enter to test the route (make sure server is restarted)...")
        test_new_route()
    else:
        print("\n❌ Failed to add route. Check the file manually.")