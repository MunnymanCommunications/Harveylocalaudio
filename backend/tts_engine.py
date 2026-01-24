"""
Text-to-Speech Engine
Uses Coqui XTTS for high-quality voice synthesis with voice cloning
"""

import asyncio
import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import soundfile as sf
import torch
import numpy as np

logger = logging.getLogger(__name__)


class CoquiTTS:
    """Coqui XTTS Text-to-Speech Engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.voice = config.get('voice', 'default')
        self.speed = config.get('speed', 1.0)
        self.language = config.get('language', 'en')
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.tts = None
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"

        # Voice sample paths for cloning
        self.voice_samples = {
            'default': None,  # Uses default XTTS voice
            'male': None,
            'female': None,
            'custom': None
        }

    async def initialize(self):
        """Initialize TTS engine"""
        logger.info(f"Initializing Coqui XTTS with voice: {self.voice}")

        try:
            # Import TTS here to avoid loading if not needed
            from TTS.api import TTS

            # Run model loading in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            self.tts = await loop.run_in_executor(
                None,
                self._load_model,
                TTS
            )

            logger.info(f"Coqui XTTS initialized successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
            raise

    def _load_model(self, TTS):
        """Load TTS model (runs in thread pool)"""
        tts = TTS(
            model_name=self.model_name,
            progress_bar=False,
            gpu=(self.device == 'cuda')
        )
        return tts

    async def cleanup(self):
        """Cleanup resources"""
        if self.tts is not None:
            del self.tts
            self.tts = None

            if self.device == 'cuda':
                torch.cuda.empty_cache()

    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize

        Returns:
            Audio data as WAV bytes
        """
        if self.tts is None:
            raise RuntimeError("Coqui TTS not initialized")

        try:
            logger.info(f"Synthesizing text ({len(text)} chars): {text[:100]}...")

            # Run synthesis in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            wav_bytes = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text
            )

            logger.info(f"Synthesized audio: {len(wav_bytes)} bytes")
            return wav_bytes

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}", exc_info=True)
            silence = self._generate_silence(1.0)
            logger.info(f"Returning silence due to error: {len(silence)} bytes")
            return silence

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous synthesis (runs in thread pool)"""
        try:
            # Get voice sample if using voice cloning
            speaker_wav = self.voice_samples.get(self.voice)

            if speaker_wav and Path(speaker_wav).exists():
                # Use voice cloning with reference audio
                wav = self.tts.tts(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=self.language,
                    speed=self.speed
                )
            else:
                # Use default XTTS voice
                wav = self.tts.tts(
                    text=text,
                    language=self.language,
                    speed=self.speed
                )

            # Convert to numpy array if needed
            if isinstance(wav, list):
                wav = np.array(wav, dtype=np.float32)

            # Normalize audio
            if np.max(np.abs(wav)) > 0:
                wav = wav / np.max(np.abs(wav))

            # Convert to WAV bytes
            wav_io = io.BytesIO()
            sf.write(wav_io, wav, self.tts.synthesizer.output_sample_rate, format='WAV')
            wav_io.seek(0)

            return wav_io.read()

        except Exception as e:
            logger.error(f"Coqui synthesis error: {e}")
            return self._generate_silence(1.0)

    def _generate_silence(self, duration: float = 1.0, sample_rate: int = 24000) -> bytes:
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

        if 'language' in config:
            self.language = config['language']
            logger.info(f"Language changed to: {self.language}")

    def add_voice_sample(self, voice_name: str, sample_path: str):
        """
        Add a voice sample for cloning

        Args:
            voice_name: Name for this voice
            sample_path: Path to audio file (3-10 seconds of clear speech)
        """
        if Path(sample_path).exists():
            self.voice_samples[voice_name] = sample_path
            logger.info(f"Voice sample '{voice_name}' added: {sample_path}")
        else:
            logger.error(f"Voice sample not found: {sample_path}")

    def list_voices(self) -> list:
        """List available voices"""
        return list(self.voice_samples.keys())
