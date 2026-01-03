# Quick Setup Guide for Your Server

## Current Status

You're on the correct branch: `claude/local-gemma-websocket-setup-uEGT7`

## Step-by-Step Setup

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Mac
brew install ollama

# Or download from: https://ollama.com/download
```

After installation, start Ollama:
```bash
# Linux (systemd)
sudo systemctl start ollama

# Or run directly
ollama serve &
```

### 2. Pull Your Preferred Model

**For Gemma 2 9B (recommended, good balance):**
```bash
ollama pull gemma2:9b
```

**Or choose a larger model for better quality:**
```bash
# Qwen 2.5 14B (closest to your original request)
ollama pull qwen2.5:14b

# Gemma 2 27B (most powerful, requires more RAM)
ollama pull gemma2:27b

# Llama 3.1 8B (fast and good quality)
ollama pull llama3.1:8b
```

**Update config if using a different model:**
Edit `backend/config.yaml` line 10:
```yaml
model: "qwen2.5:14b"  # or whichever model you chose
```

### 3. Create Python Virtual Environments

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..

# Desktop App
cd desktop-app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
```

### 4. Start the Server

**Option A: Desktop GUI (Recommended)**
```bash
./run-desktop-app.sh
```

Then click "Start Server" in the GUI.

**Option B: Command Line**
```bash
./run-server.sh
```

## WebSocket Connection

Once the server starts, you'll get:

- **WebSocket URL**: `ws://localhost:8765/ws/audio`
- **API Key**: Check desktop app or `backend/.api_key` file

## Test Connection

```python
import websockets
import asyncio
import json

async def test():
    uri = "ws://localhost:8765/ws/audio"
    headers = {"X-API-Key": "your-api-key-here"}

    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Send text message (for testing without audio)
        await ws.send(json.dumps({
            "type": "text",
            "text": "Hello, can you hear me?"
        }))

        response = json.loads(await ws.recv())
        print(f"Response: {response['text']}")

asyncio.run(test())
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List available models
ollama list

# Restart Ollama
sudo systemctl restart ollama  # Linux
# Or kill and restart: pkill ollama && ollama serve &
```

### CUDA Not Available
The system will automatically fall back to CPU. To enable GPU:
```bash
# Check CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch if needed
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Port Already in Use
Change the port in `backend/config.yaml`:
```yaml
server:
  port: 8766  # or any available port
```

## Model Comparison

| Model | Size | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **gemma2:9b** | 9B | Good | Fast | Balanced performance |
| **qwen2.5:14b** | 14B | Excellent | Medium | Closest to your original request |
| **gemma2:27b** | 27B | Excellent | Slow | Highest quality |
| **llama3.1:8b** | 8B | Good | Very Fast | Quick responses |

## What You're Running

- **STT**: Whisper Large-v3 (high accuracy for accents/slurred speech)
- **LLM**: Gemma 2 9B (configurable)
- **TTS**: Coqui XTTS v2 (voice cloning, 14+ languages)
- **Latency**: ~300-500ms end-to-end

Enjoy your self-hosted voice AI! 🎙️
