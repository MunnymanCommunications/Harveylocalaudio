#!/bin/bash

# Harvey AI - Startup Script
# This script starts the backend server and opens the web client

# Change to the project directory
cd "$(dirname "$0")"

echo "🤖 Starting Harvey AI..."

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Please run the install script first."
    exit 1
fi

# Start the backend server in the background
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate
python main.py > /tmp/harvey_server.log 2>&1 &
SERVER_PID=$!
echo "✅ Backend server started (PID: $SERVER_PID)"

# Wait a moment for the server to start
sleep 3

# Open the modern Harvey IO interface
echo "🌐 Opening Harvey IO interface..."
cd ..
xdg-open "file://$(pwd)/harvey_io.html" 2>/dev/null || \
    firefox "file://$(pwd)/harvey_io.html" 2>/dev/null || \
    google-chrome "file://$(pwd)/harvey_io.html" 2>/dev/null || \
    chromium "file://$(pwd)/harvey_io.html" 2>/dev/null

echo ""
echo "✅ Harvey is ready!"
echo "📝 Server logs: /tmp/harvey_server.log"
echo "⏹  To stop the server, run: kill $SERVER_PID"
echo ""
echo "💡 Press Harvey button in the browser to activate!"

# Keep script running and show server PID
echo $SERVER_PID > /tmp/harvey_server.pid
