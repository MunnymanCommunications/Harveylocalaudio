#!/usr/bin/env python3
"""Test Harvey performance - measure TTFT and streaming"""

import asyncio
import time
import sys
sys.path.insert(0, '/home/nic/Harveylocalaudio/backend')

from llm_client import OllamaClient
from config_manager import ConfigManager

async def test_streaming_performance():
    """Test streaming performance"""

    # Load config
    config_manager = ConfigManager('/home/nic/Harveylocalaudio/backend/config.yaml')
    config = config_manager.load_config()

    # Initialize LLM client
    llm = OllamaClient(config['llm'])
    await llm.initialize()

    # Test messages
    messages = [
        {"role": "system", "content": "You are Harvey, a helpful AI assistant. Provide clear, concise responses."},
        {"role": "user", "content": "What time is it?"}
    ]

    print("Testing LLM streaming performance...")
    print("=" * 60)

    # Test streaming
    start_time = time.time()
    first_token_time = None
    chunks_received = 0
    total_chars = 0

    try:
        async for chunk in llm.generate_stream(messages):
            if first_token_time is None:
                first_token_time = time.time() - start_time
                print(f"⚡ TIME TO FIRST TOKEN: {int(first_token_time * 1000)}ms")

            chunks_received += 1
            total_chars += len(chunk)
            print(f"Chunk {chunks_received}: '{chunk}'", end='', flush=True)

        total_time = time.time() - start_time

        print("\n")
        print("=" * 60)
        print(f"📊 Performance Metrics:")
        print(f"   - Time to First Token: {int(first_token_time * 1000)}ms")
        print(f"   - Total Time: {int(total_time * 1000)}ms")
        print(f"   - Chunks Received: {chunks_received}")
        print(f"   - Total Characters: {total_chars}")
        print(f"   - Tokens per Second: {total_chars / total_time:.1f} chars/sec")
        print("=" * 60)

        # Evaluate performance
        if first_token_time < 0.3:
            print("✅ EXCELLENT - TTFT < 300ms")
        elif first_token_time < 0.5:
            print("✅ GOOD - TTFT < 500ms")
        elif first_token_time < 1.0:
            print("⚠️  ACCEPTABLE - TTFT < 1000ms")
        else:
            print("❌ SLOW - TTFT > 1000ms - Optimization needed")

    except Exception as e:
        print(f"Error during streaming: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_performance())
