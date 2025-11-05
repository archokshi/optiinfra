#!/usr/bin/env python3
"""
Vultr Data Collection Script
Manually triggers collection of Vultr instance and billing data
"""

import os
import sys
from datetime import datetime

# Set environment variables
os.environ['VULTR_API_KEY'] = '***REMOVED***'

# Add cost-agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'cost-agent', 'src'))

print("=" * 80)
print("🔄 VULTR DATA COLLECTION")
print("=" * 80)
print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n" + "=" * 80)

try:
    from collectors.vultr.client import VultrClient
    from collectors.vultr.billing import VultrBillingCollector
    from collectors.vultr.instances import VultrInstanceCollector
    
    # Initialize client
    print("\n📡 Step 1: Initializing Vultr Client...")
    client = VultrClient(api_key=os.environ['VULTR_API_KEY'])
    print("   ✅ Client initialized")
    
    # Collect account info
    print("\n💰 Step 2: Collecting Account Information...")
    account_info = client.get_account_info()
    account_data = account_info.get('account', {})
    print("   ✅ Account data retrieved")
    print(f"      • Name: {account_data.get('name')}")
    print(f"      • Email: {account_data.get('email')}")
    print(f"      • Balance: ${account_data.get('balance', 0)}")
    print(f"      • Pending Charges: ${account_data.get('pending_charges', 0)}")
    
    # Collect instances
    print("\n🖥️  Step 3: Collecting Compute Instances...")
    instances = client.list_instances()
    print(f"   ✅ Found {len(instances)} compute instance(s)")
    
    if instances:
        print("\n   📋 Instance Details:")
        for i, instance in enumerate(instances, 1):
            print(f"\n   Instance #{i}:")
            print(f"      • ID: {instance.get('id')}")
            print(f"      • Label: {instance.get('label', 'Unnamed')}")
            print(f"      • Plan: {instance.get('plan')}")
            print(f"      • Region: {instance.get('region')}")
            print(f"      • Status: {instance.get('status')}")
            print(f"      • RAM: {instance.get('ram')} MB")
            print(f"      • vCPUs: {instance.get('vcpu_count')}")
            print(f"      • Disk: {instance.get('disk')} GB")
            print(f"      • Bandwidth: {instance.get('bandwidth')} GB")
            print(f"      • Monthly Cost: ${instance.get('monthly_cost', 0)}")
            print(f"      • Created: {instance.get('date_created')}")
            print(f"      • Main IP: {instance.get('main_ip')}")
            print(f"      • OS: {instance.get('os')}")
    else:
        print("      ℹ️  No instances found (may still be provisioning)")
    
    # Collect GPU instances
    print("\n🎮 Step 4: Collecting GPU Instances...")
    try:
        # Vultr API v2 doesn't have separate GPU endpoint, they're in regular instances
        gpu_instances = [i for i in instances if 'gpu' in i.get('plan', '').lower()]
        print(f"   ✅ Found {len(gpu_instances)} GPU instance(s)")
        
        if gpu_instances:
            for i, gpu in enumerate(gpu_instances, 1):
                print(f"\n   GPU Instance #{i}:")
                print(f"      • Label: {gpu.get('label')}")
                print(f"      • Plan: {gpu.get('plan')}")
                print(f"      • Monthly Cost: ${gpu.get('monthly_cost', 0)}")
    except Exception as e:
        print(f"   ⚠️  GPU check skipped: {e}")
    
    # Collect bare metal
    print("\n🔧 Step 5: Collecting Bare Metal Servers...")
    bare_metals = client.list_bare_metals()
    print(f"   ✅ Found {len(bare_metals)} bare metal server(s)")
    
    if bare_metals:
        for i, bm in enumerate(bare_metals, 1):
            print(f"\n   Bare Metal #{i}:")
            print(f"      • Label: {bm.get('label')}")
            print(f"      • Plan: {bm.get('plan')}")
            print(f"      • Monthly Cost: ${bm.get('monthly_cost', 0)}")
    
    # Collect billing data
    print("\n💳 Step 6: Collecting Billing Data...")
    billing_collector = VultrBillingCollector(client)
    
    # Get pending charges
    pending = billing_collector.collect_pending_charges()
    print(f"   ✅ Pending charges: ${pending.get('pending_charges', 0)}")
    
    # Get invoices
    invoices = client.list_invoices()
    print(f"   ✅ Found {len(invoices)} invoice(s)")
    
    if invoices:
        print("\n   📄 Recent Invoices:")
        for i, invoice in enumerate(invoices[:5], 1):
            print(f"      {i}. Invoice #{invoice.get('id')}")
            print(f"         Amount: ${invoice.get('amount', 0)}")
            print(f"         Date: {invoice.get('date')}")
    
    # Calculate total monthly cost
    print("\n💰 Step 7: Calculating Total Monthly Cost...")
    total_monthly = sum(i.get('monthly_cost', 0) for i in instances)
    total_monthly += sum(bm.get('monthly_cost', 0) for bm in bare_metals)
    
    print(f"   ✅ Total Monthly Cost: ${total_monthly:.2f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 COLLECTION SUMMARY")
    print("=" * 80)
    print(f"\n✅ Data Collection Complete!")
    print(f"\n📈 Infrastructure Summary:")
    print(f"   • Compute Instances: {len(instances)}")
    print(f"   • GPU Instances: {len(gpu_instances) if 'gpu_instances' in locals() else 0}")
    print(f"   • Bare Metal Servers: {len(bare_metals)}")
    print(f"   • Total Monthly Cost: ${total_monthly:.2f}")
    print(f"   • Pending Charges: ${pending.get('pending_charges', 0)}")
    print(f"   • Account Balance: ${account_data.get('balance', 0)}")
    
    print("\n🎯 Next Steps:")
    print("   1. This data has been collected from Vultr API")
    print("   2. To see it in the dashboard, we need to:")
    print("      a) Store it in ClickHouse database")
    print("      b) Refresh the portal dashboard")
    print("   3. Run: python store-vultr-data.py (I'll create this next)")
    
    print("\n" + "=" * 80)
    print(f"✅ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
