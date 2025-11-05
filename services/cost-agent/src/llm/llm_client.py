"""
LLM Client for Groq API integration.

Provides a unified interface for interacting with Groq's gpt-oss-20b model
with error handling, retries, and response validation.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from groq import Groq, GroqError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


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
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        logger.info(f"LLM client initialized with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GroqError)
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
            GroqError: If API call fails after retries
            ValueError: If response is invalid
        """
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
            
        except GroqError as e:
            logger.error(f"Groq API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            response_format: Expected JSON schema
            **kwargs: Additional parameters
        
        Returns:
            Parsed JSON response
        
        Raises:
            GroqError: If API call fails
            ValueError: If response is not valid JSON
        """
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        
        # Generate response
        response = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Parse JSON
        try:
            import json
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response: {e}")
    
    async def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of user prompts
            system_prompt: System prompt (optional)
            **kwargs: Additional parameters
        
        Returns:
            List of generated responses
        """
        responses = []
        for prompt in prompts:
            try:
                response = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs
                )
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to generate response for prompt: {e}")
                responses.append(f"Error: {str(e)}")
        
        return responses
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4
    
    def validate_response(self, response: str, min_length: int = 10) -> bool:
        """
        Validate LLM response quality.
        
        Args:
            response: Response to validate
            min_length: Minimum response length
        
        Returns:
            True if response is valid
        """
        if not response or len(response) < min_length:
            return False
        
        # Check for common error patterns
        error_patterns = [
            "I cannot",
            "I'm unable to",
            "I don't have access",
            "Error:",
            "Exception:"
        ]
        
        for pattern in error_patterns:
            if pattern.lower() in response.lower():
                logger.warning(f"Response contains error pattern: {pattern}")
                return False
        
        return True


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
