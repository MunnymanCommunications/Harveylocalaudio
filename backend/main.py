"""
Harvey Local Audio Server
Main FastAPI application with WebSocket support for audio-to-audio conversations
"""

import asyncio
import base64
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Dict, Optional

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from audio_pipeline import AudioPipeline
from config_manager import ConfigManager
from streaming_manager import ConversationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Harvey Local Audio Server",
    description="Self-hosted audio-to-audio conversation system with WebSocket support",
    version="1.0.0"
)

# Configuration
config_manager = ConfigManager()
config = config_manager.load_config()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['server']['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio pipeline
audio_pipeline: Optional[AudioPipeline] = None

# Active connections
active_connections: Dict[str, WebSocket] = {}


def verify_api_key(x_api_key: str = Header(...)) -> bool:
    """Verify API key from request header"""
    expected_key = config['server']['api_key']
    if not expected_key:
        logger.warning("API key not configured - allowing all requests")
        return True

    if x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@app.on_event("startup")
async def startup_event():
    """Initialize audio pipeline on startup"""
    global audio_pipeline

    logger.info("Starting Harvey Local Audio Server...")

    # Generate API key if not set
    if not config['server']['api_key']:
        api_key = secrets.token_urlsafe(32)
        config['server']['api_key'] = api_key
        config_manager.save_api_key(api_key)
        logger.info(f"Generated new API key: {api_key}")

    # Initialize audio pipeline
    try:
        audio_pipeline = AudioPipeline(config)
        await audio_pipeline.initialize()
        logger.info("Audio pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize audio pipeline: {e}")
        raise

    logger.info(f"Server running on ws://{config['server']['host']}:{config['server']['port']}")
    logger.info(f"API Key: {config['server']['api_key']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global audio_pipeline

    logger.info("Shutting down server...")

    if audio_pipeline:
        await audio_pipeline.cleanup()

    # Close all active connections
    for conn_id, websocket in active_connections.items():
        await websocket.close()

    logger.info("Server shutdown complete")


@app.get("/")
async def root():
    """Serve the Harvey web interface"""
    html_path = Path(__file__).parent.parent / "harvey_io.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {
        "name": "Harvey Local Audio Server",
        "version": "1.0.0",
        "status": "running",
        "websocket_url": f"ws://{config['server']['host']}:{config['server']['port']}/ws/audio",
        "llm_model": config['llm']['model']
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "audio_pipeline": audio_pipeline is not None,
        "active_connections": len(active_connections)
    }

    if audio_pipeline:
        health_status.update(await audio_pipeline.get_status())

    return health_status


@app.get("/config")
async def get_config(authenticated: bool = Depends(verify_api_key)):
    """Get current configuration (excluding sensitive data)"""
    safe_config = config.copy()
    safe_config['server']['api_key'] = "***hidden***"
    return safe_config


@app.post("/config/voice")
async def update_voice_config(voice_config: dict, authenticated: bool = Depends(verify_api_key)):
    """Update voice configuration"""
    try:
        if audio_pipeline:
            await audio_pipeline.update_tts_config(voice_config)

        # Update config file
        for key, value in voice_config.items():
            if key in config['tts']:
                config['tts'][key] = value

        config_manager.save_config(config)

        return {"status": "success", "config": voice_config}
    except Exception as e:
        logger.error(f"Failed to update voice config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket, api_key: str = None):
    """WebSocket endpoint for audio streaming"""
    conn_id = secrets.token_urlsafe(16)

    # Verify API key (from query parameter or skip if not configured)
    expected_key = config['server']['api_key']
    if expected_key and api_key != expected_key:
        await websocket.close(code=1008, reason="Invalid API key")
        logger.warning(f"WebSocket connection rejected: Invalid API key")
        return

    # Accept connection
    await websocket.accept()
    active_connections[conn_id] = websocket

    # Create conversation manager for streaming mode
    conversation_manager = None
    streaming_mode = False

    logger.info(f"New WebSocket connection: {conn_id}")

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "connection_id": conn_id,
            "message": "Connected to Harvey Local Audio Server",
            "config": {
                "sample_rate": config['audio']['sample_rate'],
                "channels": config['audio']['channels'],
                "format": config['audio']['format']
            }
        })

        # Message loop
        while True:
            try:
                # Receive message - check what type it is first
                raw_message = await websocket.receive()

                # Handle text messages (JSON)
                if raw_message['type'] == 'websocket.receive' and 'text' in raw_message:
                    message = raw_message['text']
                    data = json.loads(message)
                    message_type = data.get('type')

                # Handle binary messages (audio chunks)
                elif raw_message['type'] == 'websocket.receive' and 'bytes' in raw_message:
                    if streaming_mode and conversation_manager:
                        audio_bytes = raw_message['bytes']
                        await conversation_manager.handle_audio_chunk(audio_bytes)
                        continue
                    else:
                        logger.warning("Binary data received but not in streaming mode, ignoring")
                        continue

                # Handle disconnect
                elif raw_message['type'] == 'websocket.disconnect':
                    logger.info("Client disconnected")
                    break

                else:
                    continue

                if message_type == 'start_streaming':
                    # Enter continuous streaming mode
                    streaming_mode = True
                    conversation_manager = ConversationManager(websocket, audio_pipeline)
                    logger.info(f"Connection {conn_id} entered streaming mode")
                    await websocket.send_json({
                        "type": "streaming_started",
                        "message": "Continuous streaming mode activated"
                    })

                elif message_type == 'stop_streaming':
                    # Exit streaming mode
                    streaming_mode = False
                    if conversation_manager:
                        conversation_manager.streaming_manager.reset()
                    logger.info(f"Connection {conn_id} exited streaming mode")
                    await websocket.send_json({
                        "type": "streaming_stopped",
                        "message": "Streaming mode deactivated"
                    })

                elif message_type == 'audio_chunk':
                    # Handle audio chunk in streaming mode
                    if streaming_mode and conversation_manager:
                        audio_data = base64.b64decode(data['data'])
                        await conversation_manager.handle_audio_chunk(audio_data)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not in streaming mode. Send 'start_streaming' first."
                        })

                elif message_type == 'audio':
                    # Process audio input (legacy single-shot mode)
                    await handle_audio_message(websocket, data)

                elif message_type == 'text':
                    # Process text input (for testing)
                    await handle_text_message(websocket, data)

                elif message_type == 'configure':
                    # Update configuration
                    await handle_config_message(websocket, data)

                elif message_type == 'ping':
                    # Ping/pong for connection keep-alive
                    await websocket.send_json({"type": "pong"})

                elif message_type == 'interrupt':
                    # User wants to interrupt Harvey
                    if streaming_mode and conversation_manager:
                        await conversation_manager.interrupt_harvey()

                elif message_type == 'get_state':
                    # Get current conversation state
                    if streaming_mode and conversation_manager:
                        state = conversation_manager.get_state()
                        await websocket.send_json({
                            "type": "state",
                            "state": state
                        })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })

            except WebSocketDisconnect:
                # Connection closed by client, exit loop
                logger.info("Client disconnected normally")
                break

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    # Connection already closed, can't send error
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conn_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        # Cleanup
        if conn_id in active_connections:
            del active_connections[conn_id]
        logger.info(f"Connection closed: {conn_id}")


