# Model Selection Guide for Harvey AI Flash Drive

Complete guide for bundling multiple AI models on your flash drive so users can choose based on their hardware.

## 🎯 Recommended Models to Bundle

### Essential (Include These 3):

| Model | Size | RAM Needed | Best For |
|-------|------|------------|----------|
| **gemma2:2b** | ~1.5GB | 4GB | Old laptops, instant responses |
| **gemma2:9b** | ~5.5GB | 8GB | Most users (recommended) |
| **qwen2.5:14b** | ~9GB | 16GB | Power users, best quality |

**Total:** ~16GB (fits on 32GB drive with room for everything else)

### Optional (Add If You Have 64GB+ Drive):

| Model | Size | RAM Needed | Best For |
|-------|------|------------|----------|
| **qwen2.5:3b** | ~2GB | 6GB | Low-end systems |
| **nemotron-mini:15b** | ~9GB | 16GB | Conversational quality |
| **nemotron-3-nano:30b** | ~17GB | 32GB+ | Maximum quality |

## 📥 How to Download Models for Flash Drive

### Step 1: Install Ollama on Your Computer

```bash
# Mac/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from: https://ollama.com/download
```

### Step 2: Download Each Model

```bash
# Ultra Fast (1.5GB)
ollama pull gemma2:2b

# Balanced (2GB)  
ollama pull qwen2.5:3b

# Recommended (5.5GB)
ollama pull gemma2:9b

# High Quality (9GB)
ollama pull qwen2.5:14b

# Advanced (9GB)
ollama pull nemotron-mini:15b

# Maximum Power (17GB)
ollama pull nemotron-3-nano:30b
```

### Step 3: Find the Model Files

Models are stored in Ollama's data directory:

**Mac/Linux:**
```bash
cd ~/.ollama/models/manifests/registry.ollama.ai/library
ls -la
```

**Windows:**
```powershell
cd $env:USERPROFILE\.ollama\models\manifests\registry.ollama.ai\library
dir
```

You'll see folders for each model. Inside each folder is a manifest file.

### Step 4: Export Models to Flash Drive

**Mac/Linux:**
```bash
#!/bin/bash
# Script to export models to flash drive

FLASH_DRIVE="/Volumes/HARVEY/models"  # Change to your path
mkdir -p "$FLASH_DRIVE"

# Export each model
for model in gemma2:2b qwen2.5:3b gemma2:9b qwen2.5:14b; do
    echo "Exporting $model..."
    MODEL_FILE="${model//:/-}"
    
    # Find the actual model file
    BLOB_PATH=$(ollama show $model --modelfile | grep "FROM" | awk '{print $2}')
    
    if [ -f "$BLOB_PATH" ]; then
        cp "$BLOB_PATH" "$FLASH_DRIVE/${MODEL_FILE}.gguf"
        echo "✓ Exported $model"
    else
        # Alternate method: use ollama's built-in export
        ollama cp $model > "$FLASH_DRIVE/${MODEL_FILE}.gguf"
    fi
done

echo "All models exported!"
```

### Step 5: Verify Flash Drive Structure

Your flash drive should look like this:

```
HARVEY-AI-PORTABLE/
├── models/
│   ├── gemma2-2b.gguf           (~1.5GB)
│   ├── qwen2.5-3b.gguf          (~2GB)
│   ├── gemma2-9b.gguf           (~5.5GB)
│   ├── qwen2.5-14b.gguf         (~9GB)
│   ├── nemotron-mini-15b.gguf   (~9GB)
│   └── nemotron-3-nano-30b.gguf (~17GB)
```

## 🎨 Model Comparison Chart

### For Different Hardware Levels:

#### 💻 Old Laptop (4GB RAM, No GPU)
```
✅ gemma2:2b
   - Response: <200ms
   - Quality: Basic but fast
   - Perfect for: Quick answers, simple tasks
```

#### 💻 Standard Laptop (8GB RAM)
```
✅ gemma2:9b (RECOMMENDED)
   - Response: ~400ms
   - Quality: Very good
   - Perfect for: Most users
```

#### 🖥️ Desktop (16GB RAM)
```
✅ qwen2.5:14b
   - Response: ~600ms
   - Quality: Excellent
   - Perfect for: Detailed conversations
```

