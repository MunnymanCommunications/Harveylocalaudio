/**
 * Harvey Local Audio - JavaScript Client Example
 *
 * This example shows how to connect to Harvey Local Audio server
 * and send/receive audio data via WebSocket
 */

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// Configuration
const WS_URL = 'ws://localhost:8765/ws/audio';
const API_KEY = 'your-api-key-here';  // Replace with your API key

class HarveyAudioClient {
    constructor(wsUrl, apiKey) {
        this.wsUrl = wsUrl;
        this.apiKey = apiKey;
        this.ws = null;
    }

    connect() {
        return new Promise((resolve, reject) => {
            console.log('Connecting to Harvey Audio Server...');

            this.ws = new WebSocket(this.wsUrl, {
                headers: {
                    'X-API-Key': this.apiKey
                }
            });

            this.ws.on('open', () => {
                console.log('Connected to server');
                resolve();
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });

            this.ws.on('close', () => {
                console.log('Disconnected from server');
            });

            this.ws.on('message', (data) => {
                this.handleMessage(data);
            });
        });
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);

            switch (message.type) {
                case 'connected':
                    console.log('Server connection established');
                    console.log('Connection ID:', message.connection_id);
                    break;

                case 'audio_response':
                    console.log('\n--- Response Received ---');
                    console.log('Transcription:', message.transcription);
                    console.log('Response:', message.text);
                    console.log('Latency:', message.latency_ms, 'ms');

                    // Save audio response
                    if (message.audio) {
                        this.saveAudioResponse(message.audio);
                    }
                    break;

                case 'text_response':
                    console.log('\n--- Text Response ---');
                    console.log('Response:', message.text);
                    console.log('Latency:', message.latency_ms, 'ms');
                    break;

                case 'error':
                    console.error('Server error:', message.message);
                    break;

                case 'pong':
                    console.log('Pong received');
                    break;

                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    sendAudioFile(audioPath) {
        console.log(`\nSending audio file: ${audioPath}`);

        // Read audio file
        const audioBuffer = fs.readFileSync(audioPath);
        const audioBase64 = audioBuffer.toString('base64');

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'audio',
            data: audioBase64,
            format: 'wav',
            sample_rate: 16000
        }));
    }

    sendText(text) {
        console.log(`\nSending text: ${text}`);

        this.ws.send(JSON.stringify({
            type: 'text',
            text: text
        }));
    }

    saveAudioResponse(audioBase64, outputPath = 'response.wav') {
        const audioBuffer = Buffer.from(audioBase64, 'base64');
        fs.writeFileSync(outputPath, audioBuffer);
        console.log(`Audio response saved to: ${outputPath}`);
    }

    updateConfig(settings) {
        console.log('Updating configuration:', settings);

        this.ws.send(JSON.stringify({
            type: 'configure',
            settings: settings
        }));
    }

    ping() {
        this.ws.send(JSON.stringify({ type: 'ping' }));
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Example usage
async function main() {
    const client = new HarveyAudioClient(WS_URL, API_KEY);

    try {
        // Connect to server
        await client.connect();

        // Example 1: Send text message
        client.sendText("Hello, how are you today?");

        // Wait a bit for response
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Example 2: Send audio file (if you have one)
        // client.sendAudioFile('test-audio.wav');

        // Example 3: Update voice configuration
        // client.updateConfig({
        //     voice: 'en_US-amy-medium',
        //     speed: 1.2
        // });

        // Keep connection alive for a while
        setTimeout(() => {
            console.log('\nClosing connection...');
            client.disconnect();
        }, 10000);

    } catch (error) {
        console.error('Error:', error);
    }
}

// Run if executed directly
if (require.main === module) {
    main();
}

module.exports = HarveyAudioClient;