async def handle_audio_message(websocket: WebSocket, data: dict):
    """Handle incoming audio message with compression support"""
    start_time = time.time()

    try:
        # Decode audio data
        audio_data = base64.b64decode(data['data'])

        # Get context if provided (datetime, etc.)
        context = data.get('context', {})
        current_datetime = context.get('current_datetime', '')

        # Process through pipeline
        result = await audio_pipeline.process_audio(
            audio_data=audio_data,
            sample_rate=data.get('sample_rate', config['audio']['sample_rate']),
            format=data.get('format', config['audio']['format']),
            context=context
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Check if client supports compression
        supports_compression = data.get('supports_compression', True)

        if supports_compression:
            # Use compressed transmission
            await send_compressed_audio_response(websocket, result, latency_ms)
        else:
            # Fallback to uncompressed (legacy)
            audio_b64 = base64.b64encode(result['audio_output']).decode('utf-8')
            logger.info(f"Sending uncompressed audio: {len(result['audio_output'])} bytes WAV, {len(audio_b64)} chars base64")

            await websocket.send_json({
                "type": "audio_response",
                "transcription": result['transcription'],
                "text": result['response_text'],
                "audio": audio_b64,
                "latency_ms": latency_ms,
                "metadata": {
                    "stt_time_ms": result.get('stt_time_ms', 0),
                    "llm_time_ms": result.get('llm_time_ms', 0),
                    "tts_time_ms": result.get('tts_time_ms', 0)
                }
            })

        logger.info(f"Processed audio in {latency_ms}ms")

    except Exception as e:
        logger.error(f"Error handling audio message: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"Audio processing failed: {str(e)}"
        })


