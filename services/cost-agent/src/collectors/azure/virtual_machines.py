"""
Azure Virtual Machines Cost Collector

Collects VM costs, utilization metrics, and identifies optimization opportunities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.network import NetworkManagementClient
from .base import AzureBaseCollector
from .cost_management_client import AzureCostManagementClient


class AzureVirtualMachinesCollector(AzureBaseCollector):
    """Collector for Azure Virtual Machines"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        super().__init__(subscription_id, tenant_id, client_id, client_secret)
        self.compute_client = ComputeManagementClient(self.credentials, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credentials, subscription_id)
        self.network_client = NetworkManagementClient(self.credentials, subscription_id)
        self.cost_client = AzureCostManagementClient(subscription_id, tenant_id, client_id, client_secret)
        
        # Thresholds
        self.idle_cpu_threshold = 5.0  # %
        self.underutilized_cpu_threshold = 20.0  # %
        self.idle_network_threshold = 1.0  # GB/day
        self.spot_savings_target = 0.70  # 70% savings
        
        self.logger = logging.getLogger(__name__)
    
    async def collect_all(
        self,
        lookback_days: int = 30,
        include_utilization: bool = True
    ) -> Dict:
        """
        Collect all VM data and costs
        
        Args:
            lookback_days: Days to look back for metrics
            include_utilization: Whether to collect utilization metrics
            
        Returns:
            Dictionary with VM data, costs, and opportunities
        """
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        end_date = datetime.utcnow()
        
        self.logger.info(f"Collecting Azure VM data for {lookback_days} days")
        
        # List all VMs
        vms = await self._list_vms()
        self.logger.info(f"Found {len(vms)} VMs")
        
        # Collect costs and metrics for each VM
        vm_details = []
        for vm in vms:
            try:
                vm_data = await self._collect_vm_data(
                    vm=vm,
                    start_date=start_date,
                    end_date=end_date,
                    include_utilization=include_utilization
                )
                vm_details.append(vm_data)
            except Exception as e:
                self.logger.error(f"Failed to collect data for VM {vm['name']}: {str(e)}")
        
        # Find unattached disks
        unattached_disks = await self._find_unattached_disks()
        
        # Calculate totals
        total_vms = len(vm_details)
        total_cost = sum(vm.get('total_cost', 0) for vm in vm_details)
        running_vms = sum(1 for vm in vm_details if vm.get('power_state') == 'running')
        
        # Identify opportunities
        opportunities = self._identify_opportunities(vm_details, unattached_disks)
        
        return {
            "total_vms": total_vms,
            "running_vms": running_vms,
            "stopped_vms": total_vms - running_vms,
            "total_monthly_cost": total_cost,
            "vms": vm_details,
            "unattached_disks": unattached_disks,
            "opportunities": opportunities,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    async def _list_vms(self) -> List[Dict]:
        """List all VMs in subscription"""
        vms = []
        
        try:
            vm_list = await self._make_request(
                self.compute_client.virtual_machines,
                "list_all"
            )
            
            for vm in vm_list:
                vms.append({
                    "id": vm.id,
                    "name": vm.name,
                    "location": vm.location,
                    "resource_group": self._get_resource_group_from_id(vm.id),
                    "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else "Unknown",
                    "os_type": vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else "Unknown",
                    "tags": vm.tags or {}
                })
        except Exception as e:
            self.logger.error(f"Failed to list VMs: {str(e)}")
            raise
        
        return vms
    
    async def _collect_vm_data(
        self,
        vm: Dict,
        start_date: datetime,
        end_date: datetime,
        include_utilization: bool
    ) -> Dict:
        """Collect comprehensive data for a single VM"""
        
        # Get power state
        power_state = await self._get_vm_power_state(vm['resource_group'], vm['name'])
        
        # Get costs
        monthly_cost = await self._get_vm_costs(vm['id'], start_date, end_date)
        
        # Get disk costs
        disk_cost = await self._get_disk_costs(vm['resource_group'], vm['name'])
        
        # Get metrics if requested and VM is running
        metrics = {}
        if include_utilization and power_state == 'running':
            metrics = await self._get_vm_metrics(vm['id'], start_date, end_date)
        
        # Analyze utilization
        utilization_analysis = {}
        if metrics:
            utilization_analysis = self._analyze_vm_utilization(vm, metrics, monthly_cost)
        
        return {
            **vm,
            "power_state": power_state,
            "monthly_cost": monthly_cost,
            "disk_cost": disk_cost,
            "total_cost": monthly_cost + disk_cost,
            "metrics": metrics,
            "utilization_analysis": utilization_analysis
        }
    
    async def _get_vm_power_state(self, resource_group: str, vm_name: str) -> str:
        """Get VM power state"""
        try:
            instance_view = await self._make_request(
                self.compute_client.virtual_machines,
                "instance_view",
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            for status in instance_view.statuses:
                if status.code.startswith('PowerState/'):
                    return status.code.split('/')[-1].lower()
            
            return "unknown"
        except Exception as e:
            self.logger.error(f"Failed to get power state for {vm_name}: {str(e)}")
            return "unknown"
    
    async def _get_vm_costs(
        self,
        vm_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Get costs for specific VM"""
        try:
            daily_costs = await self.cost_client.get_resource_costs(
                resource_id=vm_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_cost = sum(day['cost'] for day in daily_costs)
            days = (end_date - start_date).days or 1
            monthly_cost = (total_cost / days) * 30
            
            return monthly_cost
        except Exception as e:
            self.logger.error(f"Failed to get costs for VM {vm_id}: {str(e)}")
            return 0.0
    
    async def _get_disk_costs(self, resource_group: str, vm_name: str) -> float:
        """Calculate disk costs for VM"""
        try:
            vm = await self._make_request(
                self.compute_client.virtual_machines,
                "get",
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            disk_cost = 0.0
            
            # OS disk
            if vm.storage_profile and vm.storage_profile.os_disk:
                disk_size_gb = vm.storage_profile.os_disk.disk_size_gb or 128
                disk_type = "Standard_LRS"
                if vm.storage_profile.os_disk.managed_disk:
                    disk_type = vm.storage_profile.os_disk.managed_disk.storage_account_type
                disk_cost += self._calculate_disk_cost(disk_size_gb, disk_type)
            
            # Data disks
            if vm.storage_profile and vm.storage_profile.data_disks:
                for disk in vm.storage_profile.data_disks:
                    disk_size_gb = disk.disk_size_gb or 128
                    disk_type = "Standard_LRS"
                    if disk.managed_disk:
                        disk_type = disk.managed_disk.storage_account_type
                    disk_cost += self._calculate_disk_cost(disk_size_gb, disk_type)
            
            return disk_cost
        except Exception as e:
            self.logger.error(f"Failed to get disk costs for {vm_name}: {str(e)}")
            return 0.0
    
    def _calculate_disk_cost(self, size_gb: int, disk_type: str) -> float:
        """Calculate monthly disk cost based on size and type"""
        # Approximate Azure disk pricing (USD/month)
        pricing = {
            "Standard_LRS": 0.05,      # $0.05/GB/month
            "StandardSSD_LRS": 0.075,  # $0.075/GB/month
            "Premium_LRS": 0.15,       # $0.15/GB/month
            "UltraSSD_LRS": 0.20       # $0.20/GB/month
        }
        
        rate = pricing.get(disk_type, 0.05)
        return size_gb * rate
    
    async def _get_vm_metrics(
        self,
        vm_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get CPU, memory, network metrics from Azure Monitor"""
        metrics_to_collect = {
            "Percentage CPU": "cpu",
            "Available Memory Bytes": "memory",
            "Network In Total": "network_in",
            "Network Out Total": "network_out"
        }
        
        collected_metrics = {}
        
        for metric_name, metric_key in metrics_to_collect.items():
            try:
                metric_data = await self._make_request(
                    self.monitor_client.metrics,
                    "list",
                    resource_uri=vm_id,
                    timespan=f"{start_date.isoformat()}/{end_date.isoformat()}",
                    interval='PT1H',
                    metricnames=metric_name,
                    aggregation='Average,Maximum'
                )
                
                values = []
                for item in metric_data.value:
                    for timeseries in item.timeseries:
                        for data in timeseries.data:
                            if data.average is not None:
                                values.append(data.average)
                
                if values:
                    collected_metrics[metric_key] = {
                        "average": sum(values) / len(values),
                        "max": max(values),
                        "min": min(values),
                        "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]
                    }
            except Exception as e:
                self.logger.warning(f"Failed to collect metric {metric_name}: {str(e)}")
        
        return collected_metrics
    
    def _analyze_vm_utilization(self, vm: Dict, metrics: Dict, monthly_cost: float) -> Dict:
        """Analyze VM utilization and identify issues"""
        analysis = {
            "is_idle": False,
            "is_underutilized": False,
            "spot_eligible": False,
            "recommendations": []
        }
        
        # Check if idle
        if 'cpu' in metrics:
            cpu_avg = metrics['cpu']['average']
            
            if cpu_avg < self.idle_cpu_threshold:
                analysis['is_idle'] = True
                analysis['recommendations'].append({
                    "type": "idle_vm",
                    "reason": f"CPU utilization is {cpu_avg:.1f}% (threshold: {self.idle_cpu_threshold}%)",
                    "action": "Consider stopping or deleting this VM",
                    "estimated_savings": monthly_cost * 0.95
                })
            elif cpu_avg < self.underutilized_cpu_threshold:
                analysis['is_underutilized'] = True
                # Recommend smaller VM size
                current_size = vm['vm_size']
                recommended_size = self._recommend_smaller_size(current_size)
                if recommended_size:
                    analysis['recommendations'].append({
                        "type": "underutilized_vm",
                        "reason": f"CPU utilization is {cpu_avg:.1f}% (threshold: {self.underutilized_cpu_threshold}%)",
                        "action": f"Downsize from {current_size} to {recommended_size}",
                        "estimated_savings": monthly_cost * 0.30
                    })
        
        # Check for Spot opportunity
        if vm.get('power_state') == 'running':
            # Check if workload is suitable for Spot (based on tags or naming)
            tags = vm.get('tags', {})
            is_dev_test = any(key.lower() in ['environment', 'env'] and 
                            value.lower() in ['dev', 'test', 'development', 'testing'] 
                            for key, value in tags.items())
            
            if is_dev_test or 'dev' in vm['name'].lower() or 'test' in vm['name'].lower():
                analysis['spot_eligible'] = True
                analysis['recommendations'].append({
                    "type": "spot_vm",
                    "reason": "VM is suitable for Azure Spot (dev/test workload)",
                    "action": "Migrate to Azure Spot VM",
                    "estimated_savings": monthly_cost * self.spot_savings_target
                })
        
        return analysis
    
    def _recommend_smaller_size(self, current_size: str) -> Optional[str]:
        """Recommend a smaller VM size"""
        # Simplified VM size downgrade mapping
        size_map = {
            "Standard_D4s_v3": "Standard_D2s_v3",
            "Standard_D8s_v3": "Standard_D4s_v3",
            "Standard_D16s_v3": "Standard_D8s_v3",
            "Standard_E4s_v3": "Standard_E2s_v3",
            "Standard_E8s_v3": "Standard_E4s_v3",
            "Standard_F4s_v2": "Standard_F2s_v2",
            "Standard_F8s_v2": "Standard_F4s_v2"
        }
        
        return size_map.get(current_size)
    
    async def _find_unattached_disks(self) -> List[Dict]:
        """Find disks not attached to any VM"""
        unattached = []
        
        try:
            disks = await self._make_request(
                self.compute_client.disks,
                "list"
            )
            
            for disk in disks:
                if not disk.managed_by:  # Not attached to any VM
                    disk_cost = self._calculate_disk_cost(
                        disk.disk_size_gb,
                        disk.sku.name if disk.sku else "Standard_LRS"
                    )
                    
                    unattached.append({
                        "id": disk.id,
                        "name": disk.name,
                        "resource_group": self._get_resource_group_from_id(disk.id),
                        "location": disk.location,
                        "size_gb": disk.disk_size_gb,
                        "disk_type": disk.sku.name if disk.sku else "Standard_LRS",
                        "monthly_cost": disk_cost,
                        "created_time": disk.time_created.isoformat() if disk.time_created else None
                    })
        except Exception as e:
            self.logger.error(f"Failed to find unattached disks: {str(e)}")
        
        return unattached
    
    def _identify_opportunities(self, vm_details: List[Dict], unattached_disks: List[Dict]) -> List[Dict]:
        """Identify all optimization opportunities"""
        opportunities = []
        
        # VM opportunities
        for vm in vm_details:
            if vm.get('utilization_analysis', {}).get('recommendations'):
                for rec in vm['utilization_analysis']['recommendations']:
                    opportunities.append({
                        "service": "Virtual Machines",
                        "resource_id": vm['id'],
                        "resource_name": vm['name'],
                        **rec
                    })
        
        # Unattached disk opportunities
        for disk in unattached_disks:
            opportunities.append({
                "service": "Virtual Machines",
                "type": "unattached_disk",
                "resource_id": disk['id'],
                "resource_name": disk['name'],
                "reason": f"Disk is not attached to any VM ({disk['size_gb']} GB)",
                "action": "Delete unattached disk",
                "estimated_savings": disk['monthly_cost']
            })
        
        return opportunities
