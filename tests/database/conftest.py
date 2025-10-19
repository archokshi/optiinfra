"""
Test fixtures for database tests.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.database.models.core import Base
from shared.config import settings


@pytest.fixture(scope="function")
def db_engine():
    """
    Create a PostgreSQL engine for testing.
    
    Uses the actual PostgreSQL database for full feature compatibility.
    """
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for testing.
    """
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def db_session_postgres():
    """
    Create a database session using actual PostgreSQL.
    Only use this for tests that specifically need PostgreSQL features.
    """
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Rollback any changes
    session.rollback()
    session.close()
