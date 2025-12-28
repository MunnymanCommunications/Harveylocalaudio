"""
Text-to-Speech Engine
Uses Piper TTS for high-quality voice synthesis
"""

import asyncio
import io
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class PiperTTS:
    """Piper Text-to-Speech Engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.voice = config.get('voice', 'en_US-lessac-medium')
        self.speed = config.get('speed', 1.0)
        self.quality = config.get('quality', 'high')

        self.piper_path = 'piper'  # Assume piper is in PATH
        self.model_path: Optional[Path] = None

    async def initialize(self):
        """Initialize TTS engine"""
        logger.info(f"Initializing Piper TTS with voice: {self.voice}")

        try:
            # Check if piper is available
            result = subprocess.run(
                ['which', 'piper'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "Piper not found. Install with: pip install piper-tts"
                )

            logger.info("Piper TTS initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        pass

    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize

        Returns:
            Audio data as WAV bytes
        """
        try:
            logger.debug(f"Synthesizing: {text[:100]}...")

            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text
            )

            return audio_data

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous TTS synthesis"""
        try:
            # Run piper command
            cmd = [
                'piper',
                '--model', self.voice,
                '--output-raw'
            ]

            if self.speed != 1.0:
                cmd.extend(['--length-scale', str(1.0 / self.speed)])

            # Run piper process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send text and get audio
            stdout, stderr = process.communicate(input=text.encode('utf-8'))

            if process.returncode != 0:
                raise RuntimeError(f"Piper failed: {stderr.decode()}")

            # Convert raw audio to WAV format
            audio_array = np.frombuffer(stdout, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Write to WAV bytes
            wav_io = io.BytesIO()
            sf.write(wav_io, audio_float, 22050, format='WAV')
            wav_io.seek(0)

            return wav_io.read()

        except Exception as e:
            logger.error(f"Piper synthesis error: {e}")
            # Fallback: return silent audio
            return self._generate_silence(1.0)

    def _generate_silence(self, duration: float = 1.0, sample_rate: int = 22050) -> bytes:
        """Generate silence as fallback"""
        samples = int(duration * sample_rate)
        silence = np.zeros(samples, dtype=np.float32)

        wav_io = io.BytesIO()
        sf.write(wav_io, silence, sample_rate, format='WAV')
        wav_io.seek(0)

        return wav_io.read()

    async def update_config(self, config: Dict[str, Any]):
        """Update TTS configuration"""
        if 'voice' in config:
            self.voice = config['voice']
            logger.info(f"Voice changed to: {self.voice}")

        if 'speed' in config:
            self.speed = config['speed']
            logger.info(f"Speed changed to: {self.speed}")

        if 'quality' in config:
            self.quality = config['quality']
