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
    Tables should already exist from migrations.
    """
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a database session for testing with transaction rollback.
    
    Each test runs in a transaction that is rolled back after the test,
    ensuring test isolation without recreating tables.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


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
