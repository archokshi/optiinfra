"""
Mock Cloud Provider Client - Python SDK for agents
"""

import logging
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class MockCloudClient:
    """Client for interacting with mock cloud provider"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to mock cloud API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def list_instances(
        self,
        provider: Optional[str] = None,
        pricing_model: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[Dict]:
        """List instances with optional filtering"""
        params = {}
        if provider:
            params['provider'] = provider
        if pricing_model:
            params['pricing_model'] = pricing_model
        if state:
            params['state'] = state
        
        result = self._request('GET', '/instances', params=params)
        return result.get('instances', [])
    
    def get_instance(self, instance_id: str) -> Dict:
        """Get a specific instance"""
        return self._request('GET', f'/instances/{instance_id}')
    
    def create_instance(
        self,
        instance_type: str,
        pricing_model: str = "on-demand",
        provider: str = "aws",
        region: str = "us-east-1",
        tags: Optional[Dict[str, str]] = None,
        auto_start: bool = True,
    ) -> Dict:
        """Create a new instance"""
        data = {
            'instance_type': instance_type,
            'pricing_model': pricing_model,
            'provider': provider,
            'region': region,
            'tags': tags or {},
            'auto_start': auto_start,
        }
        
        return self._request('POST', '/instances', json=data)
    
    def migrate_to_spot(self, instance_id: str) -> Dict:
        """Migrate instance to spot pricing"""
        return self._request('POST', f'/instances/{instance_id}/migrate/spot')
    
    def right_size(self, instance_id: str, new_instance_type: str) -> Dict:
        """Right-size an instance to a different type"""
        data = {'new_instance_type': new_instance_type}
        return self._request('POST', f'/instances/{instance_id}/right-size', json=data)
    
    def get_metrics(self, instance_id: str) -> Dict:
        """Get current metrics for an instance"""
        return self._request('GET', f'/instances/{instance_id}/metrics')
    
    def get_total_costs(
        self,
        provider: Optional[str] = None,
        pricing_model: Optional[str] = None,
    ) -> Dict:
        """Get total costs across instances"""
        params = {}
        if provider:
            params['provider'] = provider
        if pricing_model:
            params['pricing_model'] = pricing_model
        
        return self._request('GET', '/costs', params=params)
    
    def get_savings_potential(self) -> Dict:
        """Calculate potential savings from optimizations"""
        return self._request('GET', '/costs/savings-potential')
    
    def find_spot_migration_opportunities(self) -> List[Dict]:
        """Find instances that can be migrated to spot pricing"""
        instances = self.list_instances(pricing_model="on-demand", state="running")
        
        opportunities = []
        for instance in instances:
            instance_id = instance['id']
            current_rate = instance['hourly_rate']
            
            instance_type = instance['instance_type']
            pricing = self.get_instance_type_pricing(instance_type)
            
            spot_rate = pricing['costs']['spot']['hourly']
            savings = current_rate - spot_rate
            
            if savings > 0:
                opportunities.append({
                    'instance_id': instance_id,
                    'instance_type': instance_type,
                    'current_rate': current_rate,
                    'spot_rate': spot_rate,
                    'savings_monthly': round(savings * 730, 2),
                    'savings_percentage': round((savings / current_rate) * 100, 2),
                })
        
        opportunities.sort(key=lambda x: x['savings_monthly'], reverse=True)
        return opportunities
    
    def get_instance_type_pricing(self, instance_type: str) -> Dict:
        """Get pricing comparison for an instance type"""
        return self._request('GET', f'/instance-types/{instance_type}/pricing')
