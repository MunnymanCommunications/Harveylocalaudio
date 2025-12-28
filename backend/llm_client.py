"""
LLM Client
Ollama client for Gemma 3 14B and other local models
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

import aiohttp
import ollama

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama LLM Client for local model inference"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', 'gemma3:14b')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2048)
        self.top_p = config.get('top_p', 0.9)
        self.stream = config.get('stream', False)

        self.client: Optional[ollama.AsyncClient] = None

    async def initialize(self):
        """Initialize Ollama client and verify model availability"""
        logger.info(f"Initializing Ollama client for model: {self.model}")

        try:
            # Create async client
            self.client = ollama.AsyncClient(host=self.base_url)

            # Check if model is available
            await self._ensure_model_available()

            logger.info("Ollama client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        self.client = None

    async def _ensure_model_available(self):
        """Check if model is available, pull if not"""
        try:
            # List available models
            models = await self.client.list()

            model_names = [m['name'] for m in models.get('models', [])]

            if self.model not in model_names:
                logger.warning(f"Model {self.model} not found locally. Pulling...")
                await self._pull_model()
            else:
                logger.info(f"Model {self.model} is available")

        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            raise

    async def _pull_model(self):
        """Pull model from Ollama registry"""
        logger.info(f"Pulling model: {self.model}")

        try:
            # Pull model (this can take a while for large models)
            await self.client.pull(self.model)
            logger.info(f"Model {self.model} pulled successfully")

        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            raise

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from messages

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Generated response text
        """
        if self.client is None:
            raise RuntimeError("Ollama client not initialized")

        try:
            logger.debug(f"Generating response for {len(messages)} messages")

            # Call Ollama chat API
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                    'top_p': self.top_p
                },
                stream=False
            )

            response_text = response['message']['content']

            logger.debug(f"Generated response: {response_text[:100]}...")

            return response_text

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    async def generate_stream(self, messages: List[Dict[str, str]]):
        """
        Generate streaming response

        Args:
            messages: List of message dicts

        Yields:
            Response text chunks
        """
        if self.client is None:
            raise RuntimeError("Ollama client not initialized")

        try:
            stream = await self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                    'top_p': self.top_p
                },
                stream=True
            )

            async for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    async def check_health(self) -> bool:
        """Check if Ollama server is healthy"""
        try:
            if self.client:
                models = await self.client.list()
                return True
            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
