"""Check what tables exist in the database"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from shared.config import settings

engine = create_engine(settings.database_url)
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n📊 Database Tables ({len(tables)} total):")
if tables:
    for table in sorted(tables):
        print(f"  ✓ {table}")
else:
    print("  ⚠️  No tables found!")
