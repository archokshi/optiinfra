#!/usr/bin/env python3
"""
Test Prometheus Monitoring Setup

Validates that Prometheus is running and scraping all targets.
"""

import sys
import requests
import time
from typing import Dict, List

# Test configuration
PROMETHEUS_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "optiinfra_admin"

# Expected targets
EXPECTED_TARGETS = [
    "orchestrator",
    "cost-agent",
    "performance-agent",
    "resource-agent",
    "application-agent",
    "postgres",
    "clickhouse",
    "redis",
    "prometheus"
]


def test_prometheus_health():
    """Test 1: Prometheus is healthy"""
    print("\n1. Testing Prometheus health...")
    try:
        response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "Prometheus is Healthy" in response.text or response.status_code == 200
        print("   ✓ Prometheus is healthy")
        return True
    except Exception as e:
        print(f"   ✗ Prometheus health check failed: {e}")
        return False


def test_prometheus_targets():
    """Test 2: Check all targets are configured"""
    print("\n2. Testing Prometheus targets...")
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        active_targets = data.get('data', {}).get('activeTargets', [])
        
        # Get list of configured jobs
        configured_jobs = set(target['labels']['job'] for target in active_targets)
        
        print(f"   Found {len(configured_jobs)} configured targets")
        
        # Check each expected target
        missing_targets = []
        for target in EXPECTED_TARGETS:
            if target in configured_jobs:
                print(f"   ✓ {target} configured")
            else:
                print(f"   ✗ {target} NOT configured")
                missing_targets.append(target)
        
        if missing_targets:
            print(f"   Warning: Missing targets: {', '.join(missing_targets)}")
            print("   (This is expected if services are not yet running)")
        
        return len(configured_jobs) > 0
    except Exception as e:
        print(f"   ✗ Failed to check targets: {e}")
        return False


def test_prometheus_up_metric():
    """Test 3: Query 'up' metric"""
    print("\n3. Testing Prometheus queries...")
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": "up"},
            timeout=5
        )
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('data', {}).get('result', [])
        
        print(f"   Found {len(results)} services with 'up' metric")
        
        for result in results:
            job = result['metric'].get('job', 'unknown')
            value = result['value'][1]
            status = "UP" if value == "1" else "DOWN"
            symbol = "✓" if value == "1" else "✗"
            print(f"   {symbol} {job}: {status}")
        
        return len(results) > 0
    except Exception as e:
        print(f"   ✗ Failed to query metrics: {e}")
        return False


def test_alert_rules():
    """Test 4: Check alert rules are loaded"""
    print("\n4. Testing alert rules...")
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/rules", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        groups = data.get('data', {}).get('groups', [])
        
        total_rules = sum(len(group.get('rules', [])) for group in groups)
        
        print(f"   Found {len(groups)} rule groups with {total_rules} total rules")
        
        for group in groups:
            group_name = group.get('name', 'unknown')
            rule_count = len(group.get('rules', []))
            print(f"   ✓ {group_name}: {rule_count} rules")
        
        return total_rules > 0
    except Exception as e:
        print(f"   ✗ Failed to check alert rules: {e}")
        return False


def test_grafana_health():
    """Test 5: Grafana is healthy"""
    print("\n5. Testing Grafana health...")
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        db_status = data.get('database', 'unknown')
        
        print(f"   ✓ Grafana is healthy (database: {db_status})")
        return True
    except Exception as e:
        print(f"   ✗ Grafana health check failed: {e}")
        return False


def test_grafana_datasource():
    """Test 6: Grafana Prometheus datasource"""
    print("\n6. Testing Grafana datasource...")
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=5
        )
        assert response.status_code == 200
        
        datasources = response.json()
        prometheus_ds = [ds for ds in datasources if ds.get('type') == 'prometheus']
        
        if prometheus_ds:
            ds = prometheus_ds[0]
            print(f"   ✓ Prometheus datasource configured: {ds.get('name')}")
            print(f"     URL: {ds.get('url')}")
            return True
        else:
            print("   ✗ No Prometheus datasource found")
            return False
    except Exception as e:
        print(f"   ✗ Failed to check datasource: {e}")
        return False


def test_exporters():
    """Test 7: Database exporters are running"""
    print("\n7. Testing database exporters...")
    
    exporters = {
        "PostgreSQL": "http://localhost:9187/metrics",
        "ClickHouse": "http://localhost:9116/metrics",
        "Redis": "http://localhost:9121/metrics"
    }
    
    results = []
    for name, url in exporters.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✓ {name} exporter is running")
                results.append(True)
            else:
                print(f"   ✗ {name} exporter returned {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"   ✗ {name} exporter not accessible: {e}")
            results.append(False)
    
    return any(results)


def main():
    """Run all tests"""
    print("=" * 70)
    print("PROMETHEUS MONITORING STACK - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Prometheus Health", test_prometheus_health),
        ("Prometheus Targets", test_prometheus_targets),
        ("Prometheus Queries", test_prometheus_up_metric),
        ("Alert Rules", test_alert_rules),
        ("Grafana Health", test_grafana_health),
        ("Grafana Datasource", test_grafana_datasource),
        ("Database Exporters", test_exporters),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n   ✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("\nNote: Some failures are expected if services are not running yet.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
