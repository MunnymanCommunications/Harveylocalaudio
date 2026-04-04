

# Harvey AI Flash Drive Setup Guide

Complete guide to creating a portable, offline installer flash drive that anyone can use to install Harvey AI on any computer **without internet or technical knowledge**.

## 📦 What You're Building

A flash drive that contains:
- ✅ All installers (Python, Ollama)
- ✅ AI Model (Nemotron 3 Nano 30B - ~17GB)
- ✅ All Python packages (pre-downloaded)
- ✅ Harvey AI application
- ✅ One-click installer for Windows, Mac, Linux
- ✅ Beautiful HTML launcher

**Total Size Needed:** 32GB+ flash drive (64GB recommended)

## 🎯 Flash Drive Structure

```
HARVEY-AI-PORTABLE/
├── INSTALL-LAUNCHER.html          ← Open this first!
├── INSTALL-HARVEY.bat             ← Windows installer
├── INSTALL-HARVEY.sh              ← Mac/Linux installer
├── README.md                      ← Quick start guide
│
├── installers/                    ← Platform installers
│   ├── python-3.10-installer.exe  (Windows)
│   ├── OllamaSetup.exe           (Windows)
│   └── Ollama.dmg                (Mac)
│
├── models/                        ← AI models (largest files)
│   └── nemotron-3-nano-30b.gguf  (~17GB)
│
├── wheels/                        ← Python packages (offline install)
│   ├── torch-*.whl
│   ├── TTS-*.whl
│   └── [all other .whl files]
│
├── backend/                       ← Harvey backend
├── desktop-app/                   ← Desktop GUI
├── web-client/                    ← Web interface
└── [other project files]
```

## 📥 Step-by-Step Build Process

### Step 1: Prepare Your Flash Drive

1. **Get a 64GB+ flash drive** (USB 3.0 for speed)
2. **Format as exFAT** (works on Windows, Mac, Linux)
   - Windows: Right-click drive → Format → exFAT
   - Mac: Disk Utility → Erase → exFAT
   - Linux: `sudo mkfs.exfat /dev/sdX1`

3. **Create folder structure:**
   ```bash
   mkdir -p HARVEY-AI-PORTABLE/{installers,models,wheels}
   ```

### Step 2: Download Platform Installers

#### Windows Python Installer
```
1. Go to: https://www.python.org/downloads/
2. Download: "Windows installer (64-bit)"
3. Save as: installers/python-3.10-installer.exe
```

#### Windows Ollama Installer
```
1. Go to: https://ollama.com/download
2. Download: "OllamaSetup.exe"
3. Save as: installers/OllamaSetup.exe
```

#### Mac Ollama Installer
```
1. Go to: https://ollama.com/download
2. Download: "Ollama-darwin.zip" or "Ollama.dmg"
3. Save as: installers/Ollama.dmg
```

### Step 3: Download AI Model (IMPORTANT!)

This is the largest and most important file.

#### Method A: Download via Ollama (Recommended)

```bash
# 1. Install Ollama on your computer first
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the model
ollama pull nemotron-3-nano:30b

# 3. Find the model file
# Mac/Linux: ~/.ollama/models/
# Windows: C:\Users\YourName\.ollama\models\

# 4. Find the .gguf file (it might be nested in manifests/blobs)
# Look for a large file (~17GB)

# 5. Copy to flash drive
cp ~/.ollama/models/[model-hash] /path/to/flashdrive/models/nemotron-3-nano-30b.gguf
```

#### Method B: Direct Download (If Available)

```bash
# Some models available directly from Hugging Face
# Search for: "nemotron-3-nano GGUF"
# Download and rename to: nemotron-3-nano-30b.gguf
```

**⚠️ CRITICAL:** This file is ~17GB. Make sure you have it!

### Step 4: Download Python Packages (Offline Wheels)

Create a complete offline package repository:

```bash
# Create a temporary directory
mkdir temp-download

# Download all backend requirements
cd backend
pip download -r requirements.txt -d ../temp-download/wheels/

# Download desktop-app requirements
cd ../desktop-app
pip download -r requirements.txt -d ../temp-download/wheels/

# Copy wheels to flash drive
cp -R ../temp-download/wheels /path/to/flashdrive/HARVEY-AI-PORTABLE/
```

**Alternative (faster):**
```bash
# Download everything in one go
pip download \
    torch torchaudio TTS \
    fastapi uvicorn websockets \
    PyQt6 numpy scipy soundfile \
    openai-whisper ollama \
    -d /path/to/flashdrive/HARVEY-AI-PORTABLE/wheels/
```

### Step 5: Copy Harvey AI Files

```bash
# Copy entire Harvey project to flash drive
cp -R Harveylocalaudio/* /path/to/flashdrive/HARVEY-AI-PORTABLE/

# Make sure these files are there:
# - INSTALL-LAUNCHER.html (you created this)
# - INSTALL-HARVEY.bat (you created this)
# - INSTALL-HARVEY.sh (you created this)
# - backend/
# - desktop-app/
# - web-client/
```

### Step 6: Test Your Flash Drive!

Before distributing:

1. **Test on Windows:**
   - Plug in flash drive
   - Double-click `INSTALL-LAUNCHER.html`
   - Click "Install Harvey AI"
   - Wait for installation
   - Verify desktop shortcut works

2. **Test on Mac:**
   - Plug in flash drive
   - Open `INSTALL-LAUNCHER.html` in browser
   - Or run `./INSTALL-HARVEY.sh` in Terminal

3. **Test on Linux:**
   - Same as Mac