#### 🔥 Gaming PC (32GB+ RAM, GPU)
```
✅ nemotron-3-nano:30b
   - Response: ~800ms
   - Quality: Best
   - Perfect for: Maximum quality
```

## 📊 Space Planning

### Option 1: Minimal Bundle (32GB Drive)
```
Models (3):
- gemma2:2b      1.5GB
- gemma2:9b      5.5GB
- qwen2.5:14b    9GB
Total:           16GB

Plus:
- Installers     0.5GB
- Python wheels  3GB
- Harvey code    0.5GB
TOTAL:          ~20GB
```

### Option 2: Complete Bundle (64GB Drive)
```
Models (6):
- gemma2:2b              1.5GB
- qwen2.5:3b             2GB
- gemma2:9b              5.5GB
- qwen2.5:14b            9GB
- nemotron-mini:15b      9GB
- nemotron-3-nano:30b    17GB
Total:                   44GB

Plus:
- Installers             0.5GB
- Python wheels          3GB
- Harvey code            0.5GB
TOTAL:                  ~48GB
```

## 🚀 Quick Export Script

Save as `export-models.sh`:

```bash
#!/bin/bash
# Export Ollama models to flash drive

MODELS_DIR="$1"

if [ -z "$MODELS_DIR" ]; then
    echo "Usage: ./export-models.sh /path/to/flashdrive/models"
    exit 1
fi

mkdir -p "$MODELS_DIR"

MODELS=(
    "gemma2:2b"
    "qwen2.5:3b"
    "gemma2:9b"
    "qwen2.5:14b"
)

for MODEL in "${MODELS[@]}"; do
    echo "Exporting $MODEL..."
    MODEL_FILE="${MODEL//:/-}.gguf"
    
    # Get model manifest
    MANIFEST=$(ollama show $MODEL --modelfile)
    
    # Extract blob hash
    BLOB=$(echo "$MANIFEST" | grep "FROM" | awk '{print $2}')
    
    # Find blob in Ollama storage
    if [ -f "$BLOB" ]; then
        echo "  Copying from: $BLOB"
        cp "$BLOB" "$MODELS_DIR/$MODEL_FILE"
        echo "  ✓ $MODEL_FILE"
    else
        echo "  ✗ Could not find blob for $MODEL"
    fi
done

echo ""
echo "Export complete!"
echo "Models saved to: $MODELS_DIR"
ls -lh "$MODELS_DIR"
```

Usage:
```bash
chmod +x export-models.sh
./export-models.sh /Volumes/HARVEY/models
```

## 🎯 User Selection in HTML

The installer HTML now shows:

```
⚡ Gemma 2B - Ultra Fast
   Perfect for laptops, older computers

⭐ Gemma 9B - Recommended  ← Default
   Best overall choice

💎 Qwen 14B - High Quality
   Excellent reasoning

🔥 Nemotron 30B - Maximum Power
   Requires powerful computer
```

Users just click their choice before installing!

## 🔄 Alternative: Internet Fallback

If you don't want to bundle all models:

1. Bundle only `gemma2:9b` (recommended)
2. Installer will detect missing models
3. Offer to download from internet if available
4. Or install with bundled model only

## 📝 Testing Checklist

Before distributing:

- [ ] All model files exist in `models/` folder
- [ ] Files named correctly: `model-name-version.gguf`
- [ ] Each model loads in Ollama: `ollama create test -f Modelfile`
- [ ] HTML model selector shows all bundled models
- [ ] Installer respects user's model choice
- [ ] Config updates with selected model

## 💡 Pro Tips

**Faster Export:**
```bash
# Use hard links instead of copying (saves time)
ln ~/.ollama/models/blobs/sha256-xyz /path/to/flash/models/gemma2-9b.gguf
```

**Verify Model Quality:**
```bash
# Test each model before bundling
ollama run gemma2:9b "Tell me a joke"
ollama run qwen2.5:14b "Explain quantum physics"
```

**Save Space:**
- Use GGUF format (already compressed)
- Don't include model variants (q4, q5, etc.)
- Bundle quantized versions (smaller files)

## 🎁 Final Result

Users get to choose based on their hardware:

- **Old computer?** → Gemma 2B (still works!)
- **Normal computer?** → Gemma 9B (recommended)
- **Powerful computer?** → Qwen 14B or Nemotron 30B

Everyone gets Harvey AI that works perfectly for their setup! 🎉
