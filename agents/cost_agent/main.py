#!/usr/bin/env python3
"""
Cost Agent - Example implementation with task handling.

This agent:
1. Registers with the orchestrator
2. Sends periodic heartbeats
3. Receives and processes cost-related tasks
"""

import logging
import signal
import sys
import time
from typing import Dict, Any

from shared.orchestrator.registration import AgentRegistration
from shared.orchestrator.task_handler import TaskHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CostAgent:
    """Cost optimization agent."""
    
    def __init__(
        self,
        agent_name: str = "cost-agent-1",
        host: str = "localhost",
        port: int = 8001,
        orchestrator_url: str = "http://localhost:8080"
    ):
        self.agent_name = agent_name
        self.host = host
        self.port = port
        self.orchestrator_url = orchestrator_url
        
        # Initialize registration
        self.registration = AgentRegistration(
            agent_name=agent_name,
            agent_type="cost",
            host=host,
            port=port,
            capabilities=[
                "analyze_cost",
                "migrate_to_spot",
                "right_size",
                "reserved_instances"
            ],
            orchestrator_url=orchestrator_url,
            version="1.0.0"
        )
        
        # Initialize task handler
        self.task_handler = TaskHandler(port=port, host="0.0.0.0")
        self._register_task_handlers()
        
        self.running = False
    
    def _register_task_handlers(self):
        """Register all task handlers."""
        
        @self.task_handler.register_task("analyze_cost")
        def handle_analyze_cost(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Analyzing cost for task {task_id}")
            return self.analyze_cost(params)
        
        @self.task_handler.register_task("migrate_to_spot")
        def handle_spot_migration(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Migrating to spot for task {task_id}")
            return self.migrate_to_spot(params)
        
        @self.task_handler.register_task("right_size")
        def handle_right_size(task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"Right-sizing resources for task {task_id}")
            return self.right_size(params)
    
    def analyze_cost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost savings opportunities."""
        account_id = params.get('account_id', 'default')
        period = params.get('period', 'last_7_days')
        
        # Simulate analysis
        logger.info(f"Analyzing costs for account {account_id}, period {period}")
        time.sleep(1.5)  # Simulate work
        
        return {
            'account_id': account_id,
            'period': period,
            'current_spend': 15420.50,
            'potential_savings': 6800.25,
            'savings_percentage': 44.1,
            'recommendations': [
                {
                    'type': 'spot_migration',
                    'instances': 12,
                    'monthly_savings': 4200.00
                },
                {
                    'type': 'right_sizing',
                    'instances': 5,
                    'monthly_savings': 1800.25
                },
                {
                    'type': 'reserved_instances',
                    'instances': 3,
                    'monthly_savings': 800.00
                }
            ]
        }
    
    def migrate_to_spot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate instances to spot pricing."""
        instance_ids = params.get('instance_ids', [])
        
        logger.info(f"Migrating {len(instance_ids)} instances to spot")
        time.sleep(2)  # Simulate migration
        
        return {
            'total_instances': len(instance_ids),
            'migrated': len(instance_ids),
            'failed': 0,
            'monthly_savings': len(instance_ids) * 350.00,
            'status': 'completed'
        }
    
    def right_size(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Right-size over-provisioned instances."""
        instance_ids = params.get('instance_ids', [])
        
        logger.info(f"Right-sizing {len(instance_ids)} instances")
        time.sleep(1)  # Simulate analysis
        
        return {
            'total_instances': len(instance_ids),
            'optimized': len(instance_ids),
            'monthly_savings': len(instance_ids) * 280.00,
            'average_size_reduction': '38%',
            'status': 'completed'
        }
    
    def start(self):
        """Start the agent."""
        logger.info(f"Starting {self.agent_name}...")
        
        # Start task handler first
        self.task_handler.start(threaded=True)
        time.sleep(1)  # Give server time to start
        
        # Register with orchestrator
        if not self.registration.register():
            logger.error("Failed to register with orchestrator")
            sys.exit(1)
        
        # Start heartbeat
        self.registration.start_heartbeat()
        
        self.running = True
        logger.info(f"{self.agent_name} is running and ready to receive tasks")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def stop(self):
        """Stop the agent."""
        logger.info(f"Stopping {self.agent_name}...")
        self.running = False
        
        # Unregister
        self.registration.unregister()
        
        # Stop task handler
        self.task_handler.stop()
        
        logger.info(f"{self.agent_name} stopped")


def main():
    """Main entry point."""
    agent = CostAgent(
        agent_name="cost-agent-1",
        host="localhost",
        port=8001,
        orchestrator_url="http://localhost:8080"
    )
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        agent.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start agent
    agent.start()


if __name__ == "__main__":
    main()
