"""
Docker API Adapter

Documentation: https://docs.docker.com/engine/api/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class DockerAPIAdapter(BaseProviderAPI):
    """Docker API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Docker billing information (N/A for Docker)"""
        return {
            "message": "Docker does not have billing API",
            "note": "Use host infrastructure billing"
        }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Docker container information"""
        async with httpx.AsyncClient() as client:
            if instance_id:
                response = await client.get(
                    f"{self.api_url}/containers/{instance_id}/json"
                )
                response.raise_for_status()
                return self._format_container(response.json())
            else:
                response = await client.get(
                    f"{self.api_url}/containers/json?all=true"
                )
                response.raise_for_status()
                containers = response.json()
                return {
                    "containers": [self._format_container(c) for c in containers],
                    "count": len(containers)
                }
    
    def _format_container(self, container: Dict) -> Dict[str, Any]:
        """Format container data"""
        return {
            "id": container.get("Id"),
            "name": container.get("Name", "").lstrip("/"),
            "image": container.get("Image"),
            "status": container.get("State", {}).get("Status"),
            "created": container.get("Created"),
            "ports": container.get("NetworkSettings", {}).get("Ports", {}),
        }
