#!/usr/bin/env python3
"""
Harvey AI WebSocket API - Test Connection Script
Quick test to verify your AI application can connect to Harvey
"""

import asyncio
import websockets
import json
import base64
import sys

# ==================== CONFIGURATION ====================
API_KEY = "MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w"

# Choose your endpoint:
# Option 1: Local network (faster, requires same network)
LOCAL_URL = f"wss://192.168.4.108:8765/ws/audio?api_key={API_KEY}"

# Option 2: Public ngrok (works from anywhere)
NGROK_URL = f"wss://140fc1914a4c.ngrok-free.app/ws/audio?api_key={API_KEY}"

# Select which URL to use
WS_URL = NGROK_URL  # Change to LOCAL_URL if testing locally

# =======================================================


async def test_connection():
    """Test basic WebSocket connection"""
    print("🔗 Testing connection to Harvey AI...")
    print(f"📍 Endpoint: {WS_URL}\n")

    try:
        async with websockets.connect(WS_URL, ssl=True) as websocket:
            # 1. Wait for connection message
            print("⏳ Waiting for connection message...")
            response = await websocket.recv()
            data = json.loads(response)

            if data['type'] == 'connected':
                print("✅ Connected successfully!")
                print(f"   Connection ID: {data.get('connection_id', 'N/A')}")
                print(f"   Config: {json.dumps(data.get('config', {}), indent=2)}\n")

            # 2. Send a text message
            test_message = "Hello Harvey! This is a test connection. Please introduce yourself briefly."
            print(f"💬 Sending text message: '{test_message}'")

            await websocket.send(json.dumps({
                "type": "text",
                "text": test_message
            }))

            # 3. Wait for response
            print("⏳ Waiting for response...\n")
            response = await websocket.recv()
            data = json.loads(response)

            if data['type'] == 'text_response':
                print("✅ Response received!")
                print(f"   Harvey's response: {data['text']}")
                print(f"   Latency: {data.get('latency_ms', 'N/A')} ms")

                # Save audio if present
                if 'audio' in data and data['audio']:
                    audio_bytes = base64.b64decode(data['audio'])
                    filename = 'harvey_test_response.wav'
                    with open(filename, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   Audio saved to: {filename}")

                print("\n✨ Connection test successful!")
                return True

            elif data['type'] == 'error':
                print(f"❌ Error from server: {data['message']}")
                return False

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print("   Check that the server is running and the URL is correct")
        return False

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


async def test_conversation():
    """Test a multi-turn conversation"""
    print("\n" + "="*60)
    print("🗣️  Testing Multi-Turn Conversation")
    print("="*60 + "\n")

    messages = [
        "What's the weather like today?",
        "Tell me a joke",
        "What's 2+2?"
    ]

    try:
        async with websockets.connect(WS_URL, ssl=True) as websocket:
            # Wait for connection
            await websocket.recv()

            for i, msg in enumerate(messages, 1):
                print(f"Turn {i}: You: {msg}")

                await websocket.send(json.dumps({
                    "type": "text",
                    "text": msg
                }))

                response = await websocket.recv()
                data = json.loads(response)

                if data['type'] == 'text_response':
                    print(f"Turn {i}: Harvey: {data['text'][:100]}...")
                    print(f"        Latency: {data.get('latency_ms', 'N/A')} ms\n")

                await asyncio.sleep(0.5)  # Small delay between messages

            print("✅ Multi-turn conversation successful!\n")
            return True

    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False


async def check_server_health():
    """Check server health endpoint"""
    import aiohttp

    # Extract base URL from WebSocket URL
    if 'ngrok' in WS_URL:
        health_url = "https://140fc1914a4c.ngrok-free.app/health"
    else:
        health_url = "https://192.168.4.108:8765/health"

    print("\n🏥 Checking server health...")
    print(f"📍 Health endpoint: {health_url}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Server is healthy!")
                    print(f"   Status: {data.get('status', 'unknown')}")
                    print(f"   STT Ready: {data.get('stt_ready', False)}")
                    print(f"   LLM Ready: {data.get('llm_ready', False)}")
                    print(f"   TTS Ready: {data.get('tts_ready', False)}")
                    print(f"   LLM Model: {data.get('llm_model', 'unknown')}")
                    print(f"   Active Connections: {data.get('active_connections', 0)}\n")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("   The server may not be running\n")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🤖 HARVEY AI WEBSOCKET API - CONNECTION TEST")
    print("="*60 + "\n")

    # Test 1: Health check
    health_ok = await check_server_health()

    if not health_ok:
        print("⚠️  Server health check failed. Tests may not work.")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            return

    # Test 2: Basic connection
    connection_ok = await test_connection()

    if not connection_ok:
        print("\n❌ Basic connection test failed. Stopping here.")
        return

    # Test 3: Multi-turn conversation
    if input("\nRun multi-turn conversation test? (y/n): ").lower() == 'y':
        await test_conversation()

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)
    print("\n📚 See HARVEY_API_DOCS.md for full API documentation")
    print("🔗 Your WebSocket URL: " + WS_URL)
    print("🔑 Your API Key: " + API_KEY)
    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
