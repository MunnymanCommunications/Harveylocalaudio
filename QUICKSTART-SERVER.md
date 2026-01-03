# Quick Start - Run on Your Server

Get Harvey Voice AI running on your local server with Nemotron 3 Nano 30B for low-latency conversations!

## ⚡ Fast Setup (5 minutes)

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &
```

### 2. Pull Nemotron Model

```bash
# This will take ~20 minutes (30B model is ~17GB)
ollama pull nemotron-3-nano:30b
```

**While it's downloading, continue with step 3...**

### 3. Set Up Python Environment

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Desktop App (optional)
cd ../desktop-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
```

### 4. Start the Server

```bash
# Option A: Command line
./run-server.sh

# Option B: Desktop GUI
./run-desktop-app.sh
```

**Server will start on:** `http://0.0.0.0:8765`

### 5. Launch Web Client

**In a new terminal:**

```bash
./run-web-client.sh
```

**Opens at:** `http://localhost:8080`

### 6. Connect & Test

1. Copy API key from terminal or desktop app
2. Paste into web client
3. Click **Connect**
4. Allow microphone access
5. **Hold spacebar or click mic button** - Start talking!

## 🎯 Expected Performance

With Nemotron 3 Nano 30B:

- **Total Latency**: ~400-800ms (depending on hardware)
  - STT (Whisper): ~200-300ms
  - LLM (Nemotron): ~100-300ms
  - TTS (Coqui): ~100-200ms

**Hardware recommendations:**
- **GPU**: NVIDIA with 24GB+ VRAM (for 30B model)
- **RAM**: 32GB+ recommended
- **CPU**: 8+ cores if using CPU mode

## 🚀 Performance Optimization

### For Lowest Latency (<500ms)

Edit `backend/config.yaml`:

```yaml
stt:
  model: "medium"  # Faster than large-v3
  device: "cuda"   # GPU acceleration

llm:
  model: "nemotron-3-nano:30b"
  max_tokens: 1024  # Reduce from 2048

tts:
  device: "cuda"  # GPU acceleration
  speed: 1.1      # Slightly faster speech
```

### If You Have Less VRAM

Use a smaller model:

```bash
# 9B model (needs ~6GB VRAM)
ollama pull gemma2:9b

# Update config.yaml
llm:
  model: "gemma2:9b"
```

## 🌐 Access from Other Devices

### On Same Network (LAN)

1. Get server IP:
   ```bash
   hostname -I | awk '{print $1}'
   ```

2. Open web client from any device:
   ```
   http://YOUR_SERVER_IP:8080
   ```

3. WebSocket URL in client:
   ```
   ws://YOUR_SERVER_IP:8765/ws/audio
   ```

### Remote Access (Internet)

1. Set up port forwarding on router:
   - Port 8765 (WebSocket)
   - Port 8080 (Web client)

2. Use your public IP or domain:
   ```
   http://your-domain.com:8080
   ws://your-domain.com:8765/ws/audio
   ```

**⚠️ Security Note:** Use HTTPS/WSS in production! Add authentication!

## 🧪 Testing & Validation

### 1. Test Server Health

```bash
curl http://localhost:8765/health
```

Should return:
```json
{
  "status": "healthy",
  "audio_pipeline": true,
  "llm_model": "nemotron-3-nano:30b"
}
```

### 2. Test Text-Only (No Audio)

In web client:
1. Connect to server
2. Use "Test Mode" input
3. Type: "Hello, tell me a joke"
4. Press Enter

Should get response in <1 second.

### 3. Test Voice

1. Click microphone button
2. Say: "Hello Harvey, can you hear me?"
3. Release button
4. Wait for response

Check latency in web interface - should show <1000ms.

## 📊 Monitor Performance

### Check Logs

```bash
tail -f backend/logs/server.log
```

### Monitor GPU Usage

```bash
# Install nvidia-smi if needed
watch -n 1 nvidia-smi
```

### Check Ollama Models

```bash
ollama list
```

## 🔧 Troubleshooting

### "Model not found: nemotron-3-nano:30b"

```bash
# Check if download completed
ollama list

# If not there, pull again
ollama pull nemotron-3-nano:30b
```

### "CUDA out of memory"

The 30B model needs lots of VRAM. Options:

1. **Use smaller model:**
   ```bash
   ollama pull gemma2:9b
   # Update config.yaml: model: "gemma2:9b"
   ```

2. **Use CPU mode:**
   ```yaml
   # config.yaml
   llm:
     device: "cpu"  # Slower but works
   ```

3. **Reduce context:**
   ```yaml
   llm:
     max_tokens: 512
   ```

### High Latency (>2000ms)

1. **Check GPU usage:** `nvidia-smi`
2. **Use smaller Whisper:** Set `stt.model: "medium"`
3. **Reduce max_tokens:** Set `llm.max_tokens: 512`
4. **Check network:** Test on same machine first

### Microphone Not Working

1. Browser needs HTTPS for remote access
2. Grant permissions in browser
3. Check browser console for errors

## 🎙️ Voice Cloning (Optional)

Add your own voice:

1. Record 3-10 seconds of clear speech as WAV
2. Save to `backend/voice_samples/my_voice.wav`
3. Update config:
   ```yaml
   tts:
     voice: "my_voice"
   ```

## 📈 Scaling Tips

### Multiple Users

For multiple concurrent users:

1. Increase worker threads
2. Use Redis for session management
3. Load balance across multiple servers
4. Consider GPU queue management

### Production Deployment

- Use NGINX reverse proxy
- Add HTTPS/WSS
- Implement rate limiting
- Add user authentication
- Monitor with Prometheus/Grafana

## 🎯 Next Steps

1. ✅ **Test basic conversation** - Make sure it works
2. 🔧 **Tune latency** - Optimize for your hardware
3. 🎨 **Customize voice** - Try different TTS voices
4. 🌍 **Try languages** - Test multilingual support
5. 📱 **Build app** - Integrate WebSocket into your app

## 💡 Pro Tips

- **Spacebar shortcut**: Hold spacebar to record (faster than clicking)
- **Test mode first**: Validate LLM responses without audio
- **Monitor logs**: Keep an eye on `backend/logs/server.log`
- **GPU utilization**: Aim for 60-80% GPU usage for best balance
- **Batch testing**: Use test mode to validate model quality first

## 🆘 Still Having Issues?

1. Check `backend/logs/server.log` for errors
2. Verify all services running: `ps aux | grep -E "ollama|python"`
3. Test each component separately (STT, LLM, TTS)
4. Join our community for support

---

**Ready to go?** Just run:

```bash
# Terminal 1: Start server
./run-server.sh

# Terminal 2: Launch web client
./run-web-client.sh

# Then open browser and start talking! 🎤
```

Enjoy your low-latency AI conversations! ⚡
