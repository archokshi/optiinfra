"""
LLM Client for Groq API integration.

Provides a unified interface for interacting with Groq's gpt-oss-20b model
with error handling, retries, and response validation.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any

try:
    from groq import Groq, GroqError
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("Groq not available - LLM features disabled")

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger("resource_agent.llm")


class LLMClient:
    """Client for Groq LLM API with gpt-oss-20b model."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-oss-20b",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model name (default: gpt-oss-20b)
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        if not GROQ_AVAILABLE:
            logger.warning("Groq library not available - LLM client disabled")
            self.client = None
            return
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found - LLM client disabled")
            self.client = None
            return
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        logger.info(f"LLM client initialized with model: {self.model}")
    
    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return self.client is not None and GROQ_AVAILABLE
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional parameters
        
        Returns:
            Generated text response
        
        Raises:
            ValueError: If LLM client not available or response invalid
        """
        if not self.is_available():
            raise ValueError("LLM client not available")
        
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call Groq API
            logger.debug(f"Calling Groq API with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout,
                **kwargs
            )
            
            # Extract response
            if not response.choices:
                raise ValueError("No choices in LLM response")
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty content in LLM response")
            
            # Log metrics
            latency = (time.time() - start_time) * 1000
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(
                f"LLM response generated: {tokens_used} tokens, "
                f"{latency:.0f}ms latency"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    _instance: Optional[LLMClient] = None
    
    @classmethod
    def get_client(cls, **kwargs) -> LLMClient:
        """
        Get or create LLM client instance (singleton).
        
        Args:
            **kwargs: Arguments for LLMClient
        
        Returns:
            LLM client instance
        """
        if cls._instance is None:
            cls._instance = LLMClient(**kwargs)
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None
