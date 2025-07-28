#!/bin/bash
# Save as: start-factortrace.sh in your "Scope 3 Tool" directory
# Make executable with: chmod +x start-factortrace.sh

echo "🚀 Starting FactorTrace..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Start backend
echo -e "${BLUE}Starting backend API...${NC}"
cd "$(dirname "$0")"  # Ensure we're in the right directory

# Check if Python virtual environment exists
if [ -d "factortrace-backend/venv" ]; then
    source factortrace-backend/venv/bin/activate
fi

# Start the API in background
python src/scope3_api.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"
    echo -e "${GREEN}✓ API docs at http://localhost:8000/docs${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    exit 1
fi

# Start frontend
echo -e "${BLUE}Starting frontend...${NC}"
cd factortrace-frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}🎉 FactorTrace is ready!${NC}"
echo ""
echo "Dashboard: http://localhost:3000/dashboard"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Keep script running
wait
