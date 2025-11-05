"""
Vultr API Adapter

Documentation: https://www.vultr.com/api/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class VultrAPIAdapter(BaseProviderAPI):
    """Vultr API adapter for billing and instance data"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """
        Get Vultr billing information
        
        Returns:
            Dict with balance, pending charges, etc.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v2/account",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            account = data.get("account", {})
            
            return {
                "balance": float(account.get("balance", 0)),
                "pending_charges": float(account.get("pending_charges", 0)),
                "last_payment_date": account.get("last_payment_date"),
                "last_payment_amount": float(account.get("last_payment_amount", 0)),
                "currency": "USD"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Vultr instance information
        
        Args:
            instance_id: Vultr instance ID
        
        Returns:
            Dict with instance details
        """
        async with httpx.AsyncClient() as client:
            if instance_id:
                # Get specific instance
                response = await client.get(
                    f"{self.api_url}/v2/instances/{instance_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            else:
                # Get all instances
                response = await client.get(
                    f"{self.api_url}/v2/instances",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            
            response.raise_for_status()
            data = response.json()
            
            if instance_id:
                instance = data.get("instance", {})
                return self._format_instance(instance)
            else:
                instances = data.get("instances", [])
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
            "power_status": instance.get("power_status"),
            "region": instance.get("region"),
            "plan": instance.get("plan"),
            "vcpu_count": instance.get("vcpu_count"),
            "ram": instance.get("ram"),
            "disk": instance.get("disk"),
            "main_ip": instance.get("main_ip"),
            "os": instance.get("os"),
            "hostname": instance.get("hostname"),
            "cost_per_month": float(instance.get("cost_per_month", 0)),
        }
