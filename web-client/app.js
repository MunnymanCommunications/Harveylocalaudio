/**
 * Harvey Voice AI - Web Client
 * Low latency voice conversation interface
 */

// WebSocket connection
let ws = null;
let isConnected = false;

// Audio recording
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let audioContext = null;
let analyser = null;
let visualizerInterval = null;

// Stats
let messageCount = 0;
let latencies = [];

// Initialize visualizer
function initVisualizer() {
    const visualizer = document.getElementById('visualizer');
    for (let i = 0; i < 32; i++) {
        const bar = document.createElement('div');
        bar.className = 'visualizer-bar';
        bar.style.height = '10px';
        visualizer.appendChild(bar);
    }
}

// Update visualizer
function updateVisualizer(dataArray) {
    const bars = document.querySelectorAll('.visualizer-bar');
    bars.forEach((bar, i) => {
        const value = dataArray[i] || 0;
        const height = (value / 255) * 40 + 5;
        bar.style.height = `${height}px`;
    });
}

// Connect/Disconnect toggle
async function toggleConnection() {
    if (isConnected) {
        disconnect();
    } else {
        await connect();
    }
}

// Connect to WebSocket
async function connect() {
    const wsUrl = document.getElementById('wsUrl').value;
    const apiKey = document.getElementById('apiKey').value;

    if (!wsUrl) {
        alert('Please enter WebSocket URL');
        return;
    }

    if (!apiKey) {
        alert('Please enter API Key');
        return;
    }

    updateStatus('Connecting...', false);

    try {
        ws = new WebSocket(wsUrl, [], {
            headers: {
                'X-API-Key': apiKey
            }
        });

        // Note: Browser WebSocket API doesn't support custom headers directly
        // We'll send API key in first message instead
        let apiKeySent = false;

        ws.onopen = () => {
            console.log('WebSocket connected');
            isConnected = true;
            updateStatus('Connected', true);
            document.getElementById('connectBtn').classList.remove('btn-primary');
            document.getElementById('connectBtn').classList.add('btn-danger');
            document.getElementById('connectBtnText').textContent = 'Disconnect';
            document.getElementById('recordBtn').disabled = false;
            document.getElementById('testBtn').disabled = false;
            document.getElementById('recordStatus').textContent = 'Press and hold to speak';

            // Request microphone access
            requestMicrophoneAccess();
        };

        ws.onmessage = (event) => {
            console.log('Received message:', event.data);
            handleMessage(JSON.parse(event.data));
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('Connection Error', false);
            alert('Failed to connect to server. Make sure the server is running.');
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            disconnect();
        };

    } catch (error) {
        console.error('Connection error:', error);
        updateStatus('Connection Failed', false);
        alert('Failed to connect: ' + error.message);
    }
}

// Disconnect from WebSocket
function disconnect() {
    if (ws) {
        ws.close();
        ws = null;
    }

    isConnected = false;
    updateStatus('Disconnected', false);
    document.getElementById('connectBtn').classList.remove('btn-danger');
    document.getElementById('connectBtn').classList.add('btn-primary');
    document.getElementById('connectBtnText').textContent = 'Connect';
    document.getElementById('recordBtn').disabled = true;
    document.getElementById('testBtn').disabled = true;
    document.getElementById('recordStatus').textContent = 'Connect to server to start';

    // Stop recording if active
    if (isRecording) {
        stopRecording();
    }
}

// Update connection status
function updateStatus(text, connected) {
    document.getElementById('statusText').textContent = text;
    const dot = document.getElementById('statusDot');

    if (connected) {
        dot.classList.add('connected');
    } else {
        dot.classList.remove('connected');
    }
}

// Request microphone access
async function requestMicrophoneAccess() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('Microphone access granted');

        // Setup audio context for visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);

        // Setup media recorder
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            audioChunks = [];

            // Convert to base64 and send
            await sendAudio(audioBlob);
        };

    } catch (error) {
        console.error('Microphone access denied:', error);
        alert('Microphone access is required for voice input. Please allow microphone access.');
    }
}

// Toggle recording
function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// Start recording
function startRecording() {
    if (!mediaRecorder) {
        alert('Microphone not initialized. Please reconnect.');
        return;
    }

    audioChunks = [];
    mediaRecorder.start();
    isRecording = true;

    document.getElementById('recordBtn').classList.add('recording');
    document.getElementById('recordIcon').textContent = '⏹️';
    document.getElementById('recordStatus').textContent = 'Recording... (release to send)';

    // Start visualizer
    startVisualizer();
}

// Stop recording
function stopRecording() {
    if (!mediaRecorder || !isRecording) return;

    mediaRecorder.stop();
    isRecording = false;

    document.getElementById('recordBtn').classList.remove('recording');
    document.getElementById('recordIcon').textContent = '🎤';
    document.getElementById('recordStatus').textContent = 'Processing...';

    // Stop visualizer
    stopVisualizer();
}

// Start visualizer animation
function startVisualizer() {
    if (!analyser) return;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    visualizerInterval = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        updateVisualizer(dataArray);
    }, 50);
}

