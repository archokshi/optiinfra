"""
Provider API Adapters

Each provider has a simple adapter for billing/cost data collection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import logging


logger = logging.getLogger(__name__)


class BaseProviderAPI(ABC):
    """Base class for provider API adapters"""
    
    def __init__(self, api_key: str, api_url: str):
        """
        Initialize provider API adapter
        
        Args:
            api_key: Provider API key
            api_url: Provider API base URL
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def get_billing_info(self) -> Dict[str, Any]:
        """
        Get billing information
        
        Returns:
            Dict with billing data (cost, balance, usage, etc.)
        """
        pass
    
    @abstractmethod
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get instance/pod information
        
        Args:
            instance_id: Instance/pod ID (optional)
        
        Returns:
            Dict with instance data (status, specs, IP, etc.)
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.__class__.__name__.replace('APIAdapter', '').lower()


# Import all adapters
from .vultr_api import VultrAPIAdapter
from .runpod_api import RunPodAPIAdapter
from .digitalocean_api import DigitalOceanAPIAdapter
from .linode_api import LinodeAPIAdapter
from .hetzner_api import HetznerAPIAdapter
from .lambda_api import LambdaLabsAPIAdapter
from .coreweave_api import CoreWeaveAPIAdapter
from .paperspace_api import PaperspaceAPIAdapter
from .ovh_api import OVHAPIAdapter
from .kubernetes_api import KubernetesAPIAdapter
from .docker_api import DockerAPIAdapter


__all__ = [
    'BaseProviderAPI',
    'VultrAPIAdapter',
    'RunPodAPIAdapter',
    'DigitalOceanAPIAdapter',
    'LinodeAPIAdapter',
    'HetznerAPIAdapter',
    'LambdaLabsAPIAdapter',
    'CoreWeaveAPIAdapter',
    'PaperspaceAPIAdapter',
    'OVHAPIAdapter',
    'KubernetesAPIAdapter',
    'DockerAPIAdapter',
]
