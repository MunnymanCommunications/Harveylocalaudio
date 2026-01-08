#!/usr/bin/env python3
"""Quick test of local Piper TTS"""

import asyncio
import sys
sys.path.insert(0, '/home/nic/Harveylocalaudio/backend')

from tts_engine_local import LocalPiperTTS

async def test_tts():
    """Test TTS synthesis"""
    config = {
        'voice': 'en_US-lessac-medium',
        'speed': 1.0,
        'device': 'cpu',
        'quality': 'high'
    }

    tts = LocalPiperTTS(config)
    await tts.initialize()

    print("Testing TTS synthesis...")
    text = "Hello! This is a test of the local Piper TTS system."

    audio_bytes = await tts.synthesize(text)

    print(f"✅ Generated {len(audio_bytes)} bytes of audio")

    if len(audio_bytes) > 1000:
        print("✅ Audio generation successful!")
        print(f"First 20 bytes: {audio_bytes[:20]}")
    else:
        print("❌ Audio too small, likely silence")

if __name__ == "__main__":
    asyncio.run(test_tts())
