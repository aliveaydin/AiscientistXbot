#!/bin/bash

echo "🤖 Starting Twitter Bot AI Agent (Development Mode)..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "📝 Created .env file. Please fill in your API keys!"
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
source ../venv/bin/activate 2>/dev/null || (python3 -m venv ../venv && source ../venv/bin/activate && pip install -r requirements.txt -q)
python run.py &
BACKEND_PID=$!
cd ..

# Start frontend dev server
echo "🎨 Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "📊 Frontend: http://localhost:3000"
echo "📚 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Trap Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
