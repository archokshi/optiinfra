"""
Quick validation script for LLM integration.
Run this to verify all components are working.
"""

import sys
import os

print("=" * 60)
print("PHASE1-1.8 LLM Integration Validation")
print("=" * 60)

# Test 1: Import LLM Client
print("\n[1/6] Testing LLM Client import...")
try:
    from src.llm.llm_client import LLMClient, LLMClientFactory
    print("✅ LLM Client imported successfully")
except Exception as e:
    print(f"❌ Failed to import LLM Client: {e}")
    sys.exit(1)

# Test 2: Import Prompt Templates
print("\n[2/6] Testing Prompt Templates import...")
try:
    from src.llm.prompt_templates import PromptTemplate
    print("✅ Prompt Templates imported successfully")
except Exception as e:
    print(f"❌ Failed to import Prompt Templates: {e}")
    sys.exit(1)

# Test 3: Import Insight Generator
print("\n[3/6] Testing Insight Generator import...")
try:
    from src.llm.insight_generator import (
        generate_insights,
        enhance_recommendations,
        generate_executive_summary
    )
    print("✅ Insight Generator imported successfully")
except Exception as e:
    print(f"❌ Failed to import Insight Generator: {e}")
    sys.exit(1)

# Test 4: Import LLM Integration Layer
print("\n[4/6] Testing LLM Integration Layer import...")
try:
    from src.llm.llm_integration import LLMIntegrationLayer
    print("✅ LLM Integration Layer imported successfully")
except Exception as e:
    print(f"❌ Failed to import LLM Integration Layer: {e}")
    sys.exit(1)

# Test 5: Import Pydantic Models
print("\n[5/6] Testing Pydantic Models import...")
try:
    from src.models.llm_integration import (
        LLMRequest,
        LLMResponse,
        InsightGenerationRequest
    )
    print("✅ Pydantic Models imported successfully")
except Exception as e:
    print(f"❌ Failed to import Pydantic Models: {e}")
    sys.exit(1)

# Test 6: Check Configuration
print("\n[6/6] Testing Configuration...")
try:
    from src.config import get_settings
    settings = get_settings()
    print(f"✅ Configuration loaded")
    print(f"   - LLM Enabled: {settings.LLM_ENABLED}")
    print(f"   - Groq Model: {settings.GROQ_MODEL}")
    print(f"   - LLM Timeout: {settings.LLM_TIMEOUT}s")
except Exception as e:
    print(f"❌ Failed to load configuration: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL VALIDATION CHECKS PASSED!")
print("=" * 60)
print("\nNext steps:")
print("1. Set your GROQ_API_KEY in .env file")
print("2. Run: pytest tests/test_llm_integration.py -v")
print("3. Test with real Groq API")
print("=" * 60)
