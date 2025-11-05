"""
Kubernetes API Adapter

Documentation: https://kubernetes.io/docs/reference/kubernetes-api/
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class KubernetesAPIAdapter(BaseProviderAPI):
    """Kubernetes API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """Get Kubernetes billing information (N/A for K8s)"""
        return {
            "message": "Kubernetes does not have billing API",
            "note": "Use cloud provider billing for managed K8s"
        }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Kubernetes pod/node information"""
        async with httpx.AsyncClient() as client:
            # Get pods
            response = await client.get(
                f"{self.api_url}/api/v1/pods",
                headers={"Authorization": f"Bearer {self.api_key}"},
                verify=False  # For self-signed certs
            )
            response.raise_for_status()
            data = response.json()
            pods = data.get("items", [])
            
            if instance_id:
                pod = next((p for p in pods if p.get("metadata", {}).get("name") == instance_id), {})
                return self._format_pod(pod)
            else:
                return {
                    "pods": [self._format_pod(p) for p in pods],
                    "count": len(pods)
                }
    
    def _format_pod(self, pod: Dict) -> Dict[str, Any]:
        """Format pod data"""
        metadata = pod.get("metadata", {})
        status = pod.get("status", {})
        spec = pod.get("spec", {})
        
        return {
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "status": status.get("phase"),
            "pod_ip": status.get("podIP"),
            "node_name": spec.get("nodeName"),
            "containers": [c.get("name") for c in spec.get("containers", [])],
        }
