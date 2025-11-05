"""
LLM Client

Groq client for LLM-based quality analysis.
"""

import os
from typing import Optional
from groq import Groq, AsyncGroq
from ..core.logger import logger


class LLMClient:
    """Client for Groq LLM API."""
    
    def __init__(self):
        """Initialize LLM client."""
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "gpt-oss-20b")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set, LLM features will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.client = AsyncGroq(api_key=self.api_key, timeout=self.timeout)
            logger.info(f"LLM client initialized with model: {self.model}")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Generate LLM response.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response or None on error
        """
        if not self.enabled:
            logger.warning("LLM client not enabled")
            return None
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            logger.debug(f"LLM response generated: {len(content)} chars")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return None
    
    def parse_score(self, response: Optional[str]) -> Optional[float]:
        """
        Parse score from LLM response.
        
        Args:
            response: LLM response
            
        Returns:
            Parsed score (0-100) or None
        """
        if not response:
            return None
        
        try:
            # Extract first number from response (including negative)
            import re
            numbers = re.findall(r'-?\d+\.?\d*', response)
            if numbers:
                score = float(numbers[0])
                # Clamp to 0-100 range
                score = max(0.0, min(100.0, score))
                return score
            else:
                logger.warning(f"No number found in LLM response: {response}")
                return None
                
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse score from: {response[:50]}... Error: {e}")
            return None


# Global instance
llm_client = LLMClient()
