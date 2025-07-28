#!/bin/bash

echo "# PROJECT STRUCTURE ANALYSIS"
echo "Generated on: $(date)"
echo ""

echo "## Directory Structure"
tree -d -L 4 -I 'node_modules|__pycache__|.git|.next' 

echo -e "\n## Python Files and Imports"
echo "### Backend Structure"
find backend -name "*.py" | grep -v __pycache__ | sort

echo -e "\n### Python Imports by File"
find backend -name "*.py" -exec echo -e "\n--- {} ---" \; -exec grep "^import\|^from" {} \; 2>/dev/null

echo -e "\n## TypeScript/React Files"
echo "### Frontend Structure"
find factortrace-frontend/src -name "*.tsx" -o -name "*.ts" | sort

echo -e "\n### TypeScript Imports by File"
find factortrace-frontend/src \( -name "*.tsx" -o -name "*.ts" \) -exec echo -e "\n--- {} ---" \; -exec grep "^import" {} \; 2>/dev/null

echo -e "\n## API Endpoints"
grep -r "@router\|@app" backend --include="*.py" | grep -E "get\(|post\(|put\(|delete\("

echo -e "\n## Database Models"
grep -r "class.*Base" backend/app/models --include="*.py"

echo -e "\n## Environment Variables"
grep -r "os.getenv\|os.environ" backend --include="*.py" | cut -d: -f2 | sort | uniq

echo -e "\n## Package Dependencies"
echo "### Python (requirements.txt)"
cat backend/requirements.txt 2>/dev/null

echo -e "\n### JavaScript (package.json)"
cat factortrace-frontend/package.json | jq '.dependencies, .devDependencies' 2>/dev/null

