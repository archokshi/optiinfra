"""
LLM Integration Module for Cost Agent.

This module provides LLM capabilities using Groq (gpt-oss-20b) for:
- Natural language insight generation
- Recommendation enhancement
- Executive summary creation
- Query handling
"""

from src.llm.llm_client import LLMClient
from src.llm.llm_integration import LLMIntegrationLayer

__all__ = [
    "LLMClient",
    "LLMIntegrationLayer",
]
