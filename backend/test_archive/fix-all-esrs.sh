#!/bin/bash

echo "🚀 ESRS iXBRL Quick Fix Script"
echo "=============================="

# 1. Fix TypeScript import extensions
echo "📝 Step 1: Fixing TypeScript imports..."
sed -i '' "s|import { apiClient } from '../../../lib/api-client.ts';|import { apiClient } from '../../../lib/api-client';|" src/app/emissions/new/page.tsx
find src -name "*.tsx" -o -name "*.ts" | while read file; do
    sed -i '' -E "s|from '([^']+)\.(ts|tsx)'|from '\1'|g" "$file"
done

# 2. Create ESRS types if not exists
echo "📝 Step 2: Creating ESRS type definitions..."
mkdir -p src/types
if [ ! -f src/types/esrs.ts ]; then
    echo "Creating src/types/esrs.ts..."
    # You'll need to copy the types from the artifact above
fi

# 3. Add type safety to ExportOptions if needed
echo "📝 Step 3: Fixing ExportOptions types..."
if grep -q "useState<RecentExport\[\]>" src/app/components/ExportOptions.tsx; then
    # Add interface definition after imports
    sed -i '' '/^import.*from/!b; :a; n; /^import.*from/ba; a\
\
interface RecentExport {\
  format: string;\
  timestamp: Date;\
  filename: string;\
  status: string;\
}' src/app/components/ExportOptions.tsx
fi

# 4. Verify API_URL is defined
echo "📝 Step 4: Checking environment variables..."
if [ ! -f .env.local ]; then
    echo "Creating .env.local with default API_URL..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

# 5. Clean and rebuild
echo "🧹 Step 5: Cleaning build cache..."
rm -rf .next
rm -rf node_modules/.cache

echo "🔨 Step 6: Running build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful! Your ESRS iXBRL exporter is ready."
    echo ""
    echo "⚠️  IMPORTANT: Make sure to update ExportResults.tsx with the proper exportIXBRL function from the artifact above."
    echo ""
    echo "Next steps:"
    echo "1. Copy the exportIXBRL function from the artifact"
    echo "2. Add proper ESRS validation on the backend"
    echo "3. Test with EFRAG validation tools"
else
    echo "❌ Build failed. Check the errors above."
    echo ""
    echo "Common issues:"
    echo "- Missing type definitions"
    echo "- Incorrect import paths"
    echo "- Missing environment variables"
fi