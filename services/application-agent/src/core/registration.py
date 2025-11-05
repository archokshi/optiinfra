"""
Orchestrator Registration Client

Handles registration, heartbeat, and deregistration with the orchestrator.
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from .config import settings
from .logger import logger


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        self.base_url = settings.orchestrator_url
        self.agent_id = settings.agent_id
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            True if registration successful
        """
        if not settings.registration_enabled:
            logger.info("Registration disabled, skipping")
            return True
        
        payload = {
            "agent_id": settings.agent_id,
            "agent_name": settings.agent_name,
            "agent_type": settings.agent_type,
            "version": settings.version,
            "host": settings.host,
            "port": settings.port,
            "capabilities": [
                "quality_monitoring",
                "regression_detection",
                "validation_engine",
                "hallucination_detection",
                "ab_testing"
            ],
            "status": "active"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/register",
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.registered = True
                    logger.info(f"Successfully registered with orchestrator: {self.agent_id}")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            True if heartbeat successful
        """
        if not self.registered:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/{self.agent_id}/heartbeat",
                    json={"status": "active"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                    return True
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Heartbeat error: {str(e)}")
            return False
    
    async def heartbeat_loop(self):
        """Continuous heartbeat loop."""
        while self.registered:
            await self.send_heartbeat()
            await asyncio.sleep(settings.heartbeat_interval)
    
    async def start_heartbeat(self):
        """Start heartbeat task."""
        if self.registered and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            logger.info("Heartbeat task started")
    
    async def deregister(self) -> bool:
        """
        Deregister agent from orchestrator.
        
        Returns:
            True if deregistration successful
        """
        if not self.registered:
            return True
        
        # Stop heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/agents/{self.agent_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    self.registered = False
                    logger.info(f"Successfully deregistered from orchestrator")
                    return True
                else:
                    logger.error(f"Deregistration failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Deregistration error: {str(e)}")
            return False


# Global orchestrator client
orchestrator_client = OrchestratorClient()
