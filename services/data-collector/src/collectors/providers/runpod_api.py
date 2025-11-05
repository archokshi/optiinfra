"""
RunPod API Adapter

Documentation: https://docs.runpod.io/reference/graphql-api
"""

import httpx
from typing import Dict, Optional, Any

from . import BaseProviderAPI


class RunPodAPIAdapter(BaseProviderAPI):
    """RunPod GraphQL API adapter"""
    
    async def get_billing_info(self) -> Dict[str, Any]:
        """
        Get RunPod billing information
        
        Returns:
            Dict with spending, balance, etc.
        """
        query = """
        query {
            myself {
                currentSpendPerHr
                totalSpent
                creditBalance
                referralEarned
            }
        }
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={"query": query},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            myself = data.get("data", {}).get("myself", {})
            
            return {
                "cost_per_hour": float(myself.get("currentSpendPerHr", 0)),
                "total_spent": float(myself.get("totalSpent", 0)),
                "credit_balance": float(myself.get("creditBalance", 0)),
                "referral_earned": float(myself.get("referralEarned", 0)),
                "currency": "USD"
            }
    
    async def get_instance_info(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get RunPod pod information
        
        Args:
            instance_id: Pod ID
        
        Returns:
            Dict with pod details
        """
        if instance_id:
            query = f"""
            query {{
                pod(input: {{podId: "{instance_id}"}}) {{
                    id
                    name
                    runtime {{
                        uptimeInSeconds
                        ports {{
                            ip
                            isIpPublic
                            privatePort
                            publicPort
                            type
                        }}
                        gpus {{
                            id
                            gpuTypeId
                            gpuUtilPercent
                            memoryUtilPercent
                        }}
                    }}
                    machine {{
                        podHostId
                    }}
                    costPerHr
                    gpuCount
                    vcpuCount
                    memoryInGb
                    volumeInGb
                }}
            }}
            """
        else:
            query = """
            query {
                myself {
                    pods {
                        id
                        name
                        runtime {
                            uptimeInSeconds
                        }
                        costPerHr
                        gpuCount
                        vcpuCount
                        memoryInGb
                    }
                }
            }
            """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={"query": query},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            if instance_id:
                pod = data.get("data", {}).get("pod", {})
                return self._format_pod(pod)
            else:
                pods = data.get("data", {}).get("myself", {}).get("pods", [])
                return {
                    "pods": [self._format_pod(pod) for pod in pods],
                    "count": len(pods)
                }
    
    def _format_pod(self, pod: Dict) -> Dict[str, Any]:
        """Format pod data"""
        runtime = pod.get("runtime") or {}
        return {
            "id": pod.get("id"),
            "name": pod.get("name"),
            "status": "running" if runtime else "stopped",
            "uptime_seconds": runtime.get("uptimeInSeconds", 0),
            "cost_per_hour": float(pod.get("costPerHr", 0)),
            "gpu_count": pod.get("gpuCount", 0),
            "vcpu_count": pod.get("vcpuCount", 0),
            "memory_gb": pod.get("memoryInGb", 0),
            "volume_gb": pod.get("volumeInGb", 0),
            "ports": runtime.get("ports", []),
            "gpus": runtime.get("gpus", []),
        }
