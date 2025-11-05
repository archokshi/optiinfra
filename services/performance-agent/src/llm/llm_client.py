"""LLM Client for Groq API integration."""

import os
import logging
import time
from typing import Optional, Dict, Any
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for Groq LLM API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-oss-20b",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize LLM client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model name
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = AsyncGroq(api_key=self.api_key)
        
        logger.info(f"LLM client initialized with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with content, tokens_used, model, latency_ms
        """
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            result = {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": self.model,
                "latency_ms": latency_ms
            }
            
            logger.info(
                f"LLM generation successful: {result['tokens_used']} tokens, "
                f"{latency_ms:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
