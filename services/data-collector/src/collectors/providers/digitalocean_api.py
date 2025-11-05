"""
DigitalOcean API Adapter

Documentation: https://docs.digitalocean.com/reference/api/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class DigitalOceanAPIAdapter(BaseProviderAPI):
    """DigitalOcean API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """
        Get DigitalOcean billing information
        
        Returns:
            Dict with balance and usage
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v2/customers/my/balance",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "account_balance": float(data.get("account_balance", 0)),
                "month_to_date_balance": float(data.get("month_to_date_balance", 0)),
                "month_to_date_usage": float(data.get("month_to_date_usage", 0)),
                "generated_at": data.get("generated_at"),
                "currency": "USD"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get DigitalOcean droplet information
        
        Args:
            instance_id: Droplet ID
        
        Returns:
            Dict with droplet details
        """
        async with httpx.AsyncClient() as client:
            if instance_id:
                response = await client.get(
                    f"{self.api_url}/v2/droplets/{instance_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            else:
                response = await client.get(
                    f"{self.api_url}/v2/droplets",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            
            response.raise_for_status()
            data = response.json()
            
            if instance_id:
                droplet = data.get("droplet", {})
                return self._format_droplet(droplet)
            else:
                droplets = data.get("droplets", [])
                return {
                    "droplets": [self._format_droplet(d) for d in droplets],
                    "count": len(droplets)
                }
    
    def _format_droplet(self, droplet: Dict) -> Dict[str, Any]:
        """Format droplet data"""
        return {
            "id": droplet.get("id"),
            "name": droplet.get("name"),
            "status": droplet.get("status"),
            "region": droplet.get("region", {}).get("slug"),
            "size": droplet.get("size", {}).get("slug"),
            "vcpus": droplet.get("vcpus"),
            "memory": droplet.get("memory"),
            "disk": droplet.get("disk"),
            "ip_address": droplet.get("networks", {}).get("v4", [{}])[0].get("ip_address"),
            "image": droplet.get("image", {}).get("slug"),
            "created_at": droplet.get("created_at"),
        }
