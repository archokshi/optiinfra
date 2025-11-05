"""
Quick test to verify Vultr API connectivity.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from collectors.vultr import VultrClient, VultrAPIError


def test_connection():
    """Test Vultr API connection"""
    
    api_key = os.getenv("VULTR_API_KEY")
    if not api_key:
        print("❌ VULTR_API_KEY not set")
        print("   Get your API key from: https://my.vultr.com/settings/#settingsapi")
        print("\n   To set it:")
        print("   Windows: $env:VULTR_API_KEY='your_key_here'")
        print("   Linux/Mac: export VULTR_API_KEY='your_key_here'")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}..." + "*" * 20)
    
    try:
        # Initialize client
        print("\n📡 Initializing Vultr client...")
        client = VultrClient(api_key=api_key)
        print("✅ Client initialized")
        
        # Test API call
        print("\n🌐 Testing API call: GET /account...")
        account = client.get_account_info()
        
        account_data = account.get("account", {})
        print("✅ API call successful!")
        print(f"\n📊 Account Info:")
        print(f"   Name: {account_data.get('name', 'N/A')}")
        print(f"   Email: {account_data.get('email', 'N/A')}")
        print(f"   Balance: ${account_data.get('balance', 0):.2f}")
        print(f"   Pending: ${account_data.get('pending_charges', 0):.2f}")
        
        return True
        
    except VultrAPIError as e:
        print(f"❌ API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Vultr API Connection Test")
    print("=" * 60)
    
    success = test_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ CONNECTION TEST PASSED")
    else:
        print("❌ CONNECTION TEST FAILED")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
