"""
OVHcloud API Adapter

Documentation: https://api.ovh.com/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class OVHAPIAdapter(BaseProviderAPI):
    """OVHcloud API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get OVH billing information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/1.0/me/bill",
                headers={"X-Ovh-Application": self.api_key}
            )
            response.raise_for_status()
            bills = response.json()
            
            return {
                "bills": bills,
                "count": len(bills),
                "currency": "EUR"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get OVH instance information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/1.0/cloud/project",
                headers={"X-Ovh-Application": self.api_key}
            )
            response.raise_for_status()
            projects = response.json()
            
            return {
                "projects": projects,
                "count": len(projects)
            }
