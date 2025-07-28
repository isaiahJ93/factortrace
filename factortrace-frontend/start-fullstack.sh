#!/bin/bash

echo "🚀 Starting FactorTrace Full Stack..."
echo "=================================="

# Function to kill processes on exit
cleanup() {
    echo -e "\n🛑 Shutting down servers..."
    kill $FASTAPI_PID $NEXT_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start FastAPI backend
echo "📡 Starting FastAPI backend..."
cd ../src
python -m uvicorn main:app --reload --port 8000 &
FASTAPI_PID=$!

# Give FastAPI a moment to start
sleep 3

# Start Next.js frontend
echo "🎨 Starting Next.js frontend..."
cd ../factortrace-frontend
npm run dev &
NEXT_PID=$!

echo ""
echo "✅ FactorTrace is running!"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait
