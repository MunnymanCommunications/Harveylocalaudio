#!/usr/bin/env python3
"""
Harvey Local Audio - Python Client Example

This example shows how to connect to Harvey Local Audio server
and send/receive audio data via WebSocket
"""

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Optional

import websockets

# Configuration
WS_URL = "ws://localhost:8765/ws/audio"
API_KEY = "your-api-key-here"  # Replace with your API key

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HarveyAudioClient:
    """Harvey Audio WebSocket Client"""

    def __init__(self, ws_url: str, api_key: str):
        self.ws_url = ws_url
        self.api_key = api_key
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        """Connect to server"""
        logger.info("Connecting to Harvey Audio Server...")

        headers = {"X-API-Key": self.api_key}

        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers
            )

            logger.info("Connected to server")

            # Start message handler
            asyncio.create_task(self._message_handler())

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    async def _message_handler(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")

        except Exception as e:
            logger.error(f"Message handler error: {e}")

    async def _handle_message(self, data: dict):
        """Handle specific message types"""
        msg_type = data.get('type')

        if msg_type == 'connected':
            logger.info("Server connection established")
            logger.info(f"Connection ID: {data.get('connection_id')}")

        elif msg_type == 'audio_response':
            logger.info("\n--- Response Received ---")
            logger.info(f"Transcription: {data.get('transcription')}")
            logger.info(f"Response: {data.get('text')}")
            logger.info(f"Latency: {data.get('latency_ms')} ms")

            # Save audio response
            if data.get('audio'):
                await self.save_audio_response(data['audio'])

        elif msg_type == 'text_response':
            logger.info("\n--- Text Response ---")
            logger.info(f"Response: {data.get('text')}")
            logger.info(f"Latency: {data.get('latency_ms')} ms")

        elif msg_type == 'error':
            logger.error(f"Server error: {data.get('message')}")

        elif msg_type == 'pong':
            logger.info("Pong received")

        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def send_audio_file(self, audio_path: str):
        """Send audio file to server"""
        logger.info(f"\nSending audio file: {audio_path}")

        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        # Encode to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Send to server
        await self.websocket.send(json.dumps({
            'type': 'audio',
            'data': audio_base64,
            'format': 'wav',
            'sample_rate': 16000
        }))

    async def send_text(self, text: str):
        """Send text message to server"""
        logger.info(f"\nSending text: {text}")

        await self.websocket.send(json.dumps({
            'type': 'text',
            'text': text
        }))

    async def save_audio_response(self, audio_base64: str, output_path: str = 'response.wav'):
        """Save audio response to file"""
        audio_data = base64.b64decode(audio_base64)

        with open(output_path, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Audio response saved to: {output_path}")

    async def update_config(self, settings: dict):
        """Update server configuration"""
        logger.info(f"Updating configuration: {settings}")

        await self.websocket.send(json.dumps({
            'type': 'configure',
            'settings': settings
        }))

    async def ping(self):
        """Send ping to server"""
        await self.websocket.send(json.dumps({'type': 'ping'}))

    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")


async def main():
    """Example usage"""
    client = HarveyAudioClient(WS_URL, API_KEY)

    try:
        # Connect to server
        await client.connect()

        # Wait for connection to establish
        await asyncio.sleep(1)

        # Example 1: Send text message
        await client.send_text("Hello, how are you today?")

        # Wait for response
        await asyncio.sleep(5)

        # Example 2: Send audio file (if you have one)
        # await client.send_audio_file('test-audio.wav')

        # Example 3: Update voice configuration
        # await client.update_config({
        #     'voice': 'en_US-amy-medium',
        #     'speed': 1.2
        # })

        # Example 4: Ping server
        # await client.ping()

        # Keep connection alive for a while
        await asyncio.sleep(10)

        # Disconnect
        await client.disconnect()

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
