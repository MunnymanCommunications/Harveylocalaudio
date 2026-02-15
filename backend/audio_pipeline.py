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
from tts_engine_local import LocalPiperTTS as CoquiTTS  # Using Piper TTS (Python 3.12 compatible)

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
        format: str = "wav",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process audio input through complete pipeline

        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            format: Audio format (wav, mp3, etc.)
            context: Additional context (datetime, location, etc.)

        Returns:
            Dictionary with transcription, response text, and output audio
        """
        start_time = time.time()
        result = {}
        context = context or {}

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

        # Step 2 & 3: LLM + Progressive TTS (parallel processing)
        llm_tts_start = time.time()
        try:
            # Use progressive TTS - synthesize speech as sentences stream in
            response_text, audio_output = await self.generate_response_with_progressive_tts(transcription, context)
            result['response_text'] = response_text
            result['audio_output'] = audio_output
            result['llm_time_ms'] = int((time.time() - llm_tts_start) * 1000)
            result['tts_time_ms'] = 0  # TTS time included in llm_time_ms (progressive)
            logger.info(f"Progressive LLM+TTS response: {response_text[:100]}...")
        except Exception as e:
            logger.error(f"Progressive LLM+TTS failed: {e}")
            raise

        result['total_time_ms'] = int((time.time() - start_time) * 1000)

        logger.info(f"Pipeline completed in {result['total_time_ms']}ms")

        return result

    async def process_text(self, text_input: str) -> Dict[str, Any]:
        """
        Process text input (skip STT, go directly to LLM -> TTS with progressive synthesis)

        Args:
            text_input: Text message from user

        Returns:
            Dictionary with response text and output audio
        """
        start_time = time.time()
        result = {}

        # LLM + Progressive TTS Processing
        llm_tts_start = time.time()
        response_text, audio_output = await self.generate_response_with_progressive_tts(text_input)
        result['response_text'] = response_text
        result['audio_output'] = audio_output
        result['llm_time_ms'] = int((time.time() - llm_tts_start) * 1000)
        result['tts_time_ms'] = 0  # TTS time included in llm_time_ms (progressive)

        result['total_time_ms'] = int((time.time() - start_time) * 1000)

        return result

    async def generate_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Generate LLM response with conversation history and context using streaming

        Args:
            user_input: User's message
            context: Additional context (datetime, etc.)

        Returns:
            LLM response text
        """
        # Validate user input is not empty
        if not user_input or not user_input.strip():
            logger.warning(f"Empty user input received, skipping")
            raise ValueError("User input cannot be empty")

        context = context or {}

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input.strip()
        })

        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-(self.max_history * 2):]

        # Filter out any empty messages from history (cleanup)
        self.conversation_history = [
            msg for msg in self.conversation_history
            if msg.get('content', '').strip()
        ]

        # Enhance system prompt with context
        system_content = self.system_prompt
        if context.get('current_datetime'):
            system_content += f"\n\nCurrent date and time (Eastern Time): {context['current_datetime']}"

        # Build messages with system prompt
        messages = [
            {"role": "system", "content": system_content}
        ] + self.conversation_history

        # Debug logging
        logger.info(f"Generating with {len(messages)} messages, user_input: '{user_input}'")
        logger.info(f"System prompt: '{self.system_prompt}'")
        for i, msg in enumerate(messages):
            logger.info(f"Message {i}: role={msg.get('role')}, content='{msg.get('content', '')[:50]}'")

        # Generate response using streaming
        stream_start = time.time()
        first_token_time = None
        response_chunks = []

        try:
            async for chunk in self.llm.generate_stream(messages):
                # Measure time to first token
                if first_token_time is None:
                    first_token_time = time.time() - stream_start
                    logger.info(f"⚡ TIME TO FIRST TOKEN: {int(first_token_time * 1000)}ms")

                response_chunks.append(chunk)

            # Combine all chunks
            response = ''.join(response_chunks)
            total_stream_time = time.time() - stream_start

            logger.info(f"Streaming completed: {len(response_chunks)} chunks in {int(total_stream_time * 1000)}ms")
            logger.info(f"Response length: {len(response)} characters")

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    async def generate_response_with_progressive_tts(
        self,
        user_input: str,
        context: Dict[str, Any] = None,
        on_audio_chunk: Optional[callable] = None,
        on_first_token: Optional[callable] = None
    ) -> tuple[str, bytes]:
        """
        Generate LLM response with progressive TTS - synthesize speech as sentences complete

        Args:
            user_input: User's message
            context: Additional context (datetime, etc.)
            on_audio_chunk: Optional callback(audio_bytes, sentence_text, chunk_index) for streaming
            on_first_token: Optional callback(time_ms) called when first token arrives

        Returns:
            Tuple of (response_text, audio_bytes)
        """
        # Validate user input is not empty
        if not user_input or not user_input.strip():
            logger.warning(f"Empty user input received, skipping")
            raise ValueError("User input cannot be empty")

        context = context or {}

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input.strip()
        })

        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-(self.max_history * 2):]

        # Filter out any empty messages from history (cleanup)
        self.conversation_history = [
            msg for msg in self.conversation_history
            if msg.get('content', '').strip()
        ]

        # Enhance system prompt with context
        system_content = self.system_prompt
        if context.get('current_datetime'):
            system_content += f"\n\nCurrent date and time (Eastern Time): {context['current_datetime']}"

        # Build messages with system prompt
        messages = [
            {"role": "system", "content": system_content}
        ] + self.conversation_history

        # Debug logging
        logger.info(f"Generating with progressive TTS for input: '{user_input}'")

        # Progressive TTS state
        stream_start = time.time()
        first_token_time = None
        first_audio_time = None
        response_chunks = []
        sentence_buffer = ""
        audio_chunks = []
        sentence_count = 0

        # Sentence ending punctuation
        sentence_endings = {'.', '!', '?', '\n'}

        try:
            async for chunk in self.llm.generate_stream(messages):
                # Measure time to first token
                if first_token_time is None:
                    first_token_time = time.time() - stream_start
                    logger.info(f"⚡ TIME TO FIRST TOKEN: {int(first_token_time * 1000)}ms")

                    # Call first token callback
                    if on_first_token:
                        await on_first_token(int(first_token_time * 1000))

                response_chunks.append(chunk)
                sentence_buffer += chunk

                # Check if we have a complete sentence
                if any(sentence_buffer.rstrip().endswith(end) for end in sentence_endings):
                    sentence = sentence_buffer.strip()
                    if sentence:  # Only synthesize non-empty sentences
                        sentence_count += 1
                        logger.info(f"📝 Sentence {sentence_count} complete ({len(sentence)} chars): {sentence[:50]}...")

                        # Synthesize this sentence
                        try:
                            tts_start = time.time()
                            audio_chunk = await self.tts.synthesize(sentence)
                            tts_time = int((time.time() - tts_start) * 1000)

                            if first_audio_time is None:
                                first_audio_time = time.time() - stream_start
                                logger.info(f"🔊 TIME TO FIRST AUDIO: {int(first_audio_time * 1000)}ms")

                            audio_chunks.append(audio_chunk)
                            logger.info(f"✅ Sentence {sentence_count} synthesized in {tts_time}ms ({len(audio_chunk)} bytes)")

                            # Stream audio chunk immediately if callback provided
                            if on_audio_chunk:
                                await on_audio_chunk(audio_chunk, sentence, sentence_count - 1)

                        except Exception as e:
                            logger.error(f"TTS failed for sentence {sentence_count}: {e}")

                    sentence_buffer = ""

            # Handle any remaining text that didn't end with punctuation
            if sentence_buffer.strip():
                sentence_count += 1
                logger.info(f"📝 Final fragment ({len(sentence_buffer)} chars): {sentence_buffer[:50]}...")
                try:
                    audio_chunk = await self.tts.synthesize(sentence_buffer.strip())
                    audio_chunks.append(audio_chunk)
                    logger.info(f"✅ Final fragment synthesized ({len(audio_chunk)} bytes)")

                    # Stream final chunk
                    if on_audio_chunk:
                        await on_audio_chunk(audio_chunk, sentence_buffer.strip(), sentence_count - 1)

                except Exception as e:
                    logger.error(f"TTS failed for final fragment: {e}")

            # Combine all text chunks
            response = ''.join(response_chunks)
            total_time = time.time() - stream_start

            logger.info(f"🎯 Progressive TTS completed:")
            logger.info(f"   - Total time: {int(total_time * 1000)}ms")
            logger.info(f"   - Sentences: {sentence_count}")
            logger.info(f"   - Audio chunks: {len(audio_chunks)}")
            logger.info(f"   - Text length: {len(response)} characters")

        except Exception as e:
            logger.error(f"Progressive generation failed: {e}")
            raise

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        # Combine all audio chunks
        combined_audio = await self._combine_audio_chunks(audio_chunks)

        return response, combined_audio

    async def _combine_audio_chunks(self, audio_chunks: list[bytes]) -> bytes:
        """
        Combine multiple WAV audio chunks into a single WAV file

        Args:
            audio_chunks: List of WAV audio bytes

        Returns:
            Combined WAV audio bytes
        """
        if not audio_chunks:
            logger.warning("No audio chunks to combine, generating silence")
            return self.tts._generate_silence(1.0)

        if len(audio_chunks) == 1:
            return audio_chunks[0]

        try:
            import io
            import soundfile as sf
            import numpy as np

            # Read all audio chunks
            audio_arrays = []
            sample_rate = None

            for i, chunk in enumerate(audio_chunks):
                try:
                    audio_io = io.BytesIO(chunk)
                    audio_array, sr = sf.read(audio_io)

                    if sample_rate is None:
                        sample_rate = sr
                    elif sr != sample_rate:
                        logger.warning(f"Sample rate mismatch in chunk {i}: {sr} vs {sample_rate}")

                    audio_arrays.append(audio_array)

                except Exception as e:
                    logger.error(f"Failed to read audio chunk {i}: {e}")

            if not audio_arrays:
                logger.warning("No valid audio arrays, generating silence")
                return self.tts._generate_silence(1.0)

            # Concatenate all audio
            combined_array = np.concatenate(audio_arrays)

            # Write to WAV bytes
            wav_io = io.BytesIO()
            sf.write(wav_io, combined_array, sample_rate, format='WAV')
            wav_io.seek(0)

            combined_bytes = wav_io.read()
            logger.info(f"Combined {len(audio_chunks)} chunks into {len(combined_bytes)} bytes")

            return combined_bytes

        except Exception as e:
            logger.error(f"Failed to combine audio chunks: {e}")
            # Return first chunk as fallback
            return audio_chunks[0] if audio_chunks else self.tts._generate_silence(1.0)

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
