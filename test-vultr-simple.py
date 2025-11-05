#!/usr/bin/env python3
"""
Simple Vultr API Test
Tests basic Vultr API connectivity with your credentials
"""

import os
import sys

# Set environment variables
os.environ['VULTR_API_KEY'] = '***REMOVED***'

# Add cost-agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'cost-agent', 'src'))

print("=" * 80)
print("🚀 VULTR API QUICK TEST")
print("=" * 80)
print(f"\n🔑 Using API Key: {os.environ['VULTR_API_KEY'][:20]}...")
print("\n" + "=" * 80)

try:
    from collectors.vultr.client import VultrClient
    
    print("\n📡 TEST 1: Initialize Vultr Client")
    print("-" * 80)
    client = VultrClient(api_key=os.environ['VULTR_API_KEY'])
    print("   ✅ VultrClient initialized successfully")
    
    print("\n💰 TEST 2: Get Account Information")
    print("-" * 80)
    account_info = client.get_account_info()
    print("   ✅ Account API call successful!")
    print(f"\n   📊 Account Details:")
    
    account_data = account_info.get('account', {})
    print(f"      • Name: {account_data.get('name', 'N/A')}")
    print(f"      • Email: {account_data.get('email', 'N/A')}")
    print(f"      • Balance: ${account_data.get('balance', 0)}")
    print(f"      • Pending Charges: ${account_data.get('pending_charges', 0)}")
    print(f"      • ACLs: {account_data.get('acls', [])}")
    
    print("\n📋 TEST 3: List Invoices")
    print("-" * 80)
    invoices = client.list_invoices()
    print(f"   ✅ Found {len(invoices)} invoices")
    
    if invoices:
        print(f"\n   📄 Recent Invoices:")
        for i, invoice in enumerate(invoices[:3], 1):
            print(f"      {i}. Invoice #{invoice.get('id')}")
            print(f"         Amount: ${invoice.get('amount', 0)}")
            print(f"         Date: {invoice.get('date', 'N/A')}")
            print(f"         Status: {invoice.get('status', 'N/A')}")
    
    print("\n🖥️  TEST 4: List Compute Instances")
    print("-" * 80)
    instances = client.list_instances()
    print(f"   ✅ Found {len(instances)} compute instances")
    
    if instances:
        print(f"\n   💻 Active Instances:")
        for i, instance in enumerate(instances[:5], 1):
            print(f"      {i}. {instance.get('label', 'Unnamed')}")
            print(f"         ID: {instance.get('id')}")
            print(f"         Plan: {instance.get('plan')}")
            print(f"         Region: {instance.get('region')}")
            print(f"         Status: {instance.get('status')}")
            print(f"         Monthly Cost: ${instance.get('monthly_cost', 0)}")
    else:
        print("      ℹ️  No compute instances found")
    
    print("\n🔧 TEST 5: List Bare Metal Servers")
    print("-" * 80)
    bare_metals = client.list_bare_metals()
    print(f"   ✅ Found {len(bare_metals)} bare metal servers")
    
    if bare_metals:
        print(f"\n   🖥️  Bare Metal Servers:")
        for i, server in enumerate(bare_metals[:3], 1):
            print(f"      {i}. {server.get('label', 'Unnamed')}")
            print(f"         ID: {server.get('id')}")
            print(f"         Plan: {server.get('plan')}")
    else:
        print("      ℹ️  No bare metal servers found")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n🎉 Vultr API integration is working perfectly!")
    print(f"\n📊 Summary:")
    print(f"   • Account verified: ✅")
    print(f"   • Invoices retrieved: ✅ ({len(invoices)} found)")
    print(f"   • Instances listed: ✅ ({len(instances)} found)")
    print(f"   • Bare metals listed: ✅ ({len(bare_metals)} found)")
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