// Stop visualizer animation
function stopVisualizer() {
    if (visualizerInterval) {
        clearInterval(visualizerInterval);
        visualizerInterval = null;
    }

    // Reset bars
    const bars = document.querySelectorAll('.visualizer-bar');
    bars.forEach(bar => {
        bar.style.height = '10px';
    });
}

// Send audio to server
async function sendAudio(audioBlob) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('Not connected to server');
        document.getElementById('recordStatus').textContent = 'Press and hold to speak';
        return;
    }

    try {
        // Convert blob to base64
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];

            // Send to server
            const message = {
                type: 'audio',
                data: base64Audio,
                format: 'wav',
                sample_rate: 16000
            };

            console.log('Sending audio message...');
            ws.send(JSON.stringify(message));

            // Add to conversation log
            addMessage('user', '🎤 Voice message sent', null);
        };

        reader.readAsDataURL(audioBlob);

    } catch (error) {
        console.error('Error sending audio:', error);
        alert('Failed to send audio: ' + error.message);
        document.getElementById('recordStatus').textContent = 'Press and hold to speak';
    }
}

// Send test text message
function sendTestMessage() {
    const testInput = document.getElementById('testInput');
    const text = testInput.value.trim();

    if (!text) {
        alert('Please enter a message');
        return;
    }

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('Not connected to server');
        return;
    }

    const message = {
        type: 'text',
        text: text
    };

    console.log('Sending test message:', message);
    ws.send(JSON.stringify(message));

    // Add to conversation log
    addMessage('user', text, null);

    // Clear input
    testInput.value = '';
}

// Handle incoming messages
function handleMessage(data) {
    console.log('Handling message type:', data.type);

    switch (data.type) {
        case 'connected':
            console.log('Server connection confirmed:', data.connection_id);
            break;

        case 'audio_response':
            handleAudioResponse(data);
            break;

        case 'text_response':
            handleTextResponse(data);
            break;

        case 'error':
            console.error('Server error:', data.message);
            alert('Server error: ' + data.message);
            break;

        case 'pong':
            console.log('Pong received');
            break;

        default:
            console.warn('Unknown message type:', data.type);
    }
}

// Handle audio response
function handleAudioResponse(data) {
    console.log('Audio response received:', {
        transcription: data.transcription,
        text: data.text,
        latency: data.latency_ms
    });

    // Update stats
    updateStats(data.latency_ms);

    // Add to conversation log
    addMessage('assistant', data.text, data.latency_ms, data.transcription);

    // Play audio response
    if (data.audio) {
        playAudio(data.audio);
    }

    document.getElementById('recordStatus').textContent = 'Press and hold to speak';
}

// Handle text response
function handleTextResponse(data) {
    console.log('Text response received:', data.text);

    // Update stats
    updateStats(data.latency_ms);

    // Add to conversation log
    addMessage('assistant', data.text, data.latency_ms);

    // Play audio response
    if (data.audio) {
        playAudio(data.audio);
    }
}

// Play audio response
function playAudio(base64Audio) {
    try {
        const audioData = atob(base64Audio);
        const arrayBuffer = new ArrayBuffer(audioData.length);
        const view = new Uint8Array(arrayBuffer);

        for (let i = 0; i < audioData.length; i++) {
            view[i] = audioData.charCodeAt(i);
        }

        const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        audio.play().catch(error => {
            console.error('Error playing audio:', error);
        });

        audio.onended = () => {
            URL.revokeObjectURL(url);
        };

    } catch (error) {
        console.error('Error decoding audio:', error);
    }
}

// Add message to conversation log
function addMessage(role, text, latency, transcription) {
    const log = document.getElementById('conversationLog');

    // Remove "no messages" placeholder
    if (messageCount === 0) {
        log.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let content = `
        <div class="message-header">${role === 'user' ? '👤 You' : '🤖 Harvey'}</div>
    `;

    if (transcription && role === 'assistant') {
        content += `<div class="message-content"><strong>You said:</strong> ${escapeHtml(transcription)}</div>`;
    }

    content += `<div class="message-content">${escapeHtml(text)}</div>`;

    if (latency) {
        const latencyClass = latency < 500 ? 'fast' : latency < 1000 ? 'medium' : 'slow';
        content += `<div class="latency ${latencyClass}">⚡ ${latency}ms</div>`;
    }

    messageDiv.innerHTML = content;
    log.appendChild(messageDiv);

    // Scroll to bottom
    log.scrollTop = log.scrollHeight;

    messageCount++;
    document.getElementById('messageCount').textContent = messageCount;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update stats
function updateStats(latency) {
    if (latency) {
        latencies.push(latency);

        // Update last latency
        document.getElementById('lastLatency').textContent = latency;

        // Update average latency
        const avg = Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length);
        document.getElementById('avgLatency').textContent = avg;
    }
}

// Initialize on load
window.onload = () => {
    console.log('Harvey Voice AI initialized');
    initVisualizer();

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Space bar to toggle recording (when connected)
        if (e.code === 'Space' && isConnected && !e.target.matches('input')) {
            e.preventDefault();
            if (!isRecording) {
                startRecording();
            }
        }
    });

    document.addEventListener('keyup', (e) => {
        // Release space bar to stop recording
        if (e.code === 'Space' && isRecording) {
            e.preventDefault();
            stopRecording();
        }
    });
};
