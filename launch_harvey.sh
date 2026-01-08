#!/bin/bash

# Harvey AI - Complete Launch Script
# Starts backend, ngrok, and opens the browser automatically

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}"
echo "╔═══════════════════════════════════════╗"
echo "║         HARVEY AI LAUNCHER            ║"
echo "║      Voice Assistant System           ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    echo -e "${YELLOW}⏳ Waiting for $name to start...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo -e "${RED}❌ $name failed to start${NC}"
    return 1
}

# Check if backend is already running
if is_running "python.*main.py"; then
    echo -e "${YELLOW}⚠️  Backend server already running${NC}"
else
    echo -e "${YELLOW}🚀 Starting Harvey backend server...${NC}"
    cd backend
    source venv/bin/activate
    nohup python main.py > /tmp/harvey_server.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/harvey_backend.pid
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    cd ..

    # Wait for backend to be ready
    sleep 3
fi

# Check if ngrok is already running
if is_running "ngrok.*http"; then
    echo -e "${YELLOW}⚠️  Ngrok already running${NC}"
else
    echo -e "${YELLOW}🌐 Starting ngrok tunnel...${NC}"
    nohup ~/ngrok http https://localhost:8765 > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > /tmp/harvey_ngrok.pid
    echo -e "${GREEN}✅ Ngrok started (PID: $NGROK_PID)${NC}"

    # Wait for ngrok to be ready
    sleep 3
fi

# Get ngrok URL
echo -e "${YELLOW}🔍 Retrieving ngrok URL...${NC}"
NGROK_URL=""
attempt=0
while [ -z "$NGROK_URL" ] && [ $attempt -lt 10 ]; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)
    if [ -z "$NGROK_URL" ]; then
        attempt=$((attempt + 1))
        sleep 1
    fi
done

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Failed to retrieve ngrok URL${NC}"
    echo -e "${YELLOW}💡 Try accessing http://localhost:4040 to see ngrok dashboard${NC}"
    exit 1
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ HARVEY AI IS LIVE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🌐 Public URL:${NC} ${GREEN}$NGROK_URL${NC}"
echo -e "${YELLOW}📊 Ngrok Dashboard:${NC} http://localhost:4040"
echo -e "${YELLOW}📝 Server Logs:${NC} /tmp/harvey_server.log"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Save URL for later reference
echo "$NGROK_URL" > /tmp/harvey_url.txt

# Open browser
echo -e "${YELLOW}🌐 Opening browser...${NC}"
xdg-open "$NGROK_URL" 2>/dev/null || \
    firefox "$NGROK_URL" 2>/dev/null || \
    google-chrome "$NGROK_URL" 2>/dev/null || \
    chromium "$NGROK_URL" 2>/dev/null &

echo ""
echo -e "${GREEN}🎉 Harvey is ready to use!${NC}"
echo -e "${YELLOW}💡 To stop Harvey, run: ${NC}./stop_harvey.sh"
echo ""
echo -e "${YELLOW}Press Ctrl+C to close this window (Harvey will keep running)${NC}"
echo ""

# Keep script alive to show status
trap "echo -e '${YELLOW}\n👋 Launcher closed. Harvey is still running.${NC}'; exit 0" INT TERM

# Monitor and display stats
while true; do
    sleep 30
    if [ -f /tmp/harvey_url.txt ]; then
        CURRENT_URL=$(cat /tmp/harvey_url.txt)
        echo -e "${GREEN}[$(date +'%H:%M:%S')] Harvey is running at: $CURRENT_URL${NC}"
    fi
done
