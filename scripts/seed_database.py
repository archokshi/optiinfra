"""Seed database with test data"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.config import settings
from shared.database.seeds.core_seed import seed_core_data

# Create engine and session
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    # Seed data
    result = seed_core_data(session)
    print("\n✅ Seed data loaded successfully!")
    print(f"   - Customers: {len(result['customers'])}")
    print(f"   - Agents: {len(result['agents'])}")
    print(f"   - Events: {len(result['events'])}")
    print(f"   - Recommendations: {len(result['recommendations'])}")
except Exception as e:
    print(f"\n❌ Error seeding database: {e}")
    session.rollback()
    raise
finally:
    session.close()
