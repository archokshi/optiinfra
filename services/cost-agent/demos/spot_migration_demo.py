"""
Interactive demo script for PILOT-05 Spot Migration.
Run this to demonstrate the complete end-to-end workflow.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflows.spot_migration import run_spot_migration_demo


def main():
    """Run the spot migration demo"""
    print("\n" + "=" * 80)
    print("OPTIINFRA PILOT-05: SPOT MIGRATION DEMO")
    print("=" * 80)
    print("\nThis demo will:")
    print("1. Analyze 10 EC2 instances")
    print("2. Identify spot migration opportunities")
    print("3. Coordinate with Performance, Resource, and Application agents")
    print("4. Execute gradual migration (10% → 50% → 100%)")
    print("5. Monitor quality during migration")
    print("6. Report final savings (30-40% cost reduction)")
    print("\n" + "=" * 80)
    
    input("\nPress ENTER to start the demo...")
    
    try:
        # Run the workflow
        result = run_spot_migration_demo(customer_id="demo-customer-001")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Results:")
        print(f"  - EC2 Instances Analyzed: {len(result.get('ec2_instances', []))}")
        print(f"  - Spot Opportunities: {len(result.get('spot_opportunities', []))}")
        print(f"  - Monthly Savings: ${result.get('final_savings', 0):.2f}")
        
        if result.get('execution_100'):
            success_rate = result['execution_100']['success_rate'] * 100
            print(f"  - Migration Success Rate: {success_rate:.1f}%")
        
        if result.get('quality_current'):
            degradation = result['quality_current']['degradation_percentage']
            acceptable = result['quality_current']['acceptable']
            status = "✅ ACCEPTABLE" if acceptable else "❌ UNACCEPTABLE"
            print(f"  - Quality Degradation: {degradation:.1f}% {status}")
        
        print(f"\n🎯 Status: {result.get('workflow_status', 'unknown').upper()}")
        print(f"💰 Estimated Annual Savings: ${result.get('final_savings', 0) * 12:.2f}")
        print("\n" + "=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
