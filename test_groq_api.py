#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to validate Groq API key
"""
import os
import sys
import io
from groq import Groq

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_groq_api(api_key: str):
    """Test Groq API with the provided key"""
    print("=" * 60)
    print("GROQ API KEY VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Initialize client
        print(f"\n1. Initializing Groq client...")
        print(f"   API Key: {api_key[:20]}...{api_key[-10:]}")
        client = Groq(api_key=api_key)
        print("   ✅ Client initialized")
        
        # Test simple completion
        print(f"\n2. Testing chat completion...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, OptiInfra!' in exactly 3 words."}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"   Response: {result}")
        print(f"   Tokens used: {response.usage.total_tokens}")
        print("   ✅ API call successful")
        
        # Test with openai/gpt-oss-20b (our configured model)
        print(f"\n3. Testing with openai/gpt-oss-20b model...")
        try:
            response2 = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "user", "content": "What is 2+2? Answer in one word."}
                ],
                temperature=0.5,
                max_tokens=10
            )
            result2 = response2.choices[0].message.content
            print(f"   Response: {result2}")
            print(f"   Tokens used: {response2.usage.total_tokens}")
            print("   ✅ openai/gpt-oss-20b model working")
        except Exception as e:
            print(f"   ⚠️  openai/gpt-oss-20b not available: {e}")
            print(f"   Note: Check model name or availability")
        
        print("\n" + "=" * 60)
        print("✅ GROQ API KEY IS VALID AND WORKING!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n" + "=" * 60)
        print("❌ GROQ API KEY VALIDATION FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    # API key from command line or environment
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ No API key provided!")
        print("Usage: python test_groq_api.py YOUR_API_KEY")
        sys.exit(1)
    
    success = test_groq_api(api_key)
    sys.exit(0 if success else 1)
