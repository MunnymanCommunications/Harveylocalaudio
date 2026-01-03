#!/bin/bash
# Launch web client in browser

cd "$(dirname "$0")/web-client"

echo "======================================="
echo "Harvey Voice AI - Web Client"
echo "======================================="
echo ""
echo "Starting local web server on port 8080..."
echo "Opening browser..."
echo ""
echo "WebSocket URL: ws://localhost:8765/ws/audio"
echo "API Key: Check desktop app or backend/.api_key"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080" &
elif command -v open &> /dev/null; then
    open "http://localhost:8080" &
fi

# Start web server
python3 -m http.server 8080
