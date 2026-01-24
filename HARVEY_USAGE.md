# Harvey AI - Usage Guide

## 🚀 Quick Start

### Option 1: Desktop Launcher (Recommended)

1. **Double-click** the "Harvey AI Assistant" icon on your desktop
2. Or search for "Harvey AI" in your applications menu
3. The browser will open automatically with Harvey
4. **Click the "Press to Activate Harvey" button**
5. Grant microphone permission when prompted
6. Start talking to Harvey!

### Option 2: Manual Start

```bash
cd /home/nic/Harveylocalaudio
./start_harvey.sh
```

Then open `web_client.html` in your browser.

## 🛑 Stopping Harvey

```bash
cd /home/nic/Harveylocalaudio
./stop_harvey.sh
```

## 🎤 How to Use Harvey

1. **Activate Harvey**: Click the big activation button when you first open the app
2. **Grant Microphone Access**: Allow microphone permission when your browser asks
3. **Start Conversing**:
   - Click and hold "Hold to Speak" to record your voice
   - Or type your message in the text box
4. **Adjust Settings**: Change voice and speech speed in the settings panel

## 🔧 System Information

- **Backend Server**: Running on `https://localhost:8765` (SSL enabled)
- **LLM Model**: nemotron-mini (via Ollama)
- **Speech Recognition**: Whisper base model (CPU)
- **Text-to-Speech**: Edge TTS (en-US-GuyNeural)
- **API Key**: Stored in `backend/.api_key`

## 📝 Server Logs

View real-time logs:
```bash
tail -f /tmp/harvey_server.log
```

## 🔐 Security

- SSL certificates located in `ssl/` directory
- WebSocket uses WSS (secure) protocol
- API key authentication enabled
- All processing happens locally on your computer

## 🐛 Troubleshooting

### Server won't start
```bash
cd /home/nic/Harveylocalaudio/backend
source venv/bin/activate
python main.py
```

### Check if Ollama is running
```bash
curl http://localhost:11434/api/tags
```

### Microphone not working
- Make sure you granted browser microphone permission
- Check browser settings for microphone access
- Try refreshing the page and clicking "Activate Harvey" again

## 📂 Project Structure

```
Harveylocalaudio/
├── backend/              # Backend server code
│   ├── main.py          # Main server
│   ├── config.yaml      # Configuration
│   └── venv/            # Python virtual environment
├── ssl/                 # SSL certificates
├── web_client.html      # Main web interface
├── start_harvey.sh      # Startup script
├── stop_harvey.sh       # Stop script
└── harvey_ai.desktop    # Desktop launcher
```

## 🎯 Features

✅ Local, private AI processing
✅ Low-latency voice conversations
✅ Secure WebSocket (WSS) connection
✅ One-click activation with Harvey button
✅ Microphone permission on demand
✅ Real-time speech recognition
✅ Natural voice synthesis
✅ Desktop application launcher
✅ Easy start/stop scripts

---

**Enjoy chatting with Harvey!** 🤖
