"""
Provider configuration metadata shared across the data-collector service.

This module centralizes information about supported cloud providers so both the
FastAPI application and Celery workers stay in sync. It also exposes helper
functions for working with generic providers that rely on the GenericCollector.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .collectors.generic_collector import GenericCollectorConfig
from .config import config

# Provider metadata ---------------------------------------------------------

# NOTE: Keys must be lowercase because callers normalize provider slugs.
SUPPORTED_PROVIDERS: Dict[str, Dict[str, Any]] = {
    # Dedicated collectors (Big 3)
    "aws": {
        "display_name": "AWS",
        "type": "dedicated",
        "category": "Big 3",
        "env_keys": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "requirements": [
            {"field": "access_key_id", "label": "Access Key ID", "required": True},
            {"field": "secret_access_key", "label": "Secret Access Key", "required": True},
            {"field": "session_token", "label": "Session Token", "required": False},
        ],
    },
    "gcp": {
        "display_name": "GCP",
        "type": "dedicated",
        "category": "Big 3",
        "env_keys": ["GCP_SERVICE_ACCOUNT_JSON", "GCP_PROJECT_ID"],
        "requirements": [
            {
                "field": "service_account_json",
                "label": "Service Account JSON",
                "required": True,
            },
        ],
    },
    "azure": {
        "display_name": "Azure",
        "type": "dedicated",
        "category": "Big 3",
        "env_keys": [
            "AZURE_SUBSCRIPTION_ID",
            "AZURE_TENANT_ID",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
        ],
        "requirements": [
            {"field": "subscription_id", "label": "Subscription ID", "required": True},
            {"field": "tenant_id", "label": "Tenant ID", "required": True},
            {"field": "client_id", "label": "Client ID", "required": True},
            {"field": "client_secret", "label": "Client Secret", "required": True},
        ],
    },
    # Generic collector (GPU clouds)
    "vultr": {
        "display_name": "Vultr",
        "type": "generic",
        "category": "GPU Cloud",
        "enabled_flag": "VULTR_ENABLED",
        "config_keys": {
            "api_key": "VULTR_API_KEY",
            "api_url": "VULTR_API_URL",
            "prometheus_url": "VULTR_PROMETHEUS_URL",
            "dcgm_url": "VULTR_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": False},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "runpod": {
        "display_name": "RunPod",
        "type": "generic",
        "category": "GPU Cloud",
        "enabled_flag": "RUNPOD_ENABLED",
        "config_keys": {
            "api_key": "RUNPOD_API_KEY",
            "api_url": "RUNPOD_API_URL",
            "prometheus_url": "RUNPOD_PROMETHEUS_URL",
            "dcgm_url": "RUNPOD_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": True},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "lambda_labs": {
        "display_name": "Lambda Labs",
        "type": "generic",
        "category": "GPU Cloud",
        "enabled_flag": "LAMBDA_LABS_ENABLED",
        "config_keys": {
            "api_key": "LAMBDA_LABS_API_KEY",
            "api_url": "LAMBDA_LABS_API_URL",
            "prometheus_url": "LAMBDA_LABS_PROMETHEUS_URL",
            "dcgm_url": "LAMBDA_LABS_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": True},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "coreweave": {
        "display_name": "CoreWeave",
        "type": "generic",
        "category": "GPU Cloud",
        "enabled_flag": "COREWEAVE_ENABLED",
        "config_keys": {
            "api_key": "COREWEAVE_API_KEY",
            "api_url": "COREWEAVE_API_URL",
            "prometheus_url": "COREWEAVE_PROMETHEUS_URL",
            "dcgm_url": "COREWEAVE_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": True},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "paperspace": {
        "display_name": "Paperspace",
        "type": "generic",
        "category": "GPU Cloud",
        "enabled_flag": "PAPERSPACE_ENABLED",
        "config_keys": {
            "api_key": "PAPERSPACE_API_KEY",
            "api_url": "PAPERSPACE_API_URL",
            "prometheus_url": "PAPERSPACE_PROMETHEUS_URL",
            "dcgm_url": "PAPERSPACE_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": True},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    # Generic collector (general compute)
    "digitalocean": {
        "display_name": "DigitalOcean",
        "type": "generic",
        "category": "General Compute",
        "enabled_flag": "DIGITALOCEAN_ENABLED",
        "config_keys": {
            "api_key": "DIGITALOCEAN_API_KEY",
            "api_url": "DIGITALOCEAN_API_URL",
            "prometheus_url": "DIGITALOCEAN_PROMETHEUS_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Token", "required": True},
        ],
    },
    "linode": {
        "display_name": "Linode",
        "type": "generic",
        "category": "General Compute",
        "enabled_flag": "LINODE_ENABLED",
        "config_keys": {
            "api_key": "LINODE_API_KEY",
            "api_url": "LINODE_API_URL",
            "prometheus_url": "LINODE_PROMETHEUS_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Token", "required": True},
        ],
    },
    "hetzner": {
        "display_name": "Hetzner",
        "type": "generic",
        "category": "General Compute",
        "enabled_flag": "HETZNER_ENABLED",
        "config_keys": {
            "api_key": "HETZNER_API_KEY",
            "api_url": "HETZNER_API_URL",
            "prometheus_url": "HETZNER_PROMETHEUS_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Token", "required": True},
        ],
    },
    "ovh": {
        "display_name": "OVHcloud",
        "type": "generic",
        "category": "General Compute",
        "enabled_flag": "OVH_ENABLED",
        "config_keys": {
            "api_key": "OVH_API_KEY",
            "api_url": "OVH_API_URL",
            "prometheus_url": "OVH_PROMETHEUS_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "API Key", "required": True},
        ],
    },
    # Generic collector (self-hosted)
    "on_premises": {
        "display_name": "On-Premises",
        "type": "generic",
        "category": "Self-Hosted",
        "enabled_flag": "ON_PREMISES_ENABLED",
        "config_keys": {
            "prometheus_url": "ON_PREMISES_PROMETHEUS_URL",
            "dcgm_url": "ON_PREMISES_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "kubernetes": {
        "display_name": "Kubernetes",
        "type": "generic",
        "category": "Self-Hosted",
        "enabled_flag": "KUBERNETES_ENABLED",
        "config_keys": {
            "api_key": "KUBERNETES_API_KEY",
            "api_url": "KUBERNETES_API_URL",
            "prometheus_url": "KUBERNETES_PROMETHEUS_URL",
            "dcgm_url": "KUBERNETES_DCGM_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_key", "label": "Bearer Token", "required": False},
            {"field": "api_url", "label": "API Server URL", "required": False},
            {"field": "dcgm_url", "label": "DCGM Metrics URL", "required": False},
        ],
    },
    "docker": {
        "display_name": "Docker",
        "type": "generic",
        "category": "Self-Hosted",
        "enabled_flag": "DOCKER_ENABLED",
        "config_keys": {
            "api_url": "DOCKER_API_URL",
            "prometheus_url": "DOCKER_PROMETHEUS_URL",
        },
        "requirements": [
            {"field": "prometheus_url", "label": "Prometheus URL", "required": True},
            {"field": "api_url", "label": "Docker API URL", "required": False},
        ],
    },
}


# Helper functions ----------------------------------------------------------

def _metadata_for(provider: str) -> Optional[Dict[str, Any]]:
    return SUPPORTED_PROVIDERS.get(provider.lower())


def is_generic_provider(provider: str) -> bool:
    """Return True when provider uses the GenericCollector."""
    meta = _metadata_for(provider)
    return bool(meta and meta.get("type") == "generic")


def get_supported_providers() -> Dict[str, Dict[str, Any]]:
    """Return the provider metadata dictionary."""
    return SUPPORTED_PROVIDERS


def get_provider_metadata(provider: str) -> Optional[Dict[str, Any]]:
    """Fetch metadata for a single provider."""
    return _metadata_for(provider)


def get_generic_providers() -> List[str]:
    """List all providers served by the GenericCollector."""
    return [slug for slug, meta in SUPPORTED_PROVIDERS.items() if meta.get("type") == "generic"]


def _config_value(attr_name: Optional[str]) -> Optional[str]:
    if not attr_name:
        return None
    return getattr(config, attr_name, None)


def build_generic_collector_config(
    provider: str,
    customer_id: str,
    credentials: Optional[Dict[str, Any]] = None,
) -> GenericCollectorConfig:
    """
    Construct a GenericCollectorConfig for the given provider using a mix of
    stored credentials (customer specific) and environment defaults.
    """
    meta = _metadata_for(provider)
    if not meta or meta.get("type") != "generic":
        raise ValueError(f"Provider '{provider}' is not configured for the Generic Collector")

    config_keys: Dict[str, str] = meta.get("config_keys", {})
    creds = credentials or {}

    prometheus_url = creds.get("prometheus_url") or _config_value(config_keys.get("prometheus_url"))
    if not prometheus_url:
        raise ValueError(f"Prometheus URL not configured for provider '{provider}'")

    config_kwargs: Dict[str, Any] = {
        "provider": provider,
        "customer_id": customer_id,
        "prometheus_url": prometheus_url,
        "dcgm_url": creds.get("dcgm_url") or _config_value(config_keys.get("dcgm_url")),
        "api_url": creds.get("api_url") or _config_value(config_keys.get("api_url")),
        "api_key": creds.get("api_key") or _config_value(config_keys.get("api_key")),
    }

    # Optional overrides for timeout / retries (rare, but supported).
    if "timeout" in creds:
        config_kwargs["timeout"] = creds["timeout"]
    if "retry_attempts" in creds:
        config_kwargs["retry_attempts"] = creds["retry_attempts"]
    
    # Cost calculation parameters
    if "hourly_rate" in creds:
        config_kwargs["hourly_rate"] = float(creds["hourly_rate"])
    if "instance_id" in creds:
        config_kwargs["instance_id"] = creds["instance_id"]
    if "pod_start_time" in creds:
        # Parse datetime if it's a string
        from datetime import datetime
        start_time = creds["pod_start_time"]
        if isinstance(start_time, str):
            config_kwargs["pod_start_time"] = datetime.fromisoformat(start_time)
        else:
            config_kwargs["pod_start_time"] = start_time

    return GenericCollectorConfig(**config_kwargs)


def provider_enabled(provider: str) -> bool:
    """
    Inspect the configured enabled flag for a provider. If no flag exists,
    assume the provider is available (default True).
    """
    meta = _metadata_for(provider)
    if not meta:
        return False
    flag_name = meta.get("enabled_flag")
    if not flag_name:
        return True
    return bool(getattr(config, flag_name, False))


def provider_requirements(provider: str) -> List[Dict[str, Any]]:
    """Return the credential/configuration requirements for a provider."""
    meta = _metadata_for(provider)
    if not meta:
        return []
    return meta.get("requirements", [])
