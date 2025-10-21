#!/usr/bin/env python3
"""
Example usage of shared utilities

Demonstrates how to use the shared utilities in agents.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import settings
from shared.logging import setup_logger
from shared.database import initialize_all_databases, get_postgres_cursor
from shared.utils import retry, measure_time, validate_required, ValidationError


# Setup logger
logger = setup_logger('example_agent', level='INFO', format_type='text')


@retry(max_attempts=3, delay=1.0)
@measure_time('database_query')
def fetch_data_from_db():
    """Example function with retry and timing"""
    logger.info("Fetching data from database...")
    
    try:
        with get_postgres_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM agents")
            result = cursor.fetchone()
            logger.info(f"Found {result[0]} agents")
            return result[0]
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise


def validate_input(agent_name: str, agent_type: str):
    """Example validation function"""
    try:
        validate_required(agent_name, "agent_name")
        validate_required(agent_type, "agent_type")
        logger.info(f"Validation passed for agent: {agent_name}")
        return True
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        return False


def main():
    """Main example function"""
    logger.info("=" * 60)
    logger.info("SHARED UTILITIES USAGE EXAMPLE")
    logger.info("=" * 60)
    
    # 1. Configuration
    logger.info("\n1. Configuration:")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   PostgreSQL URL: {settings.database.postgres_url}")
    logger.info(f"   Orchestrator URL: {settings.orchestrator.url}")
    logger.info(f"   Mock Cloud URL: {settings.mock_cloud.url}")
    
    # 2. Validation
    logger.info("\n2. Validation:")
    validate_input("cost-agent", "cost")
    validate_input("", "cost")  # This will fail
    
    # 3. Database connection (commented out - requires running services)
    logger.info("\n3. Database Connection:")
    logger.info("   (Skipping - requires running PostgreSQL)")
    # try:
    #     initialize_all_databases()
    #     count = fetch_data_from_db()
    #     logger.info(f"   Successfully fetched data: {count} agents")
    # except Exception as e:
    #     logger.error(f"   Database connection failed: {e}")
    
    # 4. Metrics
    logger.info("\n4. Performance Metrics:")
    from shared.utils import metrics_collector
    summary = metrics_collector.get_summary()
    for metric_name, stats in summary.items():
        logger.info(f"   {metric_name}: {stats}")
    
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE COMPLETED")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
