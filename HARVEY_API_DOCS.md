# Harvey AI WebSocket API Documentation

## 🔗 Connection Endpoints

### Local Network Access
```
wss://192.168.4.108:8765/ws/audio?api_key=YOUR_API_KEY
```

### Public Access (via ngrok)
```
wss://be15f84a5e11.ngrok-free.app/ws/audio?api_key=YOUR_API_KEY
```

**Note:** ngrok URL changes each time the tunnel restarts. Check the current URL by running:
```bash
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

---

## 🔐 Authentication

### API Key
```
MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w
```

**Location:** Query parameter in WebSocket URL
```
/ws/audio?api_key=MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w
```

**Security Note:** This API key is stored in `/home/nic/Harveylocalaudio/backend/.api_key`

---

## 📡 WebSocket Protocol

### Connection Flow

1. **Connect** to WebSocket endpoint with API key
2. **Receive** `connected` message
3. **Send** audio or text messages
4. **Receive** transcription and AI responses
5. **Handle** errors and reconnections

### Message Types

#### 1. Connection Established (Server → Client)
```json
{
  "type": "connected",
  "message": "Connected to Harvey Audio Server",
  "connection_id": "unique_connection_id",
  "config": {
    "sample_rate": 16000,
    "channels": 1,
    "format": "wav"
  }
}
```

#### 2. Send Audio (Client → Server)
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_data",
  "sample_rate": 16000,
  "format": "wav",
  "mime_type": "audio/wav"
}
```

**Supported Formats:**
- WAV (recommended)
- WebM (Safari)
- MP4 (Mobile browsers)
- OGG

**Audio Specifications:**
- Sample Rate: 16000 Hz (recommended)
- Channels: 1 (mono)
- Encoding: Base64

#### 3. Send Text (Client → Server)
```json
{
  "type": "text",
  "text": "Your message to Harvey"
}
```

#### 4. Audio Response (Server → Client)
```json
{
  "type": "audio_response",
  "transcription": "What you said",
  "text": "Harvey's text response",
  "audio": "base64_encoded_audio_response",
  "latency_ms": 1250,
  "metadata": {
    "stt_time_ms": 350,
    "llm_time_ms": 650,
    "tts_time_ms": 250
  }
}
```

#### 5. Text Response (Server → Client)
```json
{
  "type": "text_response",
  "text": "Harvey's response",
  "audio": "base64_encoded_audio",
  "latency_ms": 800
}
```

#### 6. Error (Server → Client)
```json
{
  "type": "error",
  "message": "Error description"
}
```

#### 7. Configuration Update (Client → Server)
```json
{
  "type": "config",
  "settings": {
    "voice": "en_US-lessac-medium",
    "speed": 1.0
  }
}
```

**Available Voices:**
- `en_US-lessac-medium` (Male)
- `en_US-amy-medium` (Female)
- `en_US-danny-low` (Male, lower quality)

**Speed Range:** 0.5 - 2.0 (default: 1.0)

---

## 💻 Code Examples

### Python Example
```python
import asyncio
import websockets
import json
import base64

API_KEY = "MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w"
WS_URL = f"wss://be15f84a5e11.ngrok-free.app/ws/audio?api_key={API_KEY}"

async def talk_to_harvey():
    async with websockets.connect(WS_URL) as websocket:
        # Wait for connection message
        response = await websocket.recv()
        print("Connected:", json.loads(response))

        # Send text message
        await websocket.send(json.dumps({
            "type": "text",
            "text": "Hello Harvey, how are you?"
        }))

        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print("Harvey:", data['text'])

        # Decode and save audio response
        if 'audio' in data:
            audio_bytes = base64.b64decode(data['audio'])
            with open('response.wav', 'wb') as f:
                f.write(audio_bytes)

asyncio.run(talk_to_harvey())
```

### JavaScript/Node.js Example
```javascript
const WebSocket = require('ws');
const fs = require('fs');

const API_KEY = 'MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w';
const WS_URL = `wss://be15f84a5e11.ngrok-free.app/ws/audio?api_key=${API_KEY}`;

const ws = new WebSocket(WS_URL);

ws.on('open', () => {
    console.log('Connected to Harvey');

    // Send text message
    ws.send(JSON.stringify({
        type: 'text',
        text: 'Hello Harvey!'
    }));
});

