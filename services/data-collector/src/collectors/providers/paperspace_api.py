"""
Paperspace API Adapter

Documentation: https://docs.paperspace.com/gradient/api-reference/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class PaperspaceAPIAdapter(BaseProviderAPI):
    """Paperspace API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Paperspace billing information"""
        return {
            "message": "Billing API not publicly documented",
            "currency": "USD"
        }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Paperspace machine information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/machines/getMachines",
                headers={"X-API-Key": self.api_key}
            )
            response.raise_for_status()
            machines = response.json()
            
            if instance_id:
                machine = next((m for m in machines if m.get("id") == instance_id), {})
                return machine
            else:
                return {
                    "machines": machines,
                    "count": len(machines)
                }
