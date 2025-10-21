#!/usr/bin/env python3
"""Test configuration utilities"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

from shared.config import settings

print("=" * 60)
print("TESTING CONFIGURATION MODULE")
print("=" * 60)

# Test database config
print("\n1. Database Configuration:")
print(f"   PostgreSQL URL: {settings.database.postgres_url}")
print(f"   ClickHouse Host: {settings.database.clickhouse_host}")
print(f"   Qdrant Port: {settings.database.qdrant_port}")
print(f"   Redis DB: {settings.database.redis_db}")

# Test orchestrator config
print("\n2. Orchestrator Configuration:")
print(f"   URL: {settings.orchestrator.url}")

# Test mock cloud config
print("\n3. Mock Cloud Configuration:")
print(f"   URL: {settings.mock_cloud.url}")

# Test logging config
print("\n4. Logging Configuration:")
print(f"   Level: {settings.logging.level}")
print(f"   Format: {settings.logging.format}")

# Test agent config
print("\n5. Agent Configuration:")
print(f"   Name: {settings.agent.name}")
print(f"   Type: {settings.agent.agent_type}")
print(f"   Heartbeat Interval: {settings.agent.heartbeat_interval}s")

# Test environment
print("\n6. Environment:")
print(f"   Environment: {settings.environment}")
print(f"   Is Production: {settings.is_production}")
print(f"   Is Development: {settings.is_development}")
print(f"   Debug: {settings.debug}")

print("\n" + "=" * 60)
print("✅ CONFIGURATION MODULE TEST PASSED")
print("=" * 60)
