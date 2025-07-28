#!/bin/bash
# fix_pydantic_correct.sh - Fix Pydantic imports the right way

echo "🔧 Fixing Pydantic v2 imports correctly..."

# First, install pydantic-settings if not already installed
pip install pydantic-settings

# Fix the config.py file with correct imports
echo "📝 Fixing app/core/config.py..."

# Create a backup first
cp app/core/config.py app/core/config.py.backup_original 2>/dev/null || true

# Fix the imports - BaseSettings from pydantic-settings, everything else from pydantic
cat > fix_config_imports.py << 'EOF'
import re

# Read the config file
with open('app/core/config.py', 'r') as f:
    content = f.read()

# Fix the imports
# Replace the old import line
old_import = r'from pydantic import BaseSettings, Field, validator, PostgresDsn, RedisDsn, HttpUrl'
new_imports = '''from pydantic_settings import BaseSettings
from pydantic import Field, validator, PostgresDsn, RedisDsn, HttpUrl'''

content = re.sub(old_import, new_imports, content)

# Also fix field_validator if it's there
content = re.sub(r'from pydantic import (.*?)field_validator', 
                 r'from pydantic import \1field_validator', content)

# Also handle if someone already tried to fix it wrong
wrong_fix = r'from pydantic_settings import BaseSettings, Field, field_validator, PostgresDsn, RedisDsn, HttpUrl'
content = re.sub(wrong_fix, new_imports.replace('validator', 'field_validator'), content)

# Write back
with open('app/core/config.py', 'w') as f:
    f.write(content)

print("✅ Fixed imports in config.py")
EOF

python fix_config_imports.py
rm fix_config_imports.py

# Also check if there are other files with the same issue
echo "🔍 Checking for other files with BaseSettings imports..."
grep -r "from pydantic import.*BaseSettings" app/ --include="*.py" | grep -v __pycache__ || true

# Show what the correct import should look like
echo "
✅ Correct Pydantic v2 imports:
================================
from pydantic_settings import BaseSettings  # Only BaseSettings from pydantic-settings
from pydantic import Field, validator       # Everything else from pydantic

❌ Wrong:
from pydantic import BaseSettings           # Old way
from pydantic_settings import Field         # Field is still in pydantic
"

echo "🚀 Now try running your full API again:"
echo "   uvicorn app.main:app --reload --port 8000"