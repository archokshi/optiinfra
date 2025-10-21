"""
Agent registration helper for Python agents.

Usage:
    from shared.orchestrator.registration import AgentRegistration
    
    registration = AgentRegistration(
        agent_name="cost-agent-1",
        agent_type="cost",
        host="localhost",
        port=8001,
        capabilities=["spot_migration", "reserved_instances"]
    )
    
    # Register on startup
    registration.register()
    
    # Start heartbeat loop
    registration.start_heartbeat()
    
    # Unregister on shutdown
    registration.unregister()
"""

import requests
import threading
import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AgentRegistration:
    """Handles agent registration with the orchestrator."""
    
    def __init__(
        self,
        agent_name: str,
        agent_type: str,
        host: str,
        port: int,
        capabilities: List[str],
        orchestrator_url: str = "http://localhost:8080",
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.host = host
        self.port = port
        self.capabilities = capabilities
        self.orchestrator_url = orchestrator_url
        self.version = version
        self.metadata = metadata or {}
        
        self.agent_id: Optional[str] = None
        self.heartbeat_interval: int = 30
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.stop_heartbeat = threading.Event()
    
    def register(self) -> bool:
        """
        Register this agent with the orchestrator.
        
        Returns:
            bool: True if registration successful
        """
        try:
            response = requests.post(
                f"{self.orchestrator_url}/agents/register",
                json={
                    "name": self.agent_name,
                    "type": self.agent_type,
                    "host": self.host,
                    "port": self.port,
                    "capabilities": self.capabilities,
                    "version": self.version,
                    "metadata": self.metadata
                },
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.agent_id = data["agent_id"]
                self.heartbeat_interval = data.get("heartbeat_interval_seconds", 30)
                logger.info(f"Agent registered successfully: {self.agent_id}")
                return True
            else:
                logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def start_heartbeat(self):
        """Start the heartbeat thread."""
        if not self.agent_id:
            logger.error("Cannot start heartbeat - agent not registered")
            return
        
        self.stop_heartbeat.clear()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat started")
    
    def stop_heartbeat_loop(self):
        """Stop the heartbeat thread."""
        self.stop_heartbeat.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        logger.info("Heartbeat stopped")
    
    def unregister(self):
        """Unregister this agent from the orchestrator."""
        if not self.agent_id:
            return
        
        try:
            # Stop heartbeat first
            self.stop_heartbeat_loop()
            
            # Unregister
            response = requests.post(
                f"{self.orchestrator_url}/agents/{self.agent_id}/unregister",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Agent unregistered successfully: {self.agent_id}")
            else:
                logger.warning(f"Unregister failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Unregister error: {e}")
    
    def _heartbeat_loop(self):
        """Background thread that sends periodic heartbeats."""
        while not self.stop_heartbeat.is_set():
            try:
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            # Wait for next interval
            self.stop_heartbeat.wait(self.heartbeat_interval)
    
    def _send_heartbeat(self):
        """Send a single heartbeat to the orchestrator."""
        if not self.agent_id:
            return
        
        try:
            response = requests.post(
                f"{self.orchestrator_url}/agents/{self.agent_id}/heartbeat",
                json={
                    "status": "healthy",
                    "metadata": self.metadata
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"Heartbeat sent successfully")
            else:
                logger.warning(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Heartbeat send error: {e}")
