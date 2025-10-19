"""
Test fixtures for database tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.database.models.core import Base
from shared.config import settings


@pytest.fixture(scope="function")
def db_engine():
    """
    Create an in-memory SQLite engine for testing.
    
    Note: Some PostgreSQL-specific features won't work in SQLite,
    but basic CRUD operations will.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
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
