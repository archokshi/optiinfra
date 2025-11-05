"""
Orchestrator Registration

Handles registration and heartbeat with the orchestrator.
"""

import httpx
import asyncio
import logging
from typing import Optional
from datetime import datetime
from src.config import settings

logger = logging.getLogger("resource_agent.registration")


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        """Initialize orchestrator client."""
        self.base_url = settings.orchestrator_url
        self.register_endpoint = settings.orchestrator_register_endpoint
        self.heartbeat_interval = settings.orchestrator_heartbeat_interval
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            bool: True if registration successful
        """
        registration_data = {
            "agent_id": settings.agent_id,
            "agent_type": settings.agent_type,
            "capabilities": [
                "gpu_metrics_collection",
                "cpu_metrics_collection",
                "memory_metrics_collection",
                "utilization_analysis",
                "scaling_recommendations",
                "kvoptkit_integration"
            ],
            "endpoint": f"http://localhost:{settings.port}",
            "health_check_endpoint": f"http://localhost:{settings.port}/health",
            "version": "1.0.0",
            "status": "active"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{self.register_endpoint}",
                    json=registration_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.registered = True
                    logger.info(f"Successfully registered with orchestrator: {settings.agent_id}")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to register with orchestrator: {e}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            bool: True if heartbeat successful
        """
        heartbeat_data = {
            "agent_id": settings.agent_id,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "requests_processed": 0,  # Placeholder
                "avg_response_time_ms": 0.0  # Placeholder
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/heartbeat",
                    json=heartbeat_data,
                    timeout=5.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False
    
    async def start_heartbeat(self):
        """Start periodic heartbeat task."""
        while True:
            if self.registered:
                await self.send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def deregister(self):
        """Deregister agent from orchestrator."""
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self.base_url}/api/v1/agents/{settings.agent_id}",
                    timeout=5.0
                )
                logger.info(f"Deregistered from orchestrator: {settings.agent_id}")
        except Exception as e:
            logger.error(f"Failed to deregister: {e}")


# Global orchestrator client
orchestrator_client = OrchestratorClient()
