#!/bin/bash
# install_dependencies.sh - Install all missing dependencies

echo "📦 Installing missing dependencies..."

# Install aiohttp and other common async dependencies
pip install aiohttp aiofiles

# Check if there's a requirements.txt and install from it
if [ -f "requirements.txt" ]; then
    echo "📋 Found requirements.txt, installing all dependencies..."
    pip install -r requirements.txt
fi

# Install common dependencies that might be missing
echo "🔧 Installing common GHG app dependencies..."
pip install \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    aiosqlite \
    asyncpg \
    pydantic \
    pydantic-settings \
    python-dotenv \
    httpx \
    redis \
    celery \
    numpy \
    pandas \
    aiohttp \
    pytest \
    pytest-asyncio

echo "✅ Dependencies installed!"

# Show what's installed
echo -e "\n📊 Key packages installed:"
pip list | grep -E "fastapi|pydantic|sqlalchemy|aiohttp|numpy"