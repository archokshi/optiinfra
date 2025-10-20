"""Clean up workflow enum types if they exist"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from shared.config import settings

engine = create_engine(settings.database_url)

print("🧹 Cleaning up existing workflow enum types...")

with engine.connect() as conn:
    try:
        conn.execute(text('DROP TYPE IF EXISTS workflow_type CASCADE'))
        print("  ✓ Dropped workflow_type")
    except Exception as e:
        print(f"  ⚠️  workflow_type: {e}")
    
    try:
        conn.execute(text('DROP TYPE IF EXISTS workflow_status CASCADE'))
        print("  ✓ Dropped workflow_status")
    except Exception as e:
        print(f"  ⚠️  workflow_status: {e}")
    
    try:
        conn.execute(text('DROP TYPE IF EXISTS step_status CASCADE'))
        print("  ✓ Dropped step_status")
    except Exception as e:
        print(f"  ⚠️  step_status: {e}")
    
    try:
        conn.execute(text('DROP TYPE IF EXISTS artifact_type CASCADE'))
        print("  ✓ Dropped artifact_type")
    except Exception as e:
        print(f"  ⚠️  artifact_type: {e}")
    
    conn.commit()

print("✅ Cleanup complete!")
