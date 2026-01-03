"""
Audio Pipeline
Orchestrates STT -> LLM -> TTS pipeline for audio-to-audio conversations
"""

import asyncio
import io
import logging
import time
from typing import Dict, Any, Optional

import numpy as np
import soundfile as sf

from stt_engine import WhisperSTT
from llm_client import OllamaClient
from tts_engine import CoquiTTS

logger = logging.getLogger(__name__)


class AudioPipeline:
    """Complete audio processing pipeline"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Components
        self.stt: Optional[WhisperSTT] = None
        self.llm: Optional[OllamaClient] = None
        self.tts: Optional[CoquiTTS] = None

        # Conversation history
        self.conversation_history = []
        self.max_history = config['conversation']['max_history']
        self.system_prompt = config['conversation']['system_prompt']

    async def initialize(self):
        """Initialize all pipeline components"""
        logger.info("Initializing audio pipeline components...")

        # Initialize STT
        try:
            self.stt = WhisperSTT(self.config['stt'])
            await self.stt.initialize()
            logger.info("STT engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            raise

        # Initialize LLM
        try:
            self.llm = OllamaClient(self.config['llm'])
            await self.llm.initialize()
            logger.info("LLM client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

        # Initialize TTS
        try:
            self.tts = CoquiTTS(self.config['tts'])
            await self.tts.initialize()
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            raise

        logger.info("Audio pipeline ready")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up audio pipeline...")

        if self.stt:
            await self.stt.cleanup()

        if self.llm:
            await self.llm.cleanup()

        if self.tts:
            await self.tts.cleanup()

    async def process_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Process audio input through complete pipeline

        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            format: Audio format (wav, mp3, etc.)

        Returns:
            Dictionary with transcription, response text, and output audio
        """
        start_time = time.time()
        result = {}

        # Step 1: Speech-to-Text
        stt_start = time.time()
        try:
            transcription = await self.stt.transcribe(audio_data, sample_rate)
            result['transcription'] = transcription
            result['stt_time_ms'] = int((time.time() - stt_start) * 1000)
            logger.info(f"Transcription: {transcription}")
        except Exception as e:
            logger.error(f"STT failed: {e}")
            raise

        # Step 2: LLM Processing
        llm_start = time.time()
        try:
            response_text = await self.generate_response(transcription)
            result['response_text'] = response_text
            result['llm_time_ms'] = int((time.time() - llm_start) * 1000)
            logger.info(f"LLM response: {response_text[:100]}...")
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            raise

        # Step 3: Text-to-Speech
        tts_start = time.time()
        try:
            audio_output = await self.tts.synthesize(response_text)
            result['audio_output'] = audio_output
            result['tts_time_ms'] = int((time.time() - tts_start) * 1000)
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise

        result['total_time_ms'] = int((time.time() - start_time) * 1000)

        logger.info(f"Pipeline completed in {result['total_time_ms']}ms")

        return result

    async def process_text(self, text_input: str) -> Dict[str, Any]:
        """
        Process text input (skip STT, go directly to LLM -> TTS)

        Args:
            text_input: Text message from user

        Returns:
            Dictionary with response text and output audio
        """
        start_time = time.time()
        result = {}

        # LLM Processing
        llm_start = time.time()
        response_text = await self.generate_response(text_input)
        result['response_text'] = response_text
        result['llm_time_ms'] = int((time.time() - llm_start) * 1000)

        # Text-to-Speech
        tts_start = time.time()
        audio_output = await self.tts.synthesize(response_text)
        result['audio_output'] = audio_output
        result['tts_time_ms'] = int((time.time() - tts_start) * 1000)

        result['total_time_ms'] = int((time.time() - start_time) * 1000)

        return result

    async def generate_response(self, user_input: str) -> str:
        """
        Generate LLM response with conversation history

        Args:
            user_input: User's message

        Returns:
            LLM response text
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-(self.max_history * 2):]

        # Build messages with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        # Generate response
        response = await self.llm.generate(messages)

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    async def update_tts_config(self, voice_config: Dict[str, Any]):
        """Update TTS configuration"""
        if self.tts:
            await self.tts.update_config(voice_config)

    async def update_config(self, settings: Dict[str, Any]):
        """Update various pipeline settings"""
        if 'voice' in settings or 'speed' in settings:
            tts_config = {}
            if 'voice' in settings:
                tts_config['voice'] = settings['voice']
            if 'speed' in settings:
                tts_config['speed'] = settings['speed']

            await self.update_tts_config(tts_config)

        if 'temperature' in settings and self.llm:
            self.llm.temperature = settings['temperature']

        if 'system_prompt' in settings:
            self.system_prompt = settings['system_prompt']

    async def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            "stt_ready": self.stt is not None,
            "llm_ready": self.llm is not None,
            "tts_ready": self.tts is not None,
            "conversation_length": len(self.conversation_history),
            "llm_model": self.config['llm']['model'],
            "stt_model": self.config['stt']['model'],
            "tts_voice": self.config['tts']['voice']
        }

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
