#!/bin/bash

echo "🤖 Starting Twitter Bot AI Agent..."
echo ""

# Check if we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📋 Copying env.example to .env..."
    cp env.example .env
    echo "📝 Please edit .env with your API keys before running again."
    echo ""
    echo "Required keys:"
    echo "  - TWITTER_API_KEY, TWITTER_API_SECRET"
    echo "  - TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET"
    echo "  - TWITTER_BEARER_TOKEN"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo ""
    exit 1
fi

# Setup Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt -q

# Check if Node.js is installed for frontend
if command -v node &> /dev/null; then
    echo "🎨 Building frontend..."
    cd frontend
    npm install --silent 2>/dev/null
    npm run build 2>/dev/null
    cd ..
    echo "✅ Frontend built successfully!"
else
    echo "⚠️  Node.js not found. Frontend won't be built."
    echo "   Install Node.js and run: cd frontend && npm install && npm run build"
fi

echo ""
echo "🚀 Starting the bot server..."
echo "📊 Dashboard: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

cd backend
python run.py
