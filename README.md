# Harvey Local Audio - Self-Hosted Voice Conversation System

Complete audio-to-audio pipeline with WebSocket support for low-latency voice conversations using Gemma 3 14B.

## Features

- **Low Latency**: ~300-500ms end-to-end latency
- **WebSocket API**: Real-time bidirectional communication
- **Self-Hosted**: Complete privacy and control
- **Desktop Management App**: Easy server control and configuration
- **Gemma 3 14B**: Powerful local LLM for natural conversations
- **High-Quality Audio**: Whisper Large-v3 STT + Piper TTS

## Architecture

```
Audio Input → Whisper (STT) → Gemma 3 14B (LLM) → Piper (TTS) → Audio Output
                                    ↓
                            WebSocket Connection
```

## Quick Start

### 1. Install Dependencies

#### System Requirements
- Python 3.10+
- CUDA-capable GPU (recommended for best performance)
- 16GB+ RAM
- Ollama installed

#### Install Ollama and Gemma 3
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Gemma 3 14B model
ollama pull gemma3:14b
```

#### Install Python Dependencies
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Desktop App
cd ../desktop-app
pip install -r requirements.txt
```

### 2. Start the Server

#### Option A: Using Desktop App (Recommended)
```bash
cd desktop-app
python app.py
```
Then click "Start Server" in the GUI.

#### Option B: Command Line
```bash
cd backend
python main.py
```

### 3. Connect to WebSocket

**WebSocket URL**: `ws://localhost:8765/ws/audio`

**Authentication**: Include API key in connection headers:
```javascript
const ws = new WebSocket('ws://localhost:8765/ws/audio', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
});
```

## Desktop Application Features

- **Server Control**: Start/Stop server with one click
- **Connection Info**: Copy WebSocket URL and API key
- **Voice Configuration**: Adjust voice settings (speed, pitch, model)
- **Server Status**: Real-time monitoring
- **Logs Viewer**: See server activity

## Configuration

Edit `backend/config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8765
  api_key: "auto-generated"

llm:
  model: "gemma3:14b"
  temperature: 0.7
  max_tokens: 2048

stt:
  model: "large-v3"
  language: "en"
  device: "cuda"

tts:
  engine: "piper"
  voice: "en_US-lessac-medium"
  speed: 1.0
```

## API Documentation

### WebSocket Protocol

#### Send Audio (Client → Server)
```json
{
  "type": "audio",
  "data": "<base64-encoded-audio>",
  "format": "wav",
  "sample_rate": 16000
}
```

#### Receive Response (Server → Client)
```json
{
  "type": "audio_response",
  "text": "Transcribed and LLM response text",
  "audio": "<base64-encoded-audio>",
  "latency_ms": 350
}
```

#### Configuration Update
```json
{
  "type": "configure",
  "settings": {
    "voice": "en_US-amy-medium",
    "temperature": 0.8
  }
}
```

## Integration Examples

### JavaScript/Node.js
```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8765/ws/audio', {
  headers: { 'X-API-Key': 'your-api-key' }
});

ws.on('open', () => {
  // Send audio data
  const audioBuffer = fs.readFileSync('audio.wav');
  ws.send(JSON.stringify({
    type: 'audio',
    data: audioBuffer.toString('base64'),
    format: 'wav',
    sample_rate: 16000
  }));
});

ws.on('message', (data) => {
  const response = JSON.parse(data);
  console.log('Response:', response.text);
  // Play response.audio
});
```

### Python
```python
import websockets
import asyncio
import base64

async def audio_conversation():
    uri = "ws://localhost:8765/ws/audio"
    headers = {"X-API-Key": "your-api-key"}

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Send audio
        with open("audio.wav", "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()

        await websocket.send(json.dumps({
            "type": "audio",
            "data": audio_data,
            "format": "wav",
            "sample_rate": 16000
        }))

        # Receive response
        response = json.loads(await websocket.recv())
        print(f"Response: {response['text']}")

asyncio.run(audio_conversation())
```

## Troubleshooting

### GPU Not Detected
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

### Ollama Connection Failed
```bash
# Check Ollama is running
ollama list

# Restart Ollama service
systemctl restart ollama  # Linux
```

### High Latency
- Use smaller Whisper model (`medium` or `small` instead of `large-v3`)
- Reduce `max_tokens` in LLM config
- Ensure CUDA is enabled

## License

MIT License - See LICENSE file for details