async def send_compressed_audio_response(websocket: WebSocket, result: dict, latency_ms: int):
    """Send audio response with zlib compression"""
    import zlib

    try:
        # Compress audio data
        compressed = zlib.compress(result['audio_output'], level=6)
        audio_b64 = base64.b64encode(compressed).decode('utf-8')

        compression_ratio = len(compressed) / len(result['audio_output'])
        logger.info(f"Compressed audio: {len(result['audio_output'])} bytes -> {len(compressed)} bytes ({compression_ratio:.1%})")
        logger.info(f"Base64 size: {len(audio_b64)} chars (was {len(base64.b64encode(result['audio_output']).decode('utf-8'))} chars uncompressed)")

        # Send compressed response
        response_data = {
            "type": "audio_response_compressed",
            "transcription": result['transcription'],
            "text": result['response_text'],
            "audio": audio_b64,
            "compressed": True,
            "original_size": len(result['audio_output']),
            "compressed_size": len(compressed),
            "latency_ms": latency_ms,
            "metadata": {
                "stt_time_ms": result.get('stt_time_ms', 0),
                "llm_time_ms": result.get('llm_time_ms', 0),
                "tts_time_ms": result.get('tts_time_ms', 0)
            }
        }

        logger.info(f"Attempting to send compressed WebSocket message...")
        await websocket.send_json(response_data)
        logger.info(f"Compressed WebSocket message sent successfully")

    except Exception as e:
        logger.error(f"Failed to send compressed audio: {e}", exc_info=True)
        raise


async def handle_text_message(websocket: WebSocket, data: dict):
    """Handle text-only message (for testing without audio)"""
    start_time = time.time()

    try:
        text_input = data.get('text', '')

        # Process through LLM and TTS only
        result = await audio_pipeline.process_text(text_input)

        latency_ms = int((time.time() - start_time) * 1000)

        await websocket.send_json({
            "type": "text_response",
            "input": text_input,
            "text": result['response_text'],
            "audio": base64.b64encode(result['audio_output']).decode('utf-8'),
            "latency_ms": latency_ms
        })

    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"Text processing failed: {str(e)}"
        })


async def handle_config_message(websocket: WebSocket, data: dict):
    """Handle configuration update message"""
    try:
        settings = data.get('settings', {})

        if audio_pipeline:
            await audio_pipeline.update_config(settings)

        await websocket.send_json({
            "type": "config_updated",
            "settings": settings
        })

    except Exception as e:
        logger.error(f"Error handling config message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Configuration update failed: {str(e)}"
        })


def main():
    """Main entry point"""
    import os

    # Check for SSL certificates
    ssl_keyfile = "/home/nic/Harveylocalaudio/ssl/key.pem"
    ssl_certfile = "/home/nic/Harveylocalaudio/ssl/cert.pem"

    use_ssl = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)

    if use_ssl:
        logger.info("SSL certificates found - enabling WSS support")
        uvicorn.run(
            "main:app",
            host=config['server']['host'],
            port=config['server']['port'],
            log_level=config['logging']['level'].lower(),
            reload=False,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        logger.info("No SSL certificates - using WS only")
        uvicorn.run(
            "main:app",
            host=config['server']['host'],
            port=config['server']['port'],
            log_level=config['logging']['level'].lower(),
            reload=False
        )


if __name__ == "__main__":
    main()
