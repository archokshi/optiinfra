"""
Mock Cloud Provider - REST API Server

Flask server providing cloud provider APIs for testing.
"""

import logging
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

from models import CloudProvider, PricingModel, InstanceState, get_instance_type, list_instance_types
from instance_manager import InstanceManager
from cost_calculator import CostCalculator
from metrics_generator import MetricsGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize managers
instance_manager = InstanceManager()
cost_calculator = CostCalculator()
metrics_generator = MetricsGenerator()

# Background thread for metric updates
def metrics_updater():
    """Background thread to update metrics periodically"""
    while True:
        try:
            instance_manager.update_metrics()
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

# Start metrics updater
metrics_thread = threading.Thread(target=metrics_updater, daemon=True)
metrics_thread.start()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "mock-cloud-provider",
        "total_instances": len(instance_manager.instances),
        "running_instances": len([i for i in instance_manager.instances.values() if i.state == InstanceState.RUNNING]),
    }), 200

# List instances
@app.route('/instances', methods=['GET'])
def list_instances():
    """List all instances with optional filtering"""
    provider = request.args.get('provider')
    pricing_model = request.args.get('pricing_model')
    state = request.args.get('state')
    
    provider_enum = CloudProvider(provider) if provider else None
    pricing_enum = PricingModel(pricing_model) if pricing_model else None
    state_enum = InstanceState(state) if state else None
    
    instances = instance_manager.list_instances(
        provider=provider_enum,
        pricing_model=pricing_enum,
        state=state_enum,
    )
    
    return jsonify({
        "instances": [i.to_dict() for i in instances],
        "count": len(instances),
    }), 200

