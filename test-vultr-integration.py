#!/usr/bin/env python3
"""
Vultr Integration Validation Script
Tests Vultr API connectivity and data collection
"""

import os
import sys
import asyncio
from datetime import datetime
import json

# Set environment variables
os.environ['VULTR_API_KEY'] = os.getenv('VULTR_API_KEY', 'your-vultr-api-key-here')
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', 'your-groq-api-key-here')
os.environ['GROQ_MODEL'] = 'gpt-oss-20b'

# Add cost-agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'cost-agent', 'src'))

print("=" * 80)
print("🚀 VULTR INTEGRATION VALIDATION")
print("=" * 80)
print(f"\n📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n🔑 API Keys Configured:")
print(f"   • Vultr API Key: {os.environ['VULTR_API_KEY'][:20]}...")
print(f"   • Groq API Key: {os.environ['GROQ_API_KEY'][:20]}...")
print(f"   • LLM Model: {os.environ['GROQ_MODEL']}")
print("\n" + "=" * 80)


async def test_vultr_client():
    """Test 1: Vultr API Client Connectivity"""
    print("\n📡 TEST 1: Vultr API Client Connectivity")
    print("-" * 80)
    
    try:
        from collectors.vultr.client import VultrClient
        
        client = VultrClient(api_key=os.environ['VULTR_API_KEY'])
        print("   ✅ VultrClient initialized")
        
        # Test account endpoint
        account_info = client.get_account_info()
        print(f"   ✅ Account API working")
        print(f"      • Account Name: {account_info.get('name', 'N/A')}")
        print(f"      • Email: {account_info.get('email', 'N/A')}")
        print(f"      • Balance: ${account_info.get('balance', 0):.2f}")
        print(f"      • Pending Charges: ${account_info.get('pending_charges', 0):.2f}")
        
        return True, account_info
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_vultr_billing():
    """Test 2: Vultr Billing Data Collection"""
    print("\n💰 TEST 2: Vultr Billing Data Collection")
    print("-" * 80)
    
    try:
        from collectors.vultr.billing import VultrBillingCollector
        
        collector = VultrBillingCollector(api_key=os.environ['VULTR_API_KEY'])
        print("   ✅ BillingCollector initialized")
        
        # Collect billing history
        billing_data = await collector.collect_billing_history(days=30)
        print(f"   ✅ Billing history collected")
        print(f"      • Records found: {len(billing_data)}")
        
        if billing_data:
            total_cost = sum(item.get('amount', 0) for item in billing_data)
            print(f"      • Total cost (30 days): ${total_cost:.2f}")
            print(f"      • Average daily cost: ${total_cost/30:.2f}")
        
        # Collect invoices
        invoices = await collector.collect_invoices()
        print(f"   ✅ Invoices collected: {len(invoices)} invoices")
        
        return True, billing_data
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_vultr_instances():
    """Test 3: Vultr Instance Inventory"""
    print("\n🖥️  TEST 3: Vultr Instance Inventory")
    print("-" * 80)
    
    try:
        from collectors.vultr.instances import VultrInstanceCollector
        
        collector = VultrInstanceCollector(api_key=os.environ['VULTR_API_KEY'])
        print("   ✅ InstanceCollector initialized")
        
        # Collect compute instances
        instances = await collector.collect_instances()
        print(f"   ✅ Compute instances: {len(instances)}")
        
        # Collect GPU instances
        gpu_instances = await collector.collect_gpu_instances()
        print(f"   ✅ GPU instances: {len(gpu_instances)}")
        
        # Collect bare metal
        bare_metal = await collector.collect_bare_metal()
        print(f"   ✅ Bare metal servers: {len(bare_metal)}")
        
        total_instances = len(instances) + len(gpu_instances) + len(bare_metal)
        print(f"\n   📊 Total Resources: {total_instances}")
        
        if instances:
            print(f"\n   💻 Sample Compute Instance:")
            sample = instances[0]
            print(f"      • ID: {sample.get('id')}")
            print(f"      • Label: {sample.get('label')}")
            print(f"      • Plan: {sample.get('plan')}")
            print(f"      • Region: {sample.get('region')}")
            print(f"      • Status: {sample.get('status')}")
        
        return True, {'instances': instances, 'gpu': gpu_instances, 'bare_metal': bare_metal}
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_vultr_analyzer():
    """Test 4: Vultr Cost Analysis"""
    print("\n📊 TEST 4: Vultr Cost Analysis")
    print("-" * 80)
    
    try:
        from collectors.vultr.analyzer import VultrCostAnalyzer
        
        analyzer = VultrCostAnalyzer(api_key=os.environ['VULTR_API_KEY'])
        print("   ✅ CostAnalyzer initialized")
        
        # Analyze costs
        analysis = await analyzer.analyze_costs(days=30)
        print(f"   ✅ Cost analysis complete")
        
        if analysis:
            print(f"\n   💵 Cost Breakdown:")
            print(f"      • Total Spend: ${analysis.get('total_cost', 0):.2f}")
            print(f"      • Compute Cost: ${analysis.get('compute_cost', 0):.2f}")
            print(f"      • GPU Cost: ${analysis.get('gpu_cost', 0):.2f}")
            print(f"      • Storage Cost: ${analysis.get('storage_cost', 0):.2f}")
            
            if 'waste_identified' in analysis:
                print(f"\n   ⚠️  Waste Identified: ${analysis['waste_identified']:.2f}")
            
            if 'recommendations' in analysis:
                print(f"\n   💡 Recommendations: {len(analysis['recommendations'])}")
                for i, rec in enumerate(analysis['recommendations'][:3], 1):
                    print(f"      {i}. {rec.get('title', 'N/A')}")
        
        return True, analysis
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


async def main():
    """Run all validation tests"""
    results = {}
    
    # Test 1: Client connectivity
    success, data = await test_vultr_client()
    results['client'] = {'success': success, 'data': data}
    
    # Test 2: Billing collection
    success, data = await test_vultr_billing()
    results['billing'] = {'success': success, 'data': data}
    
    # Test 3: Instance inventory
    success, data = await test_vultr_instances()
    results['instances'] = {'success': success, 'data': data}
    
    # Test 4: Cost analysis
    success, data = await test_vultr_analyzer()
    results['analyzer'] = {'success': success, 'data': data}
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   {status} - {test_name.upper()}")
    
    print(f"\n   Total: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")
    
    if passed_tests == total_tests:
        print("\n   🎉 ALL TESTS PASSED! Vultr integration is working perfectly!")
    else:
        print("\n   ⚠️  Some tests failed. Check errors above for details.")
    
    print("\n" + "=" * 80)
    print(f"✅ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
