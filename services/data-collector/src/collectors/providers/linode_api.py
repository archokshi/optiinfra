"""
Linode/Akamai API Adapter

Documentation: https://www.linode.com/docs/api/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class LinodeAPIAdapter(BaseProviderAPI):
    """Linode API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Linode billing information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v4/account",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "balance": float(data.get("balance", 0)),
                "balance_uninvoiced": float(data.get("balance_uninvoiced", 0)),
                "active_since": data.get("active_since"),
                "currency": "USD"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Linode instance information"""
        async with httpx.AsyncClient() as client:
            if instance_id:
                response = await client.get(
                    f"{self.api_url}/v4/linode/instances/{instance_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return self._format_instance(response.json())
            else:
                response = await client.get(
                    f"{self.api_url}/v4/linode/instances",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                instances = data.get("data", [])
                return {
                    "instances": [self._format_instance(inst) for inst in instances],
                    "count": len(instances)
                }
    
    def _format_instance(self, instance: Dict) -> Dict[str, Any]:
        """Format instance data"""
        return {
            "id": instance.get("id"),
            "label": instance.get("label"),
            "status": instance.get("status"),
            "region": instance.get("region"),
            "type": instance.get("type"),
            "specs": instance.get("specs", {}),
            "ipv4": instance.get("ipv4", []),
            "created": instance.get("created"),
        }
