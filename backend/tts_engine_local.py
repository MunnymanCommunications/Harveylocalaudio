"""
Text-to-Speech Engine - Local Piper TTS
Fast, local TTS using Piper for minimal latency
"""

import asyncio
import io
import logging
import wave
from typing import Optional, Dict, Any
from pathlib import Path

import numpy as np
from piper import PiperVoice

logger = logging.getLogger(__name__)


class LocalPiperTTS:
    """Local Piper Text-to-Speech Engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Use male voice by default (Joe - deeper male voice)
        self.voice_model_path = Path(__file__).parent / 'piper_voices' / 'en_US-joe-medium.onnx'
        self.voice: Optional[PiperVoice] = None
        self.sample_rate = 22050  # Piper default

    async def initialize(self):
        """Initialize TTS engine"""
        logger.info(f"Initializing Local Piper TTS with model: {self.voice_model_path}")
        try:
            if not self.voice_model_path.exists():
                raise FileNotFoundError(f"Piper voice model not found at {self.voice_model_path}")

            # Load voice model
            self.voice = PiperVoice.load(str(self.voice_model_path))
            logger.info("Local Piper TTS initialized successfully")
            logger.info(f"Sample rate: {self.sample_rate}Hz")

        except Exception as e:
            logger.error(f"Failed to initialize Local Piper TTS: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.voice = None

    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text using local Piper

        Args:
            text: Text to convert to speech

        Returns:
            WAV audio bytes
        """
        if not text or not text.strip():
            return self._generate_silence(0.1)

        if self.voice is None:
            raise RuntimeError("Piper TTS not initialized")

        try:
            # Run synthesis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            wav_bytes = await loop.run_in_executor(None, self._synthesize_sync, text)

            return wav_bytes

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return self._generate_silence(1.0)

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous synthesis (runs in thread pool)"""
        # Use synthesize_wav to write directly to buffer
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wav_file:
            # Piper will set the format, but we can set it manually if needed
            self.voice.synthesize_wav(text, wav_file)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def _generate_silence(self, duration: float) -> bytes:
        """Generate silence WAV"""
        num_samples = int(self.sample_rate * duration)
        silence = np.zeros(num_samples, dtype=np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(silence.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()


# Alias for compatibility
PiperTTS = LocalPiperTTS
