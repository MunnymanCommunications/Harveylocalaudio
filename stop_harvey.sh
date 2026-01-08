#!/bin/bash

# Harvey AI - Stop Script
# This script stops the running Harvey backend server and ngrok

echo "🛑 Stopping Harvey AI..."

# Stop backend server
if [ -f "/tmp/harvey_backend.pid" ]; then
    SERVER_PID=$(cat /tmp/harvey_backend.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID
        echo "✅ Harvey backend stopped (PID: $SERVER_PID)"
        rm /tmp/harvey_backend.pid
    else
        echo "⚠️  Backend process not found (PID: $SERVER_PID)"
        rm /tmp/harvey_backend.pid
    fi
elif [ -f "/tmp/harvey_server.pid" ]; then
    # Old PID file location
    SERVER_PID=$(cat /tmp/harvey_server.pid)
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID
        echo "✅ Harvey backend stopped (PID: $SERVER_PID)"
        rm /tmp/harvey_server.pid
    else
        rm /tmp/harvey_server.pid
    fi
else
    # Try to find and kill any running main.py process
    PIDS=$(pgrep -f "python.*main.py" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "Found Harvey server processes: $PIDS"
        kill $PIDS
        echo "✅ Harvey server(s) stopped"
    else
        echo "ℹ️  No running Harvey server found"
    fi
fi

# Stop ngrok
if [ -f "/tmp/harvey_ngrok.pid" ]; then
    NGROK_PID=$(cat /tmp/harvey_ngrok.pid)
    if ps -p $NGROK_PID > /dev/null 2>&1; then
        kill $NGROK_PID
        echo "✅ Ngrok stopped (PID: $NGROK_PID)"
        rm /tmp/harvey_ngrok.pid
    else
        echo "⚠️  Ngrok process not found (PID: $NGROK_PID)"
        rm /tmp/harvey_ngrok.pid
    fi
else
    # Try to find and kill ngrok process
    PIDS=$(pgrep -f "ngrok.*http" 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "Found ngrok processes: $PIDS"
        kill $PIDS
        echo "✅ Ngrok stopped"
    else
        echo "ℹ️  No running ngrok found"
    fi
fi

# Clean up temp files
rm -f /tmp/harvey_url.txt

echo "Done!"
