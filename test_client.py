#!/usr/bin/env python3
"""
Simple test client for Harvey Local Audio
"""
import asyncio
import websockets
import json
import base64
import sys

API_KEY = "MB8w2x1hGPRBVhZdnRvqJuBxnADUQjFc7GsqXEnJJ8w"
WS_URL = "ws://localhost:8765/ws/audio"

async def test_text_message():
    """Test with a simple text message"""
    print("🔌 Connecting to Harvey Local Audio...")

    try:
        async with websockets.connect(
            WS_URL,
            extra_headers={"X-API-Key": API_KEY}
        ) as websocket:
            print("✅ Connected successfully!")

            # Receive initial connection handshake message
            handshake = await websocket.recv()
            handshake_data = json.loads(handshake)
            print(f"📡 Handshake: {handshake_data.get('message', 'Connected')}")

            # Send a text message (easier to test than audio)
            test_message = {
                "type": "text",
                "text": "Hello! Can you tell me a short joke?"
            }

            print(f"\n📤 Sending: {test_message['text']}")
            await websocket.send(json.dumps(test_message))

            print("⏳ Waiting for response...")
            response_data = await websocket.recv()
            print(f"📥 Raw response: {response_data[:200]}...")
            response = json.loads(response_data)

            print(f"\n✅ Response received!")
            print(f"📝 Text: {response.get('text', 'No text')}")
            print(f"⏱️  Latency: {response.get('latency_ms', 'N/A')} ms")

            # Save audio if present
            if 'audio' in response and response['audio']:
                audio_bytes = base64.b64decode(response['audio'])
                output_file = 'test_response.wav'
                with open(output_file, 'wb') as f:
                    f.write(audio_bytes)
                print(f"🔊 Audio saved to: {output_file}")
                print(f"   Audio size: {len(audio_bytes)} bytes")

            print("\n🎉 Test completed successfully!")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e}")
        print("   Make sure the server is running on port 8765")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Harvey Local Audio - Test Client")
    print("=" * 60)
    asyncio.run(test_text_message())
