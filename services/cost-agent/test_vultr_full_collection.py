"""
Full integration test for Vultr data collection.
Run this to verify end-to-end collection works.
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from collectors.vultr import collect_vultr_metrics


def main():
    api_key = os.getenv("VULTR_API_KEY")
    if not api_key:
        print("❌ VULTR_API_KEY not set")
        print("\n   To set it:")
        print("   Windows: $env:VULTR_API_KEY='your_key_here'")
        print("   Linux/Mac: export VULTR_API_KEY='your_key_here'")
        return 1
    
    print("=" * 60)
    print("Vultr Full Data Collection Test")
    print("=" * 60)
    
    try:
        print("\n🚀 Starting data collection...")
        metrics = collect_vultr_metrics(api_key)
        
        print("\n✅ Collection completed successfully!")
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 COLLECTED METRICS")
        print("=" * 60)
        
        account = metrics.get("account", {})
        print(f"\n💰 Account:")
        print(f"   Balance: ${account.get('balance', 0):.2f}")
        print(f"   Pending: ${account.get('pending_charges', 0):.2f}")
        
        instances = metrics.get("instances", [])
        print(f"\n🖥️  Instances: {len(instances)} total")
        
        gpu_instances = [i for i in instances if i.get("is_gpu")]
        cpu_instances = [i for i in instances if not i.get("is_gpu")]
        print(f"   - GPU: {len(gpu_instances)}")
        print(f"   - CPU: {len(cpu_instances)}")
        
        if instances:
            print(f"\n   Instance Details:")
            for i, inst in enumerate(instances[:5], 1):  # Show first 5
                print(f"   {i}. {inst.get('label', 'N/A')} ({inst.get('plan', 'N/A')})")
                print(f"      Status: {inst.get('status')} / {inst.get('power_status')}")
                print(f"      Cost: ${inst.get('monthly_cost', 0):.2f}/mo")
        
        analysis = metrics.get("cost_analysis", {})
        print(f"\n💵 Cost Analysis:")
        print(f"   Monthly Spend: ${analysis.get('current_monthly_spend', 0):.2f}")
        
        breakdown = analysis.get("cost_breakdown", {})
        print(f"   - GPU: ${breakdown.get('gpu_cost', 0):.2f} ({breakdown.get('gpu_percentage', 0):.1f}%)")
        print(f"   - CPU: ${breakdown.get('cpu_cost', 0):.2f}")
        
        waste = analysis.get("waste_analysis", {})
        print(f"\n🗑️  Waste Identified:")
        print(f"   Idle Instances: {waste.get('idle_instances', 0)}")
        print(f"   Idle Cost: ${waste.get('idle_cost', 0):.2f}/mo")
        if waste.get('idle_percentage', 0) > 0:
            print(f"   Waste: {waste.get('idle_percentage', 0):.1f}% of total spend")
        
        recommendations = analysis.get("recommendations", [])
        print(f"\n💡 Recommendations: {len(recommendations)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"      Savings: ${rec['estimated_savings']:.2f}/mo (confidence: {rec['confidence']*100:.0f}%)")
        
        total_savings = analysis.get("total_estimated_savings", 0)
        savings_pct = analysis.get("savings_percentage", 0)
        print(f"\n💰 Total Potential Savings:")
        print(f"   ${total_savings:.2f}/mo ({savings_pct:.1f}%)")
        
        # Save to file
        output_file = "vultr_metrics.json"
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        print(f"\n💾 Full metrics saved to: {output_file}")
        
        print("\n" + "=" * 60)
        print("✅ COLLECTION TEST PASSED")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
