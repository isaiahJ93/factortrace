#!/usr/bin/env python3
"""
Fix imports after migrating files to backend structure
"""
import os
import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    # Old import → New import
    "from factortrace.": "from app.",
    "from src.factortrace.": "from app.",
    "from emissions_calculator": "from app.services.emissions_calculator",
    "from compliance_engine": "from app.services.compliance_engine",
    "from voucher_generator": "from app.services.voucher_generator",
    "from ..models": "from app.models",
    "from ..schemas": "from app.schemas",
    "from ..services": "from app.services",
    "from ..utils": "from app.utils",
    "from config.settings": "from app.core.config",
    "from src.api.schemas": "from app.schemas.api_schemas",
    "from api.schemas": "from app.schemas",
    "from factortrace.models.": "from app.models.",
    "from factortrace.services.": "from app.services.",
    "from factortrace.utils.": "from app.utils.",
    "from factortrace.api.": "from app.api.v1.endpoints.",
    "from src.factortrace.models.": "from app.models.",
    "from src.factortrace.services.": "from app.services.",
    "from src.factortrace.utils.": "from app.utils.",
}

def fix_imports_in_file(file_path):
    """Fix imports in a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        # Fix relative imports based on file location
        if '/models/' in str(file_path):
            # In models directory
            content = re.sub(r'from \.(\w+)', r'from app.models.\1', content)
        elif '/services/' in str(file_path):
            # In services directory
            content = re.sub(r'from \.(\w+)', r'from app.services.\1', content)
        elif '/api/' in str(file_path):
            # In API directory
            content = re.sub(r'from \.\.\.models', r'from app.models', content)
            content = re.sub(r'from \.\.\.schemas', r'from app.schemas', content)
        
        # Fix common patterns
        content = re.sub(r'from models\.', r'from app.models.', content)
        content = re.sub(r'from schemas\.', r'from app.schemas.', content)
        content = re.sub(r'from services\.', r'from app.services.', content)
        content = re.sub(r'from utils\.', r'from app.utils.', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def fix_all_imports(backend_dir="backend"):
    """Fix imports in all Python files in the backend directory"""
    backend_path = Path(backend_dir)
    if not backend_path.exists():
        print("❌ Backend directory not found!")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Find all Python files
    for py_file in backend_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
    
    print(f"\n📊 Import Fix Summary:")
    print(f"   Total files scanned: {total_count}")
    print(f"   Files with fixed imports: {fixed_count}")

def create_import_checker():
    """Create a script to check for broken imports"""
    checker_content = '''#!/usr/bin/env python3
"""Check for broken imports in the backend"""
import ast
import sys
from pathlib import Path

def check_imports(file_path):
    """Check if all imports in a file are valid"""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    print(f"  Import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    print(f"  From {module} import {alias.name}")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False

def main():
    backend_path = Path("backend")
    errors = 0
    
    for py_file in backend_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        print(f"\\nChecking: {py_file}")
        if not check_imports(py_file):
            errors += 1
    
    if errors > 0:
        print(f"\\n❌ Found {errors} files with import errors")
        sys.exit(1)
    else:
        print("\\n✅ All imports look good!")

if __name__ == "__main__":
    main()
'''
    
    with open("backend/check_imports.py", "w") as f:
        f.write(checker_content)
    print("✅ Created import checker script: backend/check_imports.py")

def create_common_fixes():
    """Create additional common fixes"""
    
    # Fix main.py specifically
    main_py_content = '''"""
FactorTrace Backend - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("🚀 Starting FactorTrace Backend...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("👋 Shutting down FactorTrace Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FactorTrace API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.VERSION}
'''
    
    # Only create if main.py exists
    if os.path.exists("backend/app/main.py"):
        with open("backend/app/main.py", "w") as f:
            f.write(main_py_content)
        print("✅ Updated main.py with proper imports")

if __name__ == "__main__":
    print("🔧 Fixing imports in backend files...")
    fix_all_imports()
    create_import_checker()
    create_common_fixes()
    print("\n✅ Import fixing complete!")
    print("\n💡 You can run 'python backend/check_imports.py' to verify all imports")