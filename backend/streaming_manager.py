"""
Streaming Audio Manager
Handles continuous audio streaming, VAD, and interruption
"""

import asyncio
import io
import logging
import os
import tempfile
import time
from collections import deque
from typing import Optional, Callable
import numpy as np
import webrtcvad
import av
import soundfile as sf
import datetime
import pytz

logger = logging.getLogger(__name__)


class StreamingAudioManager:
    """Manages continuous audio streaming with simple timer-based chunking"""

    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 3.0):
        """
        Initialize streaming manager

        Args:
            sample_rate: Audio sample rate
            chunk_duration: Duration in seconds to accumulate before processing
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration

        # Audio buffer for accumulating raw chunks
        self.audio_buffer = []
        self.buffer_start_time = None

        # Callbacks
        self.on_chunk_ready: Optional[Callable] = None

        # State
        self.is_interrupted = False
        self.is_processing = False
        self.is_speaking = False

        logger.info(f"StreamingAudioManager initialized: sample_rate={sample_rate}, "
                   f"chunk_duration={chunk_duration}s")

    async def add_audio_chunk(self, audio_data: bytes) -> Optional[bytes]:
        """
        Add audio chunk (encoded WebM/MP4) to buffer

        Args:
            audio_data: Encoded audio bytes from MediaRecorder

        Returns:
            Complete audio segment if duration reached, None otherwise
        """
        current_time = time.time()

        # Start timer on first chunk
        if self.buffer_start_time is None:
            self.buffer_start_time = current_time
            self.is_speaking = True
            logger.info("Started accumulating audio chunks")

        # Add chunk to buffer
        self.audio_buffer.append(audio_data)

        # Check if we've accumulated enough duration
        elapsed = current_time - self.buffer_start_time

        if elapsed >= self.chunk_duration:
            logger.info(f"Chunk duration reached ({elapsed:.1f}s), processing {len(self.audio_buffer)} chunks")

            # Combine all buffered audio
            complete_audio = b''.join(self.audio_buffer)

            # Reset buffer
            self.audio_buffer = []
            self.buffer_start_time = None
            self.is_speaking = False

            # Notify callback if set
            if self.on_chunk_ready:
                await self.on_chunk_ready()

            return complete_audio

        return None

    def interrupt(self):
        """Signal that current processing should be interrupted"""
        logger.info("Interruption signaled")
        self.is_interrupted = True
        self.audio_buffer = []
        self.buffer_start_time = None
        self.is_speaking = False

    def reset(self):
        """Reset the manager state"""
        self.audio_buffer = []
        self.buffer_start_time = None
        self.is_speaking = False
        self.is_interrupted = False
        self.is_processing = False

    def get_state(self) -> dict:
        """Get current state for debugging"""
        elapsed = 0
        if self.buffer_start_time:
            elapsed = time.time() - self.buffer_start_time

        return {
            "is_speaking": self.is_speaking,
            "is_processing": self.is_processing,
            "is_interrupted": self.is_interrupted,
            "buffer_chunks": len(self.audio_buffer),
            "buffer_duration": elapsed
        }


class ConversationManager:
    """Manages full-duplex conversation flow"""

    def __init__(self, websocket, audio_pipeline):
        self.websocket = websocket
        self.audio_pipeline = audio_pipeline
        self.streaming_manager = StreamingAudioManager(sample_rate=16000, chunk_duration=5.0)
        self.is_harvey_speaking = False
        self.current_response_task: Optional[asyncio.Task] = None

        logger.info("ConversationManager initialized")

    async def interrupt_harvey(self):
        """Interrupt Harvey's current response"""
        self.is_harvey_speaking = False

        # Cancel ongoing response task
        if self.current_response_task and not self.current_response_task.done():
            self.current_response_task.cancel()
            try:
                await self.current_response_task
            except asyncio.CancelledError:
                pass

        # Notify client to stop playback
        await self.websocket.send_json({
            "type": "interrupt",
            "message": "Response interrupted"
        })

    async def handle_audio_chunk(self, audio_bytes: bytes):
        """
        Handle incoming audio chunk from client

        Args:
            audio_bytes: Encoded audio data (WebM/MP4)
        """
        # Add raw encoded chunk to buffer
        complete_audio = await self.streaming_manager.add_audio_chunk(audio_bytes)

        if complete_audio:
            # Duration reached, process accumulated audio
            logger.info(f"Processing accumulated audio ({len(complete_audio)} bytes)")
            await self.process_complete_speech(complete_audio)

    async def process_complete_speech(self, audio_data: bytes):
        """Process a complete speech segment with streaming audio response"""
        temp_file = None
        try:
            self.streaming_manager.is_processing = True

            # Notify client processing started
            await self.websocket.send_json({
                "type": "processing",
                "status": "started"
            })

            # Save accumulated WebM chunks to temporary file for reliable decoding
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as f:
                temp_file = f.name
                f.write(audio_data)

            # Read the file back and decode to WAV
            with open(temp_file, 'rb') as f:
                audio_bytes = f.read()

            # Decode audio to WAV
            import av
            wav_data = await self._decode_audio(audio_bytes, 'webm')

            # Transcribe
            start_time = time.time()
            transcription = await self.audio_pipeline.stt.transcribe(wav_data)
            stt_time = int((time.time() - start_time) * 1000)

            logger.info(f"Transcription: '{transcription}' ({stt_time}ms)")

            # Send transcription
            await self.websocket.send_json({
                "type": "transcription",
                "text": transcription
            })

            # Start Harvey speaking
            self.is_harvey_speaking = True

            # Define streaming callbacks
            import base64
            import zlib

            async def on_first_token(time_ms):
                """Send time to first token to client"""
                await self.websocket.send_json({
                    "type": "first_token",
                    "time_ms": time_ms
                })

            async def on_audio_chunk(audio_bytes, sentence_text, chunk_index):
                """Stream audio chunk to client immediately"""
                # Compress audio chunk
                compressed = zlib.compress(audio_bytes, level=6)
                audio_b64 = base64.b64encode(compressed).decode('utf-8')

                await self.websocket.send_json({
                    "type": "audio_chunk",
                    "chunk_index": chunk_index,
                    "sentence": sentence_text,
                    "audio": audio_b64,
                    "compressed": True,
                    "original_size": len(audio_bytes),
                    "compressed_size": len(compressed)
                })
                logger.info(f"Streamed chunk {chunk_index}: {len(sentence_text)} chars, {len(compressed)} bytes")

            # Generate response with streaming
            import datetime
            import pytz
            et_timezone = pytz.timezone('America/New_York')
            current_datetime = datetime.datetime.now(et_timezone).strftime("%A, %B %d, %Y at %I:%M %p %Z")

            response_text, _ = await self.audio_pipeline.generate_response_with_progressive_tts(
                user_input=transcription,
                context={"current_datetime": current_datetime},
                on_audio_chunk=on_audio_chunk,
                on_first_token=on_first_token
            )

            # Send completion signal
            await self.websocket.send_json({
                "type": "audio_complete",
                "text": response_text
            })

            self.is_harvey_speaking = False

        except Exception as e:
            logger.error(f"Error processing speech: {e}", exc_info=True)
            await self.websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        finally:
            self.streaming_manager.is_processing = False
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Could not delete temp file {temp_file}: {e}")

    async def _decode_audio(self, audio_data: bytes, format: str = 'webm') -> bytes:
        """Decode encoded audio to WAV format"""
        temp_input = None
        temp_output = None
        try:
            # Save input to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as f:
                temp_input = f.name
                f.write(audio_data)

            # Create temp output file
            temp_output = tempfile.mktemp(suffix='.wav')

            # Decode using av
            input_container = av.open(temp_input)
            output_container = av.open(temp_output, 'w')

            input_stream = input_container.streams.audio[0]
            output_stream = output_container.add_stream('pcm_s16le', rate=16000)
            output_stream.channels = 1

            for frame in input_container.decode(input_stream):
                frame = frame.to_ndarray().mean(axis=0) if frame.layout.channels > 1 else frame.to_ndarray()[0]
                frame = frame.reshape(-1, 1)
                for packet in output_stream.encode(av.AudioFrame.from_ndarray(frame, format='s16', layout='mono')):
                    output_container.mux(packet)

            for packet in output_stream.encode(None):
                output_container.mux(packet)

            output_container.close()
            input_container.close()

            # Read WAV data
            with open(temp_output, 'rb') as f:
                return f.read()

        finally:
            if temp_input and os.path.exists(temp_input):
                os.unlink(temp_input)
            if temp_output and os.path.exists(temp_output):
                os.unlink(temp_output)

    def get_state(self) -> dict:
        """Get conversation state"""
        return {
            "is_harvey_speaking": self.is_harvey_speaking,
            "streaming_state": self.streaming_manager.get_state()
        }
