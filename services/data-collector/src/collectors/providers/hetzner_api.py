"""
Hetzner Cloud API Adapter

Documentation: https://docs.hetzner.cloud/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class HetznerAPIAdapter(BaseProviderAPI):
    """Hetzner Cloud API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Hetzner billing information (pricing info)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v1/pricing",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "pricing": data.get("pricing", {}),
                "currency": "EUR"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Hetzner server information"""
        async with httpx.AsyncClient() as client:
            if instance_id:
                response = await client.get(
                    f"{self.api_url}/v1/servers/{instance_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                return self._format_server(data.get("server", {}))
            else:
                response = await client.get(
                    f"{self.api_url}/v1/servers",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                servers = data.get("servers", [])
                return {
                    "servers": [self._format_server(s) for s in servers],
                    "count": len(servers)
                }
    
    def _format_server(self, server: Dict) -> Dict[str, Any]:
        """Format server data"""
        return {
            "id": server.get("id"),
            "name": server.get("name"),
            "status": server.get("status"),
            "server_type": server.get("server_type", {}).get("name"),
            "datacenter": server.get("datacenter", {}).get("name"),
            "public_net": server.get("public_net", {}),
            "created": server.get("created"),
        }
