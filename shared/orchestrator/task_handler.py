"""
Task handler for Python agents to receive and process tasks from orchestrator.

Usage:
    from shared.orchestrator.task_handler import TaskHandler
    
    handler = TaskHandler(port=8001)
    
    @handler.register_task("analyze_cost")
    def handle_cost_analysis(task_id, parameters):
        # Process task
        result = analyze_costs(parameters)
        return {"savings": result}
    
    handler.start()
"""

import json
import logging
import time
from typing import Dict, Any, Callable, Optional
from flask import Flask, request, jsonify
import threading

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handles incoming tasks from the orchestrator."""
    
    def __init__(self, port: int = 8001, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.app = Flask(__name__)
        self.task_handlers: Dict[str, Callable] = {}
        self.server_thread: Optional[threading.Thread] = None
        
        # Register routes
        self.app.add_url_rule('/task', 'handle_task', self._handle_task, methods=['POST'])
        self.app.add_url_rule('/health', 'health', self._health, methods=['GET'])
    
    def register_task(self, task_type: str):
        """
        Decorator to register a task handler function.
        
        Args:
            task_type: The type of task this handler processes
            
        Example:
            @handler.register_task("analyze_cost")
            def handle_analysis(task_id, parameters):
                return {"result": "success"}
        """
        def decorator(func: Callable):
            self.task_handlers[task_type] = func
            logger.info(f"Registered handler for task type: {task_type}")
            return func
        return decorator
    
    def start(self, threaded: bool = True):
        """
        Start the task handler server.
        
        Args:
            threaded: If True, run in background thread
        """
        if threaded:
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            logger.info(f"Task handler started on {self.host}:{self.port} (threaded)")
        else:
            self._run_server()
    
    def stop(self):
        """Stop the task handler server."""
        # Flask doesn't have a built-in stop method when using run()
        # In production, use a proper WSGI server like gunicorn
        logger.info("Task handler stopping...")
    
    def _run_server(self):
        """Internal method to run Flask server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False
        )
    
    def _handle_task(self):
        """Handle incoming task from orchestrator."""
        start_time = time.time()
        
        try:
            # Parse request
            data = request.get_json()
            
            task_id = data.get('task_id')
            task_type = data.get('task_type')
            parameters = data.get('parameters', {})
            
            logger.info(f"Received task: {task_id} (type: {task_type})")
            
            # Validate task
            if not task_id or not task_type:
                return jsonify({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': 'Missing task_id or task_type'
                }), 400
            
            # Find handler
            handler = self.task_handlers.get(task_type)
            if not handler:
                return jsonify({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': f'No handler registered for task type: {task_type}'
                }), 400
            
            # Execute task
            try:
                result = handler(task_id, parameters)
                
                execution_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Task completed: {task_id} ({execution_time}ms)")
                
                return jsonify({
                    'task_id': task_id,
                    'status': 'completed',
                    'result': result,
                    'execution_time_ms': execution_time
                }), 200
                
            except Exception as e:
                logger.error(f"Task execution failed: {task_id} - {e}", exc_info=True)
                
                execution_time = int((time.time() - start_time) * 1000)
                
                return jsonify({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'execution_time_ms': execution_time
                }), 500
        
        except Exception as e:
            logger.error(f"Error handling task request: {e}", exc_info=True)
            return jsonify({
                'status': 'failed',
                'error': str(e)
            }), 500
    
    def _health(self):
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'registered_tasks': list(self.task_handlers.keys())
        }), 200


# Example usage
if __name__ == "__main__":
    # Create handler
    handler = TaskHandler(port=8001)
    
    # Register task handlers
    @handler.register_task("analyze_cost")
    def handle_cost_analysis(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Example: Analyze cost savings."""
        account_id = parameters.get('account_id')
        period = parameters.get('period', 'last_7_days')
        
        # Simulate processing
        time.sleep(1)
        
        return {
            'account_id': account_id,
            'period': period,
            'total_spend': 12500.50,
            'potential_savings': 3200.75,
            'recommendations': [
                {'type': 'spot_migration', 'savings': 2000},
                {'type': 'right_sizing', 'savings': 1200.75}
            ]
        }
    
    @handler.register_task("migrate_to_spot")
    def handle_spot_migration(task_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Example: Migrate instances to spot."""
        instance_ids = parameters.get('instance_ids', [])
        
        # Simulate processing
        time.sleep(2)
        
        return {
            'migrated_instances': len(instance_ids),
            'estimated_savings_per_month': 5600.00,
            'status': 'completed'
        }
    
    # Start server
    print("Starting example agent task handler...")
    handler.start(threaded=False)
