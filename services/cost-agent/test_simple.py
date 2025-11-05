"""Simple test to verify LLM components work."""

import os
os.environ['GROQ_API_KEY'] = 'test-key-12345'

from src.llm.llm_client import LLMClient
from src.llm.prompt_templates import PromptTemplate

print("Testing LLM Client initialization...")
try:
    client = LLMClient()
    print(f"✅ Client created with model: {client.model}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTesting Prompt Template...")
try:
    prompt = PromptTemplate.render_insight_generation({
        "idle_resources": [],
        "total_monthly_waste": 1000
    })
    print(f"✅ Prompt generated ({len(prompt)} chars)")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Simple tests passed!")
