#!/bin/bash
# Save as fix-crash.sh and run: chmod +x fix-crash.sh && ./fix-crash.sh

echo "🚑 Elite Crash Fixer Engaged!"
echo "============================="

# Function to fix import paths
fix_imports() {
    echo "🔧 Fixing all import paths..."
    
    # Fix all ../components imports in app directory
    find src/app -name "*.tsx" -o -name "*.jsx" | while read file; do
        if grep -q "from '../components" "$file"; then
            echo "  Fixing: $file"
            sed -i '' 's|from "../components/|from "../../components/|g' "$file"
        fi
        if grep -q "from './components" "$file"; then
            echo "  Fixing: $file"
            sed -i '' 's|from "./components/|from "../components/|g' "$file"
        fi
    done
}

# Function to check for common issues
diagnose() {
    echo -e "\n🔍 Running diagnostics..."
    
    # Check for TypeScript errors
    echo -e "\n📝 TypeScript check:"
    if npx tsc --noEmit 2>/dev/null; then
        echo "  ✅ No TypeScript errors"
    else
        echo "  ❌ TypeScript errors found (running detailed check):"
        npx tsc --noEmit 2>&1 | head -20
    fi
    
    # Check for missing files
    echo -e "\n📁 Checking imports:"
    find src -name "*.tsx" -o -name "*.jsx" | while read file; do
        grep -E "^import.*from ['\"]\.\.?/" "$file" 2>/dev/null | while read import_line; do
            import_path=$(echo "$import_line" | sed -E "s/.*from ['\"]([^'\"]+)['\"].*/\1/")
            if [[ ! "$import_path" =~ \.(css|scss|json)$ ]]; then
                base_dir=$(dirname "$file")
                full_path="$base_dir/$import_path"
                
                # Check for .tsx, .ts, .jsx, .js extensions
                found=false
                for ext in tsx ts jsx js; do
                    if [ -f "$full_path.$ext" ]; then
                        found=true
                        break
                    fi
                done
                
                if [ "$found" = false ] && [ ! -d "$full_path" ]; then
                    echo "  ❌ Missing: $import_path (imported in $file)"
                fi
            fi
        done
    done
}

# Main execution
echo "🏃 Step 1: Fixing common import issues..."
fix_imports

echo -e "\n🏃 Step 2: Clearing cache..."
rm -rf .next

echo -e "\n🏃 Step 3: Running diagnostics..."
diagnose

echo -e "\n🏃 Step 4: Attempting build with extra memory..."
echo "Running: NODE_OPTIONS='--max-old-space-size=8192' npm run build"
echo "========================================="
NODE_OPTIONS='--max-old-space-size=8192' npm run build

# If build fails, show targeted help
if [ $? -ne 0 ]; then
    echo -e "\n❌ Build failed! Here's what to do:"
    echo "1. Copy the error message above"
    echo "2. Share it with me for specific fix"
    echo -e "\n🔧 Common fixes:"
    echo "- Missing component: Create placeholder or remove import"
    echo "- Type error: Fix TypeScript issues with 'npx tsc --noEmit'"
    echo "- Memory: Use 'NODE_OPTIONS=\"--max-old-space-size=12288\" npm run build'"
else
    echo -e "\n✅ Build successful!"
fi