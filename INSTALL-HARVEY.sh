#!/bin/bash
# ========================================================
# Harvey AI - Automated One-Click Installer for Mac/Linux
# No internet required - Everything bundled on flash drive
# ========================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get model selection from parameter (default to gemma2:9b)
SELECTED_MODEL="${1:-gemma2:9b}"

# Get the directory where this script is located (flash drive)
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST_DIR="$HOME/Harvey-AI"

echo ""
echo "========================================================"
echo "           HARVEY AI INSTALLER"
echo "    Voice Conversational AI - Local Setup"
echo "========================================================"
echo ""
echo "This will install Harvey AI on your computer."
echo "Everything is included - no internet needed!"
echo ""
echo -e "${GREEN}Selected AI Model:${NC} $SELECTED_MODEL"
echo ""
echo "Installation will take 10-30 minutes."
echo ""
read -p "Press Enter to continue..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    echo -e "${GREEN}[OK]${NC} macOS detected"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${GREEN}[OK]${NC} Linux detected"
else
    echo -e "${RED}[ERROR]${NC} Unsupported OS"
    exit 1
fi

echo ""
echo "[1/7] Checking system requirements..."
echo ""

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${GREEN}[OK]${NC} Python $PYTHON_VERSION detected"

    # Check if version is 3.10+
    if [ "$(echo "$PYTHON_VERSION >= 3.10" | bc)" -eq 1 ]; then
        echo -e "${GREEN}[OK]${NC} Python version is sufficient"
    else
        echo -e "${YELLOW}[WARNING]${NC} Python 3.10+ recommended (have $PYTHON_VERSION)"
    fi
else
    echo -e "${YELLOW}[WARNING]${NC} Python 3 not found"

    if [ "$OS" == "mac" ]; then
        echo "Installing Python via Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python@3.10
    else
        echo -e "${RED}[ERROR]${NC} Please install Python 3.10+ manually:"
        echo "  Ubuntu/Debian: sudo apt install python3.10"
        echo "  Fedora: sudo dnf install python3.10"
        exit 1
    fi
fi

echo ""
echo "[2/7] Installing Ollama AI Runtime..."
echo ""

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}[OK]${NC} Ollama already installed"
else
    echo "Installing Ollama..."

    # Check for bundled installer
    if [ "$OS" == "mac" ] && [ -f "$INSTALL_DIR/installers/Ollama.dmg" ]; then
        echo "Installing from bundled DMG..."
        hdiutil attach "$INSTALL_DIR/installers/Ollama.dmg"
        cp -R /Volumes/Ollama/Ollama.app /Applications/
        hdiutil detach /Volumes/Ollama
    else
        # Download installer
        if [ "$OS" == "mac" ]; then
            curl -fsSL https://ollama.com/install.sh | sh
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    fi

    echo -e "${GREEN}[OK]${NC} Ollama installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
if [ "$OS" == "mac" ]; then
    open -a Ollama &>/dev/null || ollama serve &>/dev/null &
else
    ollama serve &>/dev/null &
fi
sleep 3

echo ""
echo "[3/7] Loading AI Model ($SELECTED_MODEL)..."
echo "This may take a few minutes..."
echo ""

# Convert model name to filename (replace : with -)
MODEL_FILENAME="${SELECTED_MODEL//:/-}"

# Check if model is already loaded
if ollama list | grep -q "$SELECTED_MODEL"; then
    echo -e "${GREEN}[OK]${NC} AI model already loaded"
else
    # Check for bundled model
    if [ -f "$INSTALL_DIR/models/${MODEL_FILENAME}.gguf" ]; then
        echo "Loading model from flash drive..."
        echo "Please be patient..."

        # Create Ollama models directory
        mkdir -p "$HOME/.ollama/models"

        # Copy model
        echo "Copying model file..."
        cp "$INSTALL_DIR/models/${MODEL_FILENAME}.gguf" "$HOME/.ollama/models/"

        # Create modelfile
        echo "FROM ${MODEL_FILENAME}.gguf" > /tmp/Modelfile

        # Load into Ollama
        ollama create "$SELECTED_MODEL" -f /tmp/Modelfile

        echo -e "${GREEN}[OK]${NC} Model loaded successfully"
    else
        echo "Model not found on flash drive."
        echo "Downloading from internet (requires connection)..."
        if ollama pull "$SELECTED_MODEL"; then
            echo -e "${GREEN}[OK]${NC} Model downloaded successfully"
        else
            echo -e "${YELLOW}[WARNING]${NC} Model download failed"
            echo "You can download it later by running:"
            echo "  ollama pull $SELECTED_MODEL"
        fi
    fi
fi

# Update config.yaml with selected model
echo ""
echo "Updating configuration with selected model..."
if [ -f "$DEST_DIR/backend/config.yaml" ]; then
    sed -i.bak "s/model: .*/model: \"$SELECTED_MODEL\"/" "$DEST_DIR/backend/config.yaml"
    echo -e "${GREEN}[OK]${NC} Configuration updated"
