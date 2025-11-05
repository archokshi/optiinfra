"""
Celery Tasks for Data Collection
Phase 6.2: Scheduled Collection
Phase 6.4: Enhanced with Performance & Resource Collection
Phase 6.5: Multi-Cloud + Application Quality Monitoring
"""
from celery import Task
from typing import List
import logging
from datetime import datetime
import os

from .celery_app import celery_app
from .config import config
from .collectors import (
    # Application
    VultrApplicationCollector,
    # AWS (Dedicated)
    AWSCostCollector, AWSPerformanceCollector, AWSResourceCollector,
    # GCP (Dedicated)
    GCPCostCollector, GCPPerformanceCollector, GCPResourceCollector,
    # Azure (Dedicated)
    AzureCostCollector, AzurePerformanceCollector, AzureResourceCollector
)
from .collectors.generic_collector import GenericCollector
from .storage import ClickHouseWriter, PostgresWriter, RedisPublisher
from .credential_manager import CredentialManager
from .provider_config import build_generic_collector_config, is_generic_provider

logger = logging.getLogger(__name__)


class CollectionTask(Task):
    """Base task with error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Exception info: {einfo}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(
    base=CollectionTask,
    bind=True,
    name="src.tasks.collect_data_task",
    max_retries=3,
    default_retry_delay=60
)
def collect_data_task(self, customer_id: str, provider: str, data_types: List[str]):
    """
    Celery task to collect data from a cloud provider
    
    Args:
        customer_id: Customer identifier
        provider: Cloud provider (vultr, aws, gcp, azure)
        data_types: List of data types to collect (cost, performance, resource, application)
    
    Returns:
        dict: Collection result
    """
    task_id = self.request.id
    started_at = datetime.now()
    
    logger.info(f"[{task_id}] Starting collection for customer: {customer_id}, provider: {provider}, data_types: {data_types}")
    
    try:
        # Initialize credential manager and storage writers
        credential_manager = CredentialManager()
        clickhouse_writer = ClickHouseWriter()
        postgres_writer = PostgresWriter()
        redis_publisher = RedisPublisher()
        
        total_records = 0
        
        # Process each data type
        for data_type in data_types:
            if data_type == "cost":
                # Instantiate the appropriate collector
                collector = None
                
                if is_generic_provider(provider):
                    creds = credential_manager.get_credential(customer_id, provider) or {}
                    try:
                        generic_config = build_generic_collector_config(
                            provider=provider,
                            customer_id=customer_id,
                            credentials=creds,
                        )
                    except ValueError as error:
                        raise ValueError(
                            f"{error}. Please add credentials in the dashboard or set provider environment variables."
                        ) from error
                    collector = GenericCollector(generic_config)
                
                elif provider == "aws":
                    # Get credentials from database
                    creds = credential_manager.get_credential(customer_id, provider)
                    if not creds:
                        raise ValueError(f"No AWS credentials found for customer {customer_id}. Please add credentials in the dashboard.")
                    
                    collector = AWSCostCollector(
                        access_key_id=creds.get('access_key_id'),
                        secret_access_key=creds.get('secret_access_key'),
                        customer_id=customer_id
                    )
                
                elif provider == "gcp":
                    # Get credentials from database
                    creds = credential_manager.get_credential(customer_id, provider)
                    if not creds:
                        raise ValueError(f"No GCP credentials found for customer {customer_id}. Please add credentials in the dashboard.")
                    
                    collector = GCPCostCollector(
                        service_account_json=creds.get('service_account_json'),
                        customer_id=customer_id
                    )
                
                elif provider == "azure":
                    # Get credentials from database
                    creds = credential_manager.get_credential(customer_id, provider)
                    if not creds:
                        raise ValueError(f"No Azure credentials found for customer {customer_id}. Please add credentials in the dashboard.")
                    
                    collector = AzureCostCollector(
                        subscription_id=creds.get('subscription_id'),
                        tenant_id=creds.get('tenant_id'),
                        client_id=creds.get('client_id'),
                        client_secret=creds.get('client_secret'),
                        customer_id=customer_id
                    )
                
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
                
                # Collect data
                logger.info(f"[{task_id}] Collecting {data_type} data from {provider}")
                result = collector.collect()
                
                # Write to ClickHouse
                if result.success and hasattr(collector, 'get_collected_metrics'):
                    metrics = collector.get_collected_metrics()
                    if metrics:
                        records_written = clickhouse_writer.write_cost_metrics(metrics)
                        total_records += records_written
                        logger.info(f"[{task_id}] Wrote {records_written} cost metrics to ClickHouse")
                
                # Publish to Redis
                if result.success:
                    redis_publisher.publish_data_updated(
                        customer_id=customer_id,
                        provider=provider,
                        data_type=data_type,
                        records_count=result.records_collected
                    )
            
            elif data_type == "performance":
                # Performance data collection (Phase 6.5 Multi-Cloud)
                collector = None
                
                if is_generic_provider(provider):
                    creds = credential_manager.get_credential(customer_id, provider) or {}
                    try:
                        generic_config = build_generic_collector_config(
                            provider=provider,
                            customer_id=customer_id,
                            credentials=creds,
                        )
                    except ValueError as error:
                        raise ValueError(
                            f"{error}. Please add credentials in the dashboard or set provider environment variables."
                        ) from error
                    collector = GenericCollector(generic_config)
                else:
                    creds = credential_manager.get_credential(customer_id, provider)
                    if not creds:
                        raise ValueError(f"No {provider} credentials found for customer {customer_id}")

                    if provider == "aws":
                        collector = AWSPerformanceCollector(
                            access_key_id=creds.get('access_key_id'),
                            secret_access_key=creds.get('secret_access_key'),
                            customer_id=customer_id,
                            region=creds.get('region', 'us-east-1')
                        )
                    elif provider == "gcp":
                        collector = GCPPerformanceCollector(
                            service_account_json=creds.get('service_account_json'),
                            customer_id=customer_id,
                            project_id=creds.get('project_id')
                        )
                    elif provider == "azure":
                        collector = AzurePerformanceCollector(
                            subscription_id=creds.get('subscription_id'),
                            tenant_id=creds.get('tenant_id'),
                            client_id=creds.get('client_id'),
                            client_secret=creds.get('client_secret'),
                            customer_id=customer_id
                        )
                    else:
                        logger.warning(f"[{task_id}] Performance collection not supported for {provider}")
                        continue
                
                # Collect data
                logger.info(f"[{task_id}] Collecting {data_type} data from {provider}")
                result = collector.collect()
                
                # Write to ClickHouse
                if result.success:
                    metrics = collector.get_metrics()
                    if metrics:
                        records_written = clickhouse_writer.write_performance_metrics(metrics)
                        total_records += records_written
                        logger.info(f"[{task_id}] Wrote {records_written} performance metrics to ClickHouse")
                
                # Publish to Redis
                if result.success:
                    redis_publisher.publish_data_updated(
                        customer_id=customer_id,
                        provider=provider,
                        data_type=data_type,
                        records_count=result.records_collected
                    )
            
            elif data_type == "resource":
                # Resource data collection (Phase 6.5 Multi-Cloud)
                collector = None
                
                if is_generic_provider(provider):
                    creds = credential_manager.get_credential(customer_id, provider) or {}
                    try:
                        generic_config = build_generic_collector_config(
                            provider=provider,
                            customer_id=customer_id,
                            credentials=creds,
                        )
                    except ValueError as error:
                        raise ValueError(
                            f"{error}. Please add credentials in the dashboard or set provider environment variables."
                        ) from error
                    collector = GenericCollector(generic_config)
                else:
                    creds = credential_manager.get_credential(customer_id, provider)
                    if not creds:
                        raise ValueError(f"No {provider} credentials found for customer {customer_id}")

                    if provider == "aws":
                        collector = AWSResourceCollector(
                            access_key_id=creds.get('access_key_id'),
                            secret_access_key=creds.get('secret_access_key'),
                            customer_id=customer_id,
                            region=creds.get('region', 'us-east-1')
                        )
                    elif provider == "gcp":
                        collector = GCPResourceCollector(
                            service_account_json=creds.get('service_account_json'),
                            customer_id=customer_id,
                            project_id=creds.get('project_id')
                        )
                    elif provider == "azure":
                        collector = AzureResourceCollector(
                            subscription_id=creds.get('subscription_id'),
                            tenant_id=creds.get('tenant_id'),
                            client_id=creds.get('client_id'),
                            client_secret=creds.get('client_secret'),
                            customer_id=customer_id
                        )
                    else:
                        logger.warning(f"[{task_id}] Resource collection not supported for {provider}")
                        continue
                
                # Collect data
                logger.info(f"[{task_id}] Collecting {data_type} data from {provider}")
                result = collector.collect()
                
                # Write to ClickHouse
                if result.success:
                    metrics = collector.get_metrics()
                    if metrics:
                        records_written = clickhouse_writer.write_resource_metrics(metrics)
                        total_records += records_written
                        logger.info(f"[{task_id}] Wrote {records_written} resource metrics to ClickHouse")
                
                # Publish to Redis
                if result.success:
                    redis_publisher.publish_data_updated(
                        customer_id=customer_id,
                        provider=provider,
                        data_type=data_type,
                        records_count=result.records_collected
                    )
            
            elif data_type == "application":
                # Application quality monitoring (Phase 6.5)
                collector = None
                creds = credential_manager.get_credential(customer_id, provider)
                if not creds:
                    raise ValueError(f"No {provider} credentials found for customer {customer_id}")
                
                # Get Groq API key from environment
                groq_api_key = os.getenv('GROQ_API_KEY', '')
                if not groq_api_key:
                    logger.warning(f"[{task_id}] GROQ_API_KEY not set, skipping application collection")
                    continue
                
                if provider == "vultr":
                    collector = VultrApplicationCollector(
                        api_key=creds.get('api_key'),
                        customer_id=customer_id,
                        groq_api_key=groq_api_key
                    )
                else:
                    logger.warning(f"[{task_id}] Application collection not yet implemented for {provider}")
                    continue
                
                # Collect data
                logger.info(f"[{task_id}] Collecting {data_type} data from {provider}")
                result = collector.collect()
                
                # Write to ClickHouse
                if result.success:
                    metrics = collector.get_metrics()
                    if metrics:
                        records_written = clickhouse_writer.write_application_metrics(metrics)
                        total_records += records_written
                        logger.info(f"[{task_id}] Wrote {records_written} application metrics to ClickHouse")
                
                # Publish to Redis
                if result.success:
                    redis_publisher.publish_data_updated(
                        customer_id=customer_id,
                        provider=provider,
                        data_type=data_type,
                        records_count=result.records_collected
                    )
            
            else:
                logger.warning(f"[{task_id}] Data type '{data_type}' not yet implemented")
        
        completed_at = datetime.now()
        
        # Write collection history
        postgres_writer.write_collection_history(
            customer_id=customer_id,
            provider=provider,
            task_id=task_id,
            status="success",
            started_at=started_at,
            completed_at=completed_at,
            metrics_collected=total_records,
            error_message=None
        )
        
        # Publish completion status
        redis_publisher.publish_collection_status(
            task_id=task_id,
            status="completed",
            message=f"Collected {total_records} records"
        )
        
        # Close connections
        clickhouse_writer.close()
        postgres_writer.close()
        redis_publisher.close()
        
        logger.info(f"[{task_id}] Collection completed successfully. Total records: {total_records}")
        
        return {
            "task_id": task_id,
            "customer_id": customer_id,
            "provider": provider,
            "data_types": data_types,
            "records_collected": total_records,
            "status": "success",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"[{task_id}] Collection failed: {str(e)}", exc_info=True)
        
        # Write failed collection history
        try:
            postgres_writer = PostgresWriter()
            postgres_writer.write_collection_history(
                customer_id=customer_id,
                provider=provider,
                task_id=task_id,
                status="failed",
                started_at=started_at,
                completed_at=datetime.now(),
                metrics_collected=0,
                error_message=str(e)
            )
            postgres_writer.close()
        except Exception as write_error:
            logger.error(f"Failed to write error to history: {write_error}")
        
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    base=CollectionTask,
    bind=True,
    name="src.tasks.scheduled_collection_task"
)
def scheduled_collection_task(self, provider: str, data_types: List[str]):
    """
    Scheduled task that collects data for all customers
    
    This task runs every 15 minutes and triggers collection for all active customers
    
    Args:
        provider: Cloud provider
        data_types: List of data types to collect
    
    Returns:
        dict: Summary of triggered collections
    """
    task_id = self.request.id
    logger.info(f"[{task_id}] Starting scheduled collection for provider: {provider}, data_types: {data_types}")
    
    # TODO: Get list of active customers from database
    # For now, use a default customer ID from config
    customers = [config.DEFAULT_CUSTOMER_ID] if hasattr(config, 'DEFAULT_CUSTOMER_ID') else []
    
    if not customers:
        logger.warning(f"[{task_id}] No customers configured for scheduled collection")
        return {
            "task_id": task_id,
            "provider": provider,
            "customers_triggered": 0,
            "status": "no_customers"
        }
    
    triggered_tasks = []
    
    for customer_id in customers:
        try:
            # Trigger async collection task for each customer
            result = collect_data_task.delay(customer_id, provider, data_types)
            triggered_tasks.append({
                "customer_id": customer_id,
                "task_id": result.id,
                "status": "queued"
            })
            logger.info(f"[{task_id}] Triggered collection task {result.id} for customer {customer_id}")
        except Exception as e:
            logger.error(f"[{task_id}] Failed to trigger collection for customer {customer_id}: {e}")
            triggered_tasks.append({
                "customer_id": customer_id,
                "task_id": None,
                "status": "failed",
                "error": str(e)
            })
    
    logger.info(f"[{task_id}] Scheduled collection completed. Triggered {len(triggered_tasks)} tasks")
    
    return {
        "task_id": task_id,
        "provider": provider,
        "data_types": data_types,
        "customers_triggered": len(triggered_tasks),
        "triggered_tasks": triggered_tasks,
        "status": "success"
    }


@celery_app.task(name="src.tasks.health_check_task")
def health_check_task():
    """Simple health check task to verify Celery is working"""
    logger.info("Health check task executed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Celery worker is operational"
    }
