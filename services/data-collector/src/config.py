"""
Configuration for Data Collector Service
"""
import os
from typing import Optional


class Config:
    """Data Collector Service Configuration"""
    
    # Service Configuration
    SERVICE_NAME = "data-collector"
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8005"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # ============================================
    # Big 3 Cloud Providers (Dedicated Collectors)
    # ============================================
    
    # AWS Credentials
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # GCP Credentials
    GCP_SERVICE_ACCOUNT_JSON = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
    
    # Azure Credentials
    AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    
    # ============================================
    # Generic Collector - GPU Clouds
    # ============================================
    
    # Vultr
    VULTR_ENABLED = os.getenv("VULTR_ENABLED", "false").lower() == "true"
    VULTR_API_KEY = os.getenv("VULTR_API_KEY", "")
    VULTR_API_URL = os.getenv("VULTR_API_URL", "https://api.vultr.com")
    VULTR_PROMETHEUS_URL = os.getenv("VULTR_PROMETHEUS_URL", "")
    VULTR_DCGM_URL = os.getenv("VULTR_DCGM_URL", "")
    
    # RunPod
    RUNPOD_ENABLED = os.getenv("RUNPOD_ENABLED", "false").lower() == "true"
    RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
    RUNPOD_GRAPHQL_URL = os.getenv("RUNPOD_GRAPHQL_URL", "https://api.runpod.io/graphql")
    RUNPOD_REST_URL = os.getenv("RUNPOD_REST_URL", "https://rest.runpod.io/v1")
    RUNPOD_SERVERLESS_URL = os.getenv("RUNPOD_SERVERLESS_URL", "https://api.runpod.ai/v2")
    RUNPOD_API_URL = os.getenv("RUNPOD_API_URL", RUNPOD_GRAPHQL_URL)
    RUNPOD_PROMETHEUS_URL = os.getenv("RUNPOD_PROMETHEUS_URL", "")
    RUNPOD_DCGM_URL = os.getenv("RUNPOD_DCGM_URL", "")
    RUNPOD_COLLECTION_INTERVAL_SECONDS = int(os.getenv("RUNPOD_COLLECTION_INTERVAL_SECONDS", "300"))
    RUNPOD_HEALTH_POLL_SECONDS = int(os.getenv("RUNPOD_HEALTH_POLL_SECONDS", "120"))
    RUNPOD_JOB_RETENTION_DAYS = int(os.getenv("RUNPOD_JOB_RETENTION_DAYS", "90"))
    
    # Lambda Labs
    LAMBDA_LABS_ENABLED = os.getenv("LAMBDA_LABS_ENABLED", "false").lower() == "true"
    LAMBDA_LABS_API_KEY = os.getenv("LAMBDA_LABS_API_KEY", "")
    LAMBDA_LABS_API_URL = os.getenv("LAMBDA_LABS_API_URL", "https://cloud.lambdalabs.com/api/v1")
    LAMBDA_LABS_PROMETHEUS_URL = os.getenv("LAMBDA_LABS_PROMETHEUS_URL", "")
    LAMBDA_LABS_DCGM_URL = os.getenv("LAMBDA_LABS_DCGM_URL", "")
    
    # CoreWeave
    COREWEAVE_ENABLED = os.getenv("COREWEAVE_ENABLED", "false").lower() == "true"
    COREWEAVE_API_KEY = os.getenv("COREWEAVE_API_KEY", "")
    COREWEAVE_API_URL = os.getenv("COREWEAVE_API_URL", "")
    COREWEAVE_PROMETHEUS_URL = os.getenv("COREWEAVE_PROMETHEUS_URL", "")
    COREWEAVE_DCGM_URL = os.getenv("COREWEAVE_DCGM_URL", "")
    
    # Paperspace
    PAPERSPACE_ENABLED = os.getenv("PAPERSPACE_ENABLED", "false").lower() == "true"
    PAPERSPACE_API_KEY = os.getenv("PAPERSPACE_API_KEY", "")
    PAPERSPACE_API_URL = os.getenv("PAPERSPACE_API_URL", "https://api.paperspace.io")
    PAPERSPACE_PROMETHEUS_URL = os.getenv("PAPERSPACE_PROMETHEUS_URL", "")
    PAPERSPACE_DCGM_URL = os.getenv("PAPERSPACE_DCGM_URL", "")
    
    # ============================================
    # Generic Collector - General Compute
    # ============================================
    
    # DigitalOcean
    DIGITALOCEAN_ENABLED = os.getenv("DIGITALOCEAN_ENABLED", "false").lower() == "true"
    DIGITALOCEAN_API_KEY = os.getenv("DIGITALOCEAN_API_KEY", "")
    DIGITALOCEAN_API_URL = os.getenv("DIGITALOCEAN_API_URL", "https://api.digitalocean.com")
    DIGITALOCEAN_PROMETHEUS_URL = os.getenv("DIGITALOCEAN_PROMETHEUS_URL", "")
    
    # Linode
    LINODE_ENABLED = os.getenv("LINODE_ENABLED", "false").lower() == "true"
    LINODE_API_KEY = os.getenv("LINODE_API_KEY", "")
    LINODE_API_URL = os.getenv("LINODE_API_URL", "https://api.linode.com")
    LINODE_PROMETHEUS_URL = os.getenv("LINODE_PROMETHEUS_URL", "")
    
    # Hetzner
    HETZNER_ENABLED = os.getenv("HETZNER_ENABLED", "false").lower() == "true"
    HETZNER_API_KEY = os.getenv("HETZNER_API_KEY", "")
    HETZNER_API_URL = os.getenv("HETZNER_API_URL", "https://api.hetzner.cloud")
    HETZNER_PROMETHEUS_URL = os.getenv("HETZNER_PROMETHEUS_URL", "")
    
    # OVHcloud
    OVH_ENABLED = os.getenv("OVH_ENABLED", "false").lower() == "true"
    OVH_API_KEY = os.getenv("OVH_API_KEY", "")
    OVH_API_URL = os.getenv("OVH_API_URL", "https://api.ovh.com")
    OVH_PROMETHEUS_URL = os.getenv("OVH_PROMETHEUS_URL", "")
    
    # ============================================
    # Generic Collector - Self-Hosted
    # ============================================
    
    # On-Premises
    ON_PREMISES_ENABLED = os.getenv("ON_PREMISES_ENABLED", "false").lower() == "true"
    ON_PREMISES_PROMETHEUS_URL = os.getenv("ON_PREMISES_PROMETHEUS_URL", "")
    ON_PREMISES_DCGM_URL = os.getenv("ON_PREMISES_DCGM_URL", "")
    
    # Kubernetes
    KUBERNETES_ENABLED = os.getenv("KUBERNETES_ENABLED", "false").lower() == "true"
    KUBERNETES_API_KEY = os.getenv("KUBERNETES_API_KEY", "")
    KUBERNETES_API_URL = os.getenv("KUBERNETES_API_URL", "https://kubernetes.default.svc")
    KUBERNETES_PROMETHEUS_URL = os.getenv("KUBERNETES_PROMETHEUS_URL", "")
    KUBERNETES_DCGM_URL = os.getenv("KUBERNETES_DCGM_URL", "")
    
    # Docker
    DOCKER_ENABLED = os.getenv("DOCKER_ENABLED", "false").lower() == "true"
    DOCKER_API_URL = os.getenv("DOCKER_API_URL", "http://localhost:2375")
    DOCKER_PROMETHEUS_URL = os.getenv("DOCKER_PROMETHEUS_URL", "")
    
    # Database Configuration
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    CLICKHOUSE_HTTP_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
    CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "optiinfra")
    CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
    
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "optiinfra")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Collection Configuration
    COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "900"))  # 15 minutes in seconds
    COLLECTION_INTERVAL_MINUTES = int(os.getenv("COLLECTION_INTERVAL_MINUTES", "15"))
    COLLECTION_TIMEOUT_SECONDS = int(os.getenv("COLLECTION_TIMEOUT_SECONDS", "300"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "60"))  # seconds
    DEFAULT_CUSTOMER_ID = os.getenv("DEFAULT_CUSTOMER_ID", "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")  
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_postgres_url(cls) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = []
        
        if not cls.VULTR_API_KEY:
            required.append("VULTR_API_KEY")
        
        if required:
            raise ValueError(f"Missing required configuration: {', '.join(required)}")
        
        return True


config = Config()