ws.on('message', (data) => {
    const message = JSON.parse(data);

    if (message.type === 'connected') {
        console.log('Connection established:', message);
    }
    else if (message.type === 'text_response') {
        console.log('Harvey:', message.text);
        console.log('Latency:', message.latency_ms, 'ms');

        // Save audio response
        if (message.audio) {
            const audioBuffer = Buffer.from(message.audio, 'base64');
            fs.writeFileSync('response.wav', audioBuffer);
        }
    }
    else if (message.type === 'error') {
        console.error('Error:', message.message);
    }
});

ws.on('error', (error) => {
    console.error('WebSocket error:', error);
});
```

### Browser JavaScript Example
```javascript
const API_KEY = 'MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w';
const WS_URL = `wss://be15f84a5e11.ngrok-free.app/ws/audio?api_key=${API_KEY}`;

const ws = new WebSocket(WS_URL);

ws.onopen = () => {
    console.log('Connected to Harvey');

    // Send text
    ws.send(JSON.stringify({
        type: 'text',
        text: 'Hello Harvey!'
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'text_response') {
        console.log('Harvey:', message.text);

        // Play audio response
        if (message.audio) {
            const audioBlob = base64ToBlob(message.audio, 'audio/wav');
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        }
    }
};

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}
```

### Sending Audio Data
```javascript
// Record audio from microphone
async function sendAudioToHarvey() {
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
            sampleRate: 16000,
            channelCount: 1
        }
    });

    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks);
        const arrayBuffer = await audioBlob.arrayBuffer();
        const base64Audio = btoa(
            String.fromCharCode(...new Uint8Array(arrayBuffer))
        );

        ws.send(JSON.stringify({
            type: 'audio',
            data: base64Audio,
            sample_rate: 16000,
            format: 'webm',
            mime_type: 'audio/webm'
        }));
    };

    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 3000); // Record for 3 seconds
}
```

---

## 🔧 System Components

### Speech-to-Text (STT)
- **Engine:** OpenAI Whisper
- **Model:** base (CPU-optimized)
- **Language:** English (en)
- **Device:** CPU
- **Compute Type:** int8

### Large Language Model (LLM)
- **Provider:** Ollama
- **Model:** nemotron-mini
- **Temperature:** 0.4
- **Max Tokens:** 1024
- **Streaming:** Enabled

### Text-to-Speech (TTS)
- **Engine:** Edge TTS
- **Default Voice:** en-US-GuyNeural
- **Speed:** 1.0 (adjustable 0.5-2.0)

### Performance Metrics
- **Average Total Latency:** ~1000-2000ms
- **STT Processing:** ~300-500ms
- **LLM Processing:** ~400-800ms
- **TTS Processing:** ~200-400ms

---

## 🚀 Quick Start

### 1. Test Connection
```bash
curl -k https://be15f84a5e11.ngrok-free.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "audio_pipeline": true,
  "active_connections": 0,
  "stt_ready": true,
  "llm_ready": true,
  "tts_ready": true,
  "llm_model": "nemotron-mini",
  "stt_model": "base"
}
```

### 2. Connect via WebSocket
Use any WebSocket client or the code examples above.

### 3. Send Your First Message
```json
{
  "type": "text",
  "text": "Hello Harvey, introduce yourself!"
}
```

---

## 📊 Rate Limits & Constraints

- **Concurrent Connections:** Unlimited (within server resources)
- **Message Size:** Audio files should be <10MB
- **Audio Duration:** Recommended <30 seconds per message
- **No rate limiting** currently enforced

---

## 🛠️ Troubleshooting

### Connection Issues
```python
# Test with verbose logging
import websockets
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Audio Not Transcribing
- Ensure audio is 16kHz sample rate
- Use WAV format when possible
- Check audio is mono (1 channel)
- Verify base64 encoding is correct

### Slow Responses
- Check `/health` endpoint for component status
- Local network: Use `wss://192.168.4.108:8765`
- Monitor latency in response metadata

---

## 📝 Notes

- WebSocket connection stays open for continuous conversation
- Server maintains conversation history (last 10 messages)
- Audio responses are always included with text responses
- All processing happens locally on the server
- ngrok URL changes on server restart (get new URL from `/api/tunnels`)

---

## 🔗 Additional Resources

- **Server Logs:** `/tmp/harvey_server.log`
- **Configuration:** `/home/nic/Harveylocalaudio/backend/config.yaml`
- **API Key:** `/home/nic/Harveylocalaudio/backend/.api_key`
- **Web Interface:** https://be15f84a5e11.ngrok-free.app

---

**Last Updated:** 2026-01-03
**API Version:** 1.0.0
