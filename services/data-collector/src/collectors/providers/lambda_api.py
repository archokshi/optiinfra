"""
Lambda Labs API Adapter

Documentation: https://cloud.lambdalabs.com/api/v1/docs
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class LambdaLabsAPIAdapter(BaseProviderAPI):
    """Lambda Labs API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Lambda Labs billing information"""
        # Lambda Labs doesn't have a billing API endpoint
        # Return placeholder
        return {
            "message": "Billing API not available",
            "currency": "USD"
        }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Lambda Labs instance information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v1/instances",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            instances = data.get("data", [])
            
            if instance_id:
                instance = next((i for i in instances if i.get("id") == instance_id), {})
                return self._format_instance(instance)
            else:
                return {
                    "instances": [self._format_instance(i) for i in instances],
                    "count": len(instances)
                }
    
    def _format_instance(self, instance: Dict) -> Dict[str, Any]:
        """Format instance data"""
        return {
            "id": instance.get("id"),
            "name": instance.get("name"),
            "status": instance.get("status"),
            "instance_type": instance.get("instance_type", {}),
            "region": instance.get("region", {}),
            "ip": instance.get("ip"),
        }
