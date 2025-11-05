"""
Orchestrator Registration

Handles registration and heartbeat with the orchestrator.
"""

import asyncio
import logging
from typing import Optional
import httpx
from datetime import datetime

from src.config import settings

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start orchestrator client."""
        self.client = httpx.AsyncClient(timeout=10.0)
        await self.register()
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """Stop orchestrator client."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.aclose()
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            bool: True if registration successful
        """
        if not self.client:
            logger.error("HTTP client not initialized")
            return False
        
        registration_url = (
            f"{settings.orchestrator_url}"
            f"{settings.orchestrator_register_endpoint}"
        )
        
        payload = {
            "agent_id": settings.agent_id,
            "agent_type": settings.agent_type,
            "capabilities": [
                "performance_monitoring",
                "bottleneck_detection",
                "kv_cache_optimization",
                "quantization_optimization",
                "batch_size_tuning"
            ],
            "endpoint": f"http://localhost:{settings.port}",
            "health_check_endpoint": "/api/v1/health",
            "version": "0.1.0",
            "metadata": {
                "environment": settings.environment,
                "log_level": settings.log_level
            }
        }
        
        try:
            response = await self.client.post(
                registration_url,
                json=payload
            )
            
            if response.status_code == 200:
                self.registered = True
                logger.info(
                    f"Successfully registered with orchestrator",
                    extra={
                        "agent_id": settings.agent_id,
                        "orchestrator_url": settings.orchestrator_url
                    }
                )
                return True
            else:
                logger.error(
                    f"Failed to register with orchestrator: {response.status_code}",
                    extra={"response": response.text}
                )
                return False
        
        except Exception as e:
            logger.error(
                f"Error registering with orchestrator: {e}",
                exc_info=True
            )
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            bool: True if heartbeat successful
        """
        if not self.client or not self.registered:
            return False
        
        heartbeat_url = f"{settings.orchestrator_url}/api/v1/agents/heartbeat"
        
        payload = {
            "agent_id": settings.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
        
        try:
            response = await self.client.post(
                heartbeat_url,
                json=payload
            )
            
            if response.status_code == 200:
                logger.debug(f"Heartbeat sent successfully")
                return True
            else:
                logger.warning(
                    f"Heartbeat failed: {response.status_code}",
                    extra={"response": response.text}
                )
                return False
        
        except Exception as e:
            logger.warning(f"Error sending heartbeat: {e}")
            return False
    
    async def _heartbeat_loop(self):
        """Background task for sending periodic heartbeats."""
        while True:
            try:
                await asyncio.sleep(settings.orchestrator_heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)


# Global orchestrator client instance
orchestrator_client = OrchestratorClient()
