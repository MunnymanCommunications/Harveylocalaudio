# Harvey Voice AI - Web Client

Beautiful web interface for testing low-latency voice conversations with Harvey AI.

## Features

- 🎙️ **Voice Recording**: Push-to-talk or click-to-record
- 🔊 **Audio Playback**: Hear AI responses in real-time
- 📊 **Live Stats**: Track latency and performance
- 💬 **Conversation History**: See full conversation log
- 🧪 **Test Mode**: Send text messages without audio
- 📈 **Audio Visualizer**: See real-time audio levels
- ⌨️ **Keyboard Shortcuts**: Spacebar to record

## Quick Start

### 1. Start the Backend Server

```bash
# From the root directory
cd backend
source venv/bin/activate
python main.py
```

Or use the desktop app:
```bash
./run-desktop-app.sh
```

### 2. Get Your API Key

The API key is displayed in the desktop app or found in `backend/.api_key`

### 3. Open the Web Client

**Option A: Open directly in browser**
```bash
cd web-client
open index.html  # Mac
xdg-open index.html  # Linux
start index.html  # Windows
```

**Option B: Serve with Python**
```bash
cd web-client
python3 -m http.server 8080
# Then open: http://localhost:8080
```

**Option C: Serve with Node.js**
```bash
cd web-client
npx http-server -p 8080
# Then open: http://localhost:8080
```

### 4. Connect

1. Enter WebSocket URL: `ws://localhost:8765/ws/audio`
2. Enter your API key
3. Click **Connect**
4. Allow microphone access when prompted
5. Start talking!

## Usage

### Voice Recording

**Method 1: Push-to-Talk**
- Hold spacebar to record
- Release to send

**Method 2: Click to Record**
- Click the microphone button to start
- Click again (stop icon) to send

### Test Mode

Type a message and press Enter or click "Send Test Message" to test without audio.

### Keyboard Shortcuts

- **Spacebar**: Hold to record, release to send
- **Enter** (in test input): Send test message

## WebSocket Configuration

### Default Settings
- **URL**: `ws://localhost:8765/ws/audio`
- **Port**: 8765
- **Protocol**: WebSocket

### For Remote Server

If running on a remote server, update the URL:
```
ws://your-server-ip:8765/ws/audio
```

Make sure to:
1. Update `backend/config.yaml` with `host: "0.0.0.0"`
2. Open firewall port 8765
3. Use your server's IP address

## Performance Tips

### Low Latency Settings

For best performance (< 500ms latency):

1. **Use GPU acceleration**:
   ```yaml
   # backend/config.yaml
   stt:
     device: "cuda"
   tts:
     device: "cuda"
   ```

2. **Use smaller models**:
   ```yaml
   stt:
     model: "medium"  # or "small" for even faster
   ```

3. **Local server**: Run on same machine or LAN for lowest latency

### Expected Latencies

- **Excellent**: < 500ms (🟢 Green)
- **Good**: 500-1000ms (🟡 Yellow)
- **Acceptable**: 1000-2000ms (🔴 Red)

## Troubleshooting

### "WebSocket connection failed"

1. Check server is running: `curl http://localhost:8765/health`
2. Verify WebSocket URL is correct
3. Check API key is correct

### "Microphone access denied"

1. Grant microphone permission in browser
2. Check browser settings for microphone access
3. Try HTTPS if on remote server (required for mic access)

### No audio playback

1. Check browser console for errors
2. Verify audio codec support
3. Try different browser (Chrome/Firefox recommended)

### High latency

1. Enable GPU acceleration in config
2. Use smaller Whisper model (medium or small)
3. Check network connection
4. Monitor server resource usage

## Browser Compatibility

✅ **Recommended:**
- Chrome 90+
- Firefox 88+
- Edge 90+

⚠️ **Limited support:**
- Safari (may require HTTPS for mic access)

## Architecture

```
┌─────────────┐      WebSocket      ┌─────────────┐
│             │ ←─────────────────→ │             │
│  Web Client │     Audio Base64    │   Backend   │
│             │                      │   Server    │
└─────────────┘                      └─────────────┘
      │                                     │
      │ Microphone                          │
      │ Speakers                   ┌────────┼────────┐
      ▼                            │        │        │
   Browser                      Whisper  Ollama  Coqui
                                (STT)    (LLM)   (TTS)
```

## Security Notes

- API keys are required for authentication
- Use HTTPS in production
- Don't share API keys publicly
- API key is sent in WebSocket headers

## Advanced Features

### Custom Voice Samples

Add your own voice for cloning:

1. Record 3-10 seconds of clear speech
2. Save as WAV file
3. Add to config:
   ```yaml
   tts:
     voice: "custom"
   ```
4. Upload via API or desktop app

### Multi-language Support

Change TTS language in real-time:
```javascript
ws.send(JSON.stringify({
    type: 'configure',
    settings: {
        language: 'es'  // Spanish
    }
}));
```

Supported: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja

## Development

### File Structure
```
web-client/
├── index.html    # Main HTML interface
├── app.js        # WebSocket & audio handling
└── README.md     # This file
```

### Customization

- Modify colors in `index.html` CSS
- Adjust visualizer bars (line 18 in app.js)
- Change audio settings (sample rate, etc.)

## Support

For issues or questions:
- Check server logs: `backend/logs/server.log`
- Check browser console for errors
- Verify WebSocket connection in Network tab

Enjoy your low-latency AI conversations! 🎙️✨