# Get specific instance
@app.route('/instances/<instance_id>', methods=['GET'])
def get_instance(instance_id):
    """Get a specific instance"""
    try:
        instance = instance_manager.get_instance(instance_id)
        return jsonify(instance.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Create instance
@app.route('/instances', methods=['POST'])
def create_instance():
    """Create a new instance"""
    data = request.get_json()
    
    try:
        instance_type = data.get('instance_type')
        pricing_model = data.get('pricing_model', 'on-demand')
        provider = data.get('provider', 'aws')
        region = data.get('region', 'us-east-1')
        tags = data.get('tags', {})
        auto_start = data.get('auto_start', True)
        
        instance = instance_manager.create_instance(
            instance_type=instance_type,
            pricing_model=PricingModel(pricing_model),
            provider=CloudProvider(provider),
            region=region,
            tags=tags,
        )
        
        if auto_start:
            instance = instance_manager.start_instance(instance.id)
        
        return jsonify(instance.to_dict()), 201
        
    except (ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 400

# Start instance
@app.route('/instances/<instance_id>/start', methods=['POST'])
def start_instance(instance_id):
    """Start an instance"""
    try:
        instance = instance_manager.start_instance(instance_id)
        return jsonify(instance.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Stop instance
@app.route('/instances/<instance_id>/stop', methods=['POST'])
def stop_instance(instance_id):
    """Stop an instance"""
    try:
        instance = instance_manager.stop_instance(instance_id)
        return jsonify(instance.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Terminate instance
@app.route('/instances/<instance_id>', methods=['DELETE'])
def terminate_instance(instance_id):
    """Terminate an instance"""
    try:
        instance = instance_manager.terminate_instance(instance_id)
        return jsonify(instance.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Migrate to spot
@app.route('/instances/<instance_id>/migrate/spot', methods=['POST'])
def migrate_to_spot(instance_id):
    """Migrate instance to spot pricing"""
    try:
        result = instance_manager.migrate_to_spot(instance_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Migrate to reserved
@app.route('/instances/<instance_id>/migrate/reserved', methods=['POST'])
def migrate_to_reserved(instance_id):
    """Migrate instance to reserved pricing"""
    try:
        result = instance_manager.migrate_to_reserved(instance_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Right-size instance
@app.route('/instances/<instance_id>/right-size', methods=['POST'])
def right_size_instance(instance_id):
    """Right-size an instance"""
    data = request.get_json()
    new_instance_type = data.get('new_instance_type')
    
    if not new_instance_type:
        return jsonify({"error": "new_instance_type required"}), 400
    
    try:
        result = instance_manager.right_size(instance_id, new_instance_type)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# Get metrics
@app.route('/instances/<instance_id>/metrics', methods=['GET'])
def get_metrics(instance_id):
    """Get current metrics for an instance"""
    try:
        instance = instance_manager.get_instance(instance_id)
        metrics = metrics_generator.generate_metrics(instance)
        return jsonify(metrics), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Get time series metrics
@app.route('/instances/<instance_id>/metrics/timeseries', methods=['GET'])
def get_metrics_timeseries(instance_id):
    """Get time series metrics for an instance"""
    hours = request.args.get('hours', default=24, type=int)
    
    try:
        instance = instance_manager.get_instance(instance_id)
        timeseries = metrics_generator.generate_time_series(instance, hours)
        return jsonify(timeseries), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Get recommendations
@app.route('/instances/<instance_id>/recommendations', methods=['GET'])
def get_recommendations(instance_id):
    """Get optimization recommendations for an instance"""
    try:
        instance = instance_manager.get_instance(instance_id)
        recommendations = metrics_generator.get_recommendations(instance)
        return jsonify({
            "instance_id": instance_id,
            "recommendations": recommendations,
            "count": len(recommendations),
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# Get costs
@app.route('/costs', methods=['GET'])
def get_costs():
    """Get total costs across instances"""
    provider = request.args.get('provider')
    pricing_model = request.args.get('pricing_model')
    
    provider_enum = CloudProvider(provider) if provider else None
    pricing_enum = PricingModel(pricing_model) if pricing_model else None
    
    costs = instance_manager.get_total_cost(
        provider=provider_enum,
        pricing_model=pricing_enum,
    )
    
    return jsonify(costs), 200

# Get savings potential
@app.route('/costs/savings-potential', methods=['GET'])
def get_savings_potential():
    """Calculate potential savings from optimizations"""
    savings = instance_manager.calculate_savings_potential()
    return jsonify(savings), 200

# List instance types
@app.route('/instance-types', methods=['GET'])
def list_instance_type_catalog():
    """List available instance types"""
    provider = request.args.get('provider')
    has_gpu = request.args.get('has_gpu')
    
    provider_enum = CloudProvider(provider) if provider else None
    has_gpu_bool = has_gpu.lower() == 'true' if has_gpu else None
    
    types = list_instance_types(provider=provider_enum, has_gpu=has_gpu_bool)
    
    return jsonify({
        "instance_types": [
            {
                "name": t.name,
                "provider": t.provider.value,
                "vcpus": t.vcpus,
                "memory_gb": t.memory_gb,
                "gpu_count": t.gpu_count,
                "gpu_type": t.gpu_type,
                "pricing": {
                    "on_demand_hourly": round(t.on_demand_hourly, 4),
                    "spot_hourly": round(t.spot_hourly, 4),
                    "reserved_hourly": round(t.reserved_hourly, 4),
                    "spot_discount": round(t.spot_discount, 2),
                    "reserved_discount": round(t.reserved_discount, 2),
                }
            }
            for t in types
        ],
        "count": len(types),
    }), 200

# Get instance type pricing
@app.route('/instance-types/<instance_type>/pricing', methods=['GET'])
def get_instance_type_pricing(instance_type):
    """Get pricing comparison for an instance type"""
    inst_type = get_instance_type(instance_type)
    
    if not inst_type:
        return jsonify({"error": f"Instance type not found: {instance_type}"}), 404
    
    comparison = cost_calculator.compare_pricing_models(inst_type)
    return jsonify(comparison), 200

if __name__ == '__main__':
    logger.info("Starting Mock Cloud Provider API on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
