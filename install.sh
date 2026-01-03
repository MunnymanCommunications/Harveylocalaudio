#!/bin/bash
# Harvey Local Audio - Installation Script

set -e

echo "======================================="
echo "Harvey Local Audio - Installation"
echo "======================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10+ is required (found Python $python_version)"
    exit 1
fi

echo "Python $python_version detected ✓"
echo ""

# Check if Ollama is installed
echo "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama installed ✓"
else
    echo "Ollama already installed ✓"
fi
echo ""

# Pull Gemma 2 9B model (or your preferred model)
echo "Pulling Gemma 2 9B model (this may take a while)..."
echo "Note: You can change the model in backend/config.yaml"
ollama pull gemma2:9b
echo "Gemma 2 9B model ready ✓"
echo ""

# Create virtual environment for backend
echo "Setting up backend environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo "Backend environment ready ✓"
echo ""

# Create virtual environment for desktop app
echo "Setting up desktop app environment..."
cd desktop-app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo "Desktop app environment ready ✓"
echo ""

# Create launcher scripts
echo "Creating launcher scripts..."

# Desktop app launcher
cat > run-desktop-app.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/desktop-app"
source venv/bin/activate
python app.py
EOF

chmod +x run-desktop-app.sh

# Backend server launcher (for command line)
cat > run-server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
python main.py
EOF

chmod +x run-server.sh

echo "Launcher scripts created ✓"
echo ""

echo "======================================="
echo "Installation Complete!"
echo "======================================="
echo ""
echo "To start the desktop application:"
echo "  ./run-desktop-app.sh"
echo ""
echo "Or to run the server directly:"
echo "  ./run-server.sh"
echo ""
echo "The desktop app provides an easy GUI to:"
echo "  - Start/stop the server"
echo "  - View WebSocket URL and API key"
echo "  - Configure voice settings"
echo "  - Monitor server logs"
echo ""
