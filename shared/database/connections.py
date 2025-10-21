"""
Shared Database Connection Manager

Provides connection pooling and management for all databases.
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from clickhouse_driver import Client as ClickHouseClient
from qdrant_client import QdrantClient
import redis

logger = logging.getLogger(__name__)


class DatabaseConnections:
    """Manages database connections with connection pooling"""
    
    def __init__(self):
        self._postgres_pool: Optional[pool.ThreadedConnectionPool] = None
        self._clickhouse_client: Optional[ClickHouseClient] = None
        self._qdrant_client: Optional[QdrantClient] = None
        self._redis_client: Optional[redis.Redis] = None
    
    def initialize_postgres(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        min_connections: int = 1,
        max_connections: int = 10,
    ):
        """Initialize PostgreSQL connection pool"""
        host = host or os.getenv('POSTGRES_HOST', 'localhost')
        port = port or int(os.getenv('POSTGRES_PORT', '5432'))
        database = database or os.getenv('POSTGRES_DB', 'optiinfra')
        user = user or os.getenv('POSTGRES_USER', 'optiinfra')
        password = password or os.getenv('POSTGRES_PASSWORD', 'password')
        
        try:
            self._postgres_pool = pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            logger.info(f"PostgreSQL connection pool initialized: {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise
    
    def initialize_clickhouse(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        """Initialize ClickHouse client"""
        host = host or os.getenv('CLICKHOUSE_HOST', 'localhost')
        port = port or int(os.getenv('CLICKHOUSE_PORT', '8123'))
        database = database or os.getenv('CLICKHOUSE_DB', 'optiinfra')
        user = user or os.getenv('CLICKHOUSE_USER', 'default')
        password = password or os.getenv('CLICKHOUSE_PASSWORD', '')
        
        try:
            self._clickhouse_client = ClickHouseClient(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            logger.info(f"ClickHouse client initialized: {host}:{port}/{database}")
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse client: {e}")
            raise
    
    def initialize_qdrant(
        self,
        host: str = None,
        port: int = None,
        api_key: str = None,
    ):
        """Initialize Qdrant client"""
        host = host or os.getenv('QDRANT_HOST', 'localhost')
        port = port or int(os.getenv('QDRANT_PORT', '6333'))
        api_key = api_key or os.getenv('QDRANT_API_KEY')
        
        try:
            self._qdrant_client = QdrantClient(
                host=host,
                port=port,
                api_key=api_key,
            )
            logger.info(f"Qdrant client initialized: {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
    
    def initialize_redis(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
    ):
        """Initialize Redis client"""
        host = host or os.getenv('REDIS_HOST', 'localhost')
        port = port or int(os.getenv('REDIS_PORT', '6379'))
        db = db or int(os.getenv('REDIS_DB', '0'))
        password = password or os.getenv('REDIS_PASSWORD')
        
        try:
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )
            # Test connection
            self._redis_client.ping()
            logger.info(f"Redis client initialized: {host}:{port}/{db}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
    
    @contextmanager
    def get_postgres_connection(self):
        """Get PostgreSQL connection from pool (context manager)"""
        if not self._postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        conn = self._postgres_pool.getconn()
        try:
            yield conn
        finally:
            self._postgres_pool.putconn(conn)
    
    @contextmanager
    def get_postgres_cursor(self, commit: bool = True):
        """Get PostgreSQL cursor (context manager)"""
        with self.get_postgres_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    @property
    def clickhouse(self) -> ClickHouseClient:
        """Get ClickHouse client"""
        if not self._clickhouse_client:
            raise RuntimeError("ClickHouse client not initialized")
        return self._clickhouse_client
    
    @property
    def qdrant(self) -> QdrantClient:
        """Get Qdrant client"""
        if not self._qdrant_client:
            raise RuntimeError("Qdrant client not initialized")
        return self._qdrant_client
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis client"""
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")
        return self._redis_client
    
    def close_all(self):
        """Close all database connections"""
        if self._postgres_pool:
            self._postgres_pool.closeall()
            logger.info("PostgreSQL pool closed")
        
        if self._clickhouse_client:
            self._clickhouse_client.disconnect()
            logger.info("ClickHouse client closed")
        
        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis client closed")


# Global database connections instance
db_connections = DatabaseConnections()


# Convenience functions
def get_postgres_connection():
    """Get PostgreSQL connection (context manager)"""
    return db_connections.get_postgres_connection()


def get_postgres_cursor(commit: bool = True):
    """Get PostgreSQL cursor (context manager)"""
    return db_connections.get_postgres_cursor(commit=commit)


def get_clickhouse_client() -> ClickHouseClient:
    """Get ClickHouse client"""
    return db_connections.clickhouse


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client"""
    return db_connections.qdrant


def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    return db_connections.redis


def initialize_all_databases():
    """Initialize all database connections"""
    db_connections.initialize_postgres()
    db_connections.initialize_clickhouse()
    db_connections.initialize_qdrant()
    db_connections.initialize_redis()
    logger.info("All database connections initialized")