## 🎨 Optional: Customize the Flash Drive

### Add a Nice Icon

**Windows:**
Create `autorun.inf`:
```ini
[autorun]
icon=harvey-icon.ico
label=Harvey AI Installer
```

Add `harvey-icon.ico` to root of flash drive.

### Add a README.txt

Create `README.txt` at root:
```
HARVEY AI - VOICE CONVERSATIONAL AI
====================================

QUICK START:
1. Open INSTALL-LAUNCHER.html in your web browser
2. Click "Install Harvey AI"
3. Follow the on-screen instructions
4. Done! Look for Harvey AI on your desktop

WHAT IS HARVEY?
- 100% offline voice AI assistant
- Complete privacy - everything runs locally
- Natural conversations with voice cloning
- Supports 14+ languages

SYSTEM REQUIREMENTS:
- Windows 10/11, macOS 10.15+, or Linux
- 16GB+ RAM recommended
- 30GB free disk space
- Works without internet after installation

NEED HELP?
See QUICKSTART-SERVER.md for detailed instructions.
```

## 📊 Size Breakdown

Here's what takes up space:

| Item | Size | Required? |
|------|------|-----------|
| Nemotron Model | ~17GB | ✅ YES |
| Python Wheels | ~3-5GB | ✅ YES |
| Python Installer | ~30MB | ✅ YES |
| Ollama Installer | ~500MB | ✅ YES |
| Harvey Code | ~50MB | ✅ YES |
| **Total** | **~20-23GB** | |

**Recommended Flash Drive:** 64GB (gives room for updates)

## ⚡ Quick Build Script (Linux/Mac)

Save this as `build-flashdrive.sh`:

```bash
#!/bin/bash
set -e

FLASH_DRIVE="/Volumes/HARVEY"  # Change to your flash drive path
BUILD_DIR="$FLASH_DRIVE/HARVEY-AI-PORTABLE"

echo "Building Harvey AI Flash Drive..."

# Create structure
mkdir -p "$BUILD_DIR"/{installers,models,wheels}

# Copy Harvey files
echo "Copying Harvey files..."
cp -R backend desktop-app web-client *.md *.html *.sh *.bat "$BUILD_DIR/"

# Download installers
echo "Downloading installers..."
cd "$BUILD_DIR/installers"

# Python (you'll need to download manually)
echo "Download Python installer manually and place in installers/"

# Ollama
if [ ! -f "OllamaSetup.exe" ]; then
    echo "Download Ollama installer manually"
fi

# Download wheels
echo "Downloading Python packages..."
cd "$BUILD_DIR"
pip download -r backend/requirements.txt -d wheels/
pip download -r desktop-app/requirements.txt -d wheels/

echo "Flash drive structure created!"
echo "IMPORTANT: Copy AI model to: $BUILD_DIR/models/nemotron-3-nano-30b.gguf"
echo "          Download from Ollama or Hugging Face"
```

## 🚀 Distribution Checklist

Before giving flash drive to users:

- [ ] `INSTALL-LAUNCHER.html` opens in browser
- [ ] `installers/` folder has Python + Ollama installers
- [ ] `models/nemotron-3-nano-30b.gguf` exists (~17GB)
- [ ] `wheels/` folder has all Python packages
- [ ] Tested on at least one Windows, Mac, or Linux machine
- [ ] `README.txt` explains how to use
- [ ] Flash drive labeled "HARVEY AI INSTALLER"

## 💾 Alternative: Create Multiple Versions

For different use cases:

### Minimal Version (No Model)
- ~3GB total
- Users download model during install (needs internet once)
- Good for: Testing, development

### Full Version (Everything Bundled)
- ~20GB total  
- Complete offline installation
- Good for: No-internet environments, field deployment

### USB Stick vs Cloud Storage

**USB Stick Pros:**
- ✅ Works offline
- ✅ Fast installation
- ✅ Give to anyone

**Cloud Download Pros:**
- ✅ Easy updates
- ✅ No physical media
- ✅ Always latest version

## 🔄 Updating the Flash Drive

When Harvey gets updates:

1. Download latest Harvey code from GitHub
2. Replace `backend/`, `desktop-app/`, `web-client/` folders
3. Update `wheels/` if requirements changed
4. Update model if new version available
5. Test installation again

## 🆘 Troubleshooting Build Process

### "Not enough space" Error

- Check flash drive capacity: `df -h /path/to/drive`
- Model file alone is 17GB - need 64GB drive minimum

### "Permission denied" on Mac/Linux

```bash
chmod +x INSTALL-HARVEY.sh
chmod +x build-flashdrive.sh
```

### Model Download Fails

Ollama stores models in blob format. Finding the actual file:

```bash
# Mac/Linux
cd ~/.ollama/models
find . -type f -size +10G  # Find files > 10GB

# Windows PowerShell
cd $env:USERPROFILE\.ollama\models
Get-ChildItem -Recurse | Where-Object {$_.Length -gt 10GB}
```

## 📚 Resources

- **Ollama Models:** https://ollama.com/library
- **Python Downloads:** https://www.python.org/downloads/
- **Harvey GitHub:** [your-repo-url]

## ✅ Final Result

When done, users can:

1. Plug in flash drive
2. Open `INSTALL-LAUNCHER.html`
3. Click ONE button
4. Wait 10-30 minutes
5. Have fully functional Harvey AI!

**No internet, no command line, no technical knowledge required!** 🎉

---

**Questions?** See `QUICKSTART-SERVER.md` or `SETUP.md` for more details.
