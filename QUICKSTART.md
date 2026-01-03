# Quick Start Guide

Get Harvey Local Audio up and running in minutes!

## Prerequisites

- Python 3.10 or higher
- 16GB+ RAM (recommended)
- NVIDIA GPU with CUDA support (optional, but recommended for best performance)
- ~20GB free disk space (for models)

## Installation

### Linux/Mac

1. **Clone or download this repository**

2. **Run the installation script:**
```bash
chmod +x install.sh
./install.sh
```

The installation script will:
- Check Python version
- Install Ollama (if not present)
- Download Gemma 3 14B model
- Install Coqui XTTS v2 (via requirements.txt)
- Set up Python virtual environments
- Create launcher scripts

### Windows

1. **Download and install Ollama** from https://ollama.com/download

2. **Run the installation script:**
```cmd
install.bat
```

## Starting the Server

### Option 1: Desktop Application (Recommended)

**Linux/Mac:**
```bash
./run-desktop-app.sh
```

**Windows:**
```cmd
run-desktop-app.bat
```

The desktop app provides:
- One-click server start/stop
- WebSocket URL and API key display
- Voice configuration interface
- Real-time server logs
- Connection instructions

### Option 2: Command Line

**Linux/Mac:**
```bash
./run-server.sh
```

**Windows:**
```cmd
run-server.bat
```

## Using the Server

### 1. Get Your Connection Info

After starting the server (via desktop app or command line), you'll see:

```
WebSocket URL: ws://localhost:8765/ws/audio
API Key: [your-generated-api-key]
```

### 2. Test with Example Client

**Python:**
```bash
cd examples
# Edit client-python.py and add your API key
python client-python.py
```

**JavaScript:**
```bash
cd examples
npm install ws
# Edit client-javascript.js and add your API key
node client-javascript.js
```

### 3. Connect from Your Application

See the [README.md](README.md) for detailed integration examples.

## Basic Usage

### Send Audio for Conversation

```python
import websockets
import asyncio
import json
import base64

async def talk():
    uri = "ws://localhost:8765/ws/audio"
    headers = {"X-API-Key": "your-api-key"}

    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Send audio
        with open("my-voice.wav", "rb") as f:
            audio = base64.b64encode(f.read()).decode()

        await ws.send(json.dumps({
            "type": "audio",
            "data": audio,
            "format": "wav",
            "sample_rate": 16000
        }))

        # Get response
        response = json.loads(await ws.recv())
        print(f"AI said: {response['text']}")

        # Save response audio
        with open("response.wav", "wb") as f:
            f.write(base64.b64decode(response['audio']))

asyncio.run(talk())
```

### Send Text (for Testing)

```python
await ws.send(json.dumps({
    "type": "text",
    "text": "Hello, tell me a joke"
}))
```

## Configuration

Edit `backend/config.yaml` to customize:

- **LLM Model**: Change `llm.model` to use different models
- **Voice**: Change `tts.voice` for different voices (default, male, female, custom)
- **TTS Language**: Change `tts.language` for different output languages
- **STT Language**: Change `stt.language` for non-English input
- **Performance**: Adjust `stt.model` size (tiny/small/medium/large)

Example TTS voices:
- `default` (Natural XTTS voice)
- `male` (Add custom male voice sample)
- `female` (Add custom female voice sample)
- `custom` (Use your own voice cloning sample)

Supported TTS Languages:
- English (en), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt)
- Polish (pl), Turkish (tr), Russian (ru), Dutch (nl), Czech (cs), Arabic (ar)
- Chinese (zh-cn), Japanese (ja)

## Troubleshooting

### "Ollama connection failed"

```bash
# Check if Ollama is running
ollama list

# Start Ollama (Linux/Mac)
systemctl start ollama

# Pull the model again
ollama pull gemma3:14b
```

### "CUDA not available"

The system will automatically fall back to CPU. For faster performance:
- Install NVIDIA drivers
- Install CUDA toolkit
- Reinstall PyTorch with CUDA support:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

### High Latency

- Use smaller Whisper model: `stt.model: "medium"` or `"small"`
- Reduce `llm.max_tokens` to 1024
- Ensure CUDA is enabled for GPU acceleration

### Port Already in Use

Change the port in `backend/config.yaml`:
```yaml
server:
  port: 8766  # Use different port
```

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check out [examples/](examples/) for more integration examples
- Customize the system prompt in config for different personalities
- Explore different TTS voices and LLM models

## Support

For issues and questions:
- Check the README.md troubleshooting section
- Review example code in `examples/`
- Check server logs in desktop app or `backend/logs/server.log`

Enjoy your self-hosted voice AI! 🎙️🤖