fi

echo ""
echo "[4/7] Copying Harvey AI files..."
echo ""

# Create destination directory
mkdir -p "$DEST_DIR"

echo "Copying application files..."
cp -R "$INSTALL_DIR/backend" "$DEST_DIR/"
cp -R "$INSTALL_DIR/desktop-app" "$DEST_DIR/"
cp -R "$INSTALL_DIR/web-client" "$DEST_DIR/"
cp "$INSTALL_DIR"/*.sh "$DEST_DIR/" 2>/dev/null || true
cp "$INSTALL_DIR"/*.md "$DEST_DIR/" 2>/dev/null || true

# Make scripts executable
chmod +x "$DEST_DIR"/*.sh 2>/dev/null || true

echo -e "${GREEN}[OK]${NC} Files copied to: $DEST_DIR"

echo ""
echo "[5/7] Installing Python dependencies..."
echo ""

# Install backend dependencies
echo "Installing backend dependencies (this may take 5-10 minutes)..."
cd "$DEST_DIR/backend"

python3 -m venv venv
source venv/bin/activate

if [ -d "$INSTALL_DIR/wheels" ]; then
    echo "Installing from bundled packages..."
    pip install --no-index --find-links="$INSTALL_DIR/wheels" -r requirements.txt
else
    echo "Installing from PyPI (requires internet)..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} Backend dependencies installed"
else
    echo -e "${YELLOW}[WARNING]${NC} Some dependencies failed to install"
fi

deactivate

# Install desktop app dependencies
echo "Installing desktop app dependencies..."
cd "$DEST_DIR/desktop-app"
python3 -m venv venv
source venv/bin/activate

if [ -d "$INSTALL_DIR/wheels" ]; then
    pip install --no-index --find-links="$INSTALL_DIR/wheels" -r requirements.txt
else
    pip install -r requirements.txt
fi

deactivate

echo ""
echo "[6/7] Creating launcher scripts..."
echo ""

# Create launcher script
cat > "$DEST_DIR/LAUNCH-HARVEY.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/desktop-app"
source venv/bin/activate
python app.py
EOF

chmod +x "$DEST_DIR/LAUNCH-HARVEY.sh"

if [ "$OS" == "mac" ]; then
    # Create macOS app bundle
    echo "Creating macOS application..."

    APP_DIR="$HOME/Applications/Harvey AI.app"
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"

    # Create Info.plist
    cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>harvey</string>
    <key>CFBundleName</key>
    <string>Harvey AI</string>
    <key>CFBundleIdentifier</key>
    <string>com.harveyai.app</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
</dict>
</plist>
EOF

    # Create launcher
    cat > "$APP_DIR/Contents/MacOS/harvey" << EOF
#!/bin/bash
cd "$DEST_DIR/desktop-app"
source venv/bin/activate
python app.py
EOF

    chmod +x "$APP_DIR/Contents/MacOS/harvey"

    echo -e "${GREEN}[OK]${NC} macOS app created in Applications folder"

elif [ "$OS" == "linux" ]; then
    # Create Linux desktop entry
    echo "Creating desktop shortcut..."

    mkdir -p "$HOME/.local/share/applications"

    cat > "$HOME/.local/share/applications/harvey-ai.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Harvey AI
Comment=Voice Conversational AI
Exec=$DEST_DIR/LAUNCH-HARVEY.sh
Icon=utilities-terminal
Terminal=false
Categories=Utility;Application;
EOF

    chmod +x "$HOME/.local/share/applications/harvey-ai.desktop"

    # Also create desktop shortcut
    cp "$HOME/.local/share/applications/harvey-ai.desktop" "$HOME/Desktop/" 2>/dev/null || true
    chmod +x "$HOME/Desktop/harvey-ai.desktop" 2>/dev/null || true

    echo -e "${GREEN}[OK]${NC} Desktop shortcut created"
fi

echo ""
echo "========================================================"
echo "           INSTALLATION COMPLETE!"
echo "========================================================"
echo ""
echo "Harvey AI has been successfully installed!"
echo ""
echo "Location: $DEST_DIR"
echo ""
echo "To start Harvey AI:"

if [ "$OS" == "mac" ]; then
    echo "  1. Open 'Harvey AI' from Applications folder"
    echo "  OR"
    echo "  2. Run: $DEST_DIR/LAUNCH-HARVEY.sh"
else
    echo "  1. Click 'Harvey AI' icon on your desktop"
    echo "  OR"
    echo "  2. Run: $DEST_DIR/LAUNCH-HARVEY.sh"
fi

echo ""
echo "IMPORTANT: Keep your flash drive safe!"
echo "It contains the original files and can be used"
echo "to install Harvey on other computers."
echo ""
echo "========================================================"
echo ""
read -p "Press Enter to launch Harvey AI now..."

# Launch Harvey AI
"$DEST_DIR/LAUNCH-HARVEY.sh" &

echo "Harvey AI is starting..."
echo "The application window will open shortly."

exit 0
