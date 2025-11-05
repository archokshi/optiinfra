"""
Test Authentication System.

Simple test script to verify authentication components work.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auth.api_key import APIKeyManager
from src.auth.jwt_handler import JWTHandler


async def test_api_key_system():
    """Test API key generation and validation."""
    print("=" * 60)
    print("Testing API Key System")
    print("=" * 60)
    
    # Test 1: Generate API key
    print("\n1. Generating API key...")
    plain_key, key_record = await APIKeyManager.create_key(
        customer_id="cust-test-123",
        name="Test API Key",
        expires_days=365
    )
    print(f"   ✅ Generated key: {plain_key}")
    print(f"   ✅ Key ID: {key_record.id}")
    print(f"   ✅ Customer ID: {key_record.customer_id}")
    print(f"   ✅ Expires: {key_record.expires_at}")
    
    # Test 2: Validate API key
    print("\n2. Validating API key...")
    validated_key = await APIKeyManager.validate_key(plain_key)
    if validated_key:
        print(f"   ✅ Key validated successfully")
        print(f"   ✅ Customer ID: {validated_key.customer_id}")
        print(f"   ✅ Requests count: {validated_key.requests_count}")
    else:
        print(f"   ❌ Key validation failed")
    
    # Test 3: Validate invalid key
    print("\n3. Testing invalid key...")
    invalid_key = await APIKeyManager.validate_key("sk_invalid_key_12345")
    if invalid_key is None:
        print(f"   ✅ Invalid key correctly rejected")
    else:
        print(f"   ❌ Invalid key was accepted (should not happen)")
    
    # Test 4: List keys
    print("\n4. Listing keys for customer...")
    keys = await APIKeyManager.list_keys("cust-test-123")
    print(f"   ✅ Found {len(keys)} key(s)")
    for key in keys:
        print(f"      - {key.id}: {key.name}")
    
    # Test 5: Revoke key
    print("\n5. Revoking key...")
    success = await APIKeyManager.revoke_key(key_record.id)
    if success:
        print(f"   ✅ Key revoked successfully")
        
        # Try to validate revoked key
        revoked_key = await APIKeyManager.validate_key(plain_key)
        if revoked_key is None:
            print(f"   ✅ Revoked key correctly rejected")
        else:
            print(f"   ❌ Revoked key was still accepted")
    else:
        print(f"   ❌ Key revocation failed")


def test_jwt_system():
    """Test JWT token generation and validation."""
    print("\n" + "=" * 60)
    print("Testing JWT Token System")
    print("=" * 60)
    
    # Test 1: Create access token
    print("\n1. Creating access token...")
    token = JWTHandler.create_access_token(
        subject="user@example.com",
        customer_id="cust-test-123"
    )
    print(f"   ✅ Token created: {token[:50]}...")
    
    # Test 2: Decode token
    print("\n2. Decoding token...")
    payload = JWTHandler.decode_token(token)
    if payload:
        print(f"   ✅ Token decoded successfully")
        print(f"   ✅ Subject: {payload.get('sub')}")
        print(f"   ✅ Customer ID: {payload.get('customer_id')}")
        print(f"   ✅ Type: {payload.get('type')}")
    else:
        print(f"   ❌ Token decoding failed")
    
    # Test 3: Decode invalid token
    print("\n3. Testing invalid token...")
    invalid_payload = JWTHandler.decode_token("invalid.token.here")
    if invalid_payload is None:
        print(f"   ✅ Invalid token correctly rejected")
    else:
        print(f"   ❌ Invalid token was accepted")
    
    # Test 4: Create refresh token
    print("\n4. Creating refresh token...")
    refresh_token = JWTHandler.create_refresh_token(
        subject="user@example.com",
        customer_id="cust-test-123"
    )
    print(f"   ✅ Refresh token created: {refresh_token[:50]}...")
    
    # Decode refresh token
    refresh_payload = JWTHandler.decode_token(refresh_token)
    if refresh_payload and refresh_payload.get("type") == "refresh":
        print(f"   ✅ Refresh token type correct")
    else:
        print(f"   ❌ Refresh token type incorrect")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AUTHENTICATION SYSTEM TESTS")
    print("=" * 60)
    
    # Test API key system
    await test_api_key_system()
    
    # Test JWT system
    test_jwt_system()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
