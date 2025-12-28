"""
Speech-to-Text Engine
Uses OpenAI Whisper for high-quality speech recognition
"""

import io
import logging
import asyncio
from typing import Optional, Dict, Any

import numpy as np
import soundfile as sf
import torch
import whisper

logger = logging.getLogger(__name__)


class WhisperSTT:
    """Whisper Speech-to-Text Engine"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model', 'large-v3')
        self.language = config.get('language', 'en')
        self.device = config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.model: Optional[whisper.Whisper] = None

    async def initialize(self):
        """Load Whisper model"""
        logger.info(f"Loading Whisper model: {self.model_name} on {self.device}")

        try:
            # Run model loading in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                whisper.load_model,
                self.model_name,
                self.device
            )

            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        if self.model is not None:
            del self.model
            self.model = None

            if self.device == 'cuda':
                torch.cuda.empty_cache()

    async def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text

        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate of audio

        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Whisper model not initialized")

        try:
            # Convert audio bytes to numpy array
            audio_array = self._load_audio(audio_data, sample_rate)

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_array
            )

            text = result['text'].strip()
            logger.debug(f"Transcribed: {text}")

            return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _transcribe_sync(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Synchronous transcription (runs in thread pool)"""
        return self.model.transcribe(
            audio_array,
            language=self.language,
            fp16=(self.device == 'cuda')
        )

    def _load_audio(self, audio_data: bytes, sample_rate: int) -> np.ndarray:
        """
        Load audio from bytes and convert to format expected by Whisper

        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate

        Returns:
            Numpy array of audio samples
        """
        # Read audio from bytes
        audio_io = io.BytesIO(audio_data)
        audio_array, sr = sf.read(audio_io)

        # Convert to mono if stereo
        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)

        # Resample to 16kHz if needed (Whisper expects 16kHz)
        if sr != 16000:
            audio_array = self._resample(audio_array, sr, 16000)

        # Convert to float32
        audio_array = audio_array.astype(np.float32)

        return audio_array

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate"""
        import librosa

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
