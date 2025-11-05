"""
CoreWeave API Adapter

Documentation: https://docs.coreweave.com/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class CoreWeaveAPIAdapter(BaseProviderAPI):
    """CoreWeave API adapter (Kubernetes-based)"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get CoreWeave billing information"""
        return {
            "message": "Use Kubernetes API for resource info",
            "currency": "USD"
        }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get CoreWeave instance information"""
        return {
            "message": "Use Kubernetes API for pod/deployment info",
            "instance_id": instance_id
        }
