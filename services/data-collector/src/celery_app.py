"""
Celery Application Configuration
Phase 6.2: Scheduled Collection
"""
from celery import Celery
from celery.schedules import crontab
import logging

from .config import config

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "data_collector",
    broker=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}",
    backend=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}",
    include=["src.tasks"]
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster"
    },
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Beat schedule (every 15 minutes) - Phase 6.5 Multi-Cloud
    beat_schedule={
        # Vultr - All data types
        "collect-vultr-all-every-15-minutes": {
            "task": "src.tasks.scheduled_collection_task",
            "schedule": crontab(minute="*/15"),
            "args": ("vultr", ["cost", "performance", "resource", "application"]),
            "options": {"expires": 60 * 10}
        },
        # RunPod - Cost, Performance, Resource
        "collect-runpod-all-every-15-minutes": {
            "task": "src.tasks.scheduled_collection_task",
            "schedule": crontab(minute="*/15"),
            "args": ("runpod", ["cost", "performance", "resource"]),
            "options": {"expires": 60 * 10}
        },
        # AWS - Cost, Performance, Resource
        "collect-aws-all-every-15-minutes": {
            "task": "src.tasks.scheduled_collection_task",
            "schedule": crontab(minute="*/15"),
            "args": ("aws", ["cost", "performance", "resource"]),
            "options": {"expires": 60 * 10}
        },
        # GCP - Cost, Performance, Resource
        "collect-gcp-all-every-15-minutes": {
            "task": "src.tasks.scheduled_collection_task",
            "schedule": crontab(minute="*/15"),
            "args": ("gcp", ["cost", "performance", "resource"]),
            "options": {"expires": 60 * 10}
        },
        # Azure - Cost, Performance, Resource
        "collect-azure-all-every-15-minutes": {
            "task": "src.tasks.scheduled_collection_task",
            "schedule": crontab(minute="*/15"),
            "args": ("azure", ["cost", "performance", "resource"]),
            "options": {"expires": 60 * 10}
        },
    },
    
    # Worker settings
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,
)

logger.info("Celery app configured successfully")
