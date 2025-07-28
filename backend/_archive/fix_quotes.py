#!/usr/bin/env python3
"""Fix quote issues in the files"""

print("🔧 Fixing quote issues...")

# Fix ghg_schemas.py line 65
print("\n📋 Fixing ghg_schemas.py...")
try:
    with open('app/schemas/ghg_schemas.py', 'r') as f:
        lines = f.readlines()
    
    # Fix line 65 - replace with proper docstring
    if len(lines) > 64:
        lines[64] = '    """Query parameters for emission factor search"""\n'
        
        with open('app/schemas/ghg_schemas.py', 'w') as f:
            f.writelines(lines)
        print("✅ Fixed line 65 (removed excess quotes)")
except Exception as e:
    print(f"❌ Error fixing ghg_schemas.py: {e}")

# Fix ghg_tables.py - add closing quotes
print("\n📋 Fixing ghg_tables.py...")
try:
    with open('app/models/ghg_tables.py', 'r') as f:
        lines = f.readlines()
    
    # Insert closing quotes after line 15
    if len(lines) > 15:
        # Check if line 16 already has """
        if len(lines) > 15 and '"""' not in lines[15]:
            lines.insert(15, '"""\n')
            
            with open('app/models/ghg_tables.py', 'w') as f:
                f.writelines(lines)
            print("✅ Added closing quotes after line 15")
        else:
            print("ℹ️  Closing quotes might already be present")
except Exception as e:
    print(f"❌ Error fixing ghg_tables.py: {e}")

print("\n✅ Quote fixes complete!")
print("🚀 Now run: uvicorn app.main:app --reload --port 8000")