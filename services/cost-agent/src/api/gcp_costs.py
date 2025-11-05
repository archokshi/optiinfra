"""
GCP Cost Collection API Endpoints

FastAPI routes for GCP cost collection and analysis.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from src.models.gcp_models import (
    GCPCollectionRequest,
    GCPTestConnectionRequest,
    GCPCostResponse,
    GCPConnectionTestResponse,
    GCPCostQueryRequest,
    GCPOpportunitiesRequest
)
from src.analyzers.gcp_analyzer import GCPCostAnalyzer
from src.storage.gcp_metrics import GCPMetricsStorage
from src.config import get_settings
from src.metrics import cost_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gcp", tags=["GCP Costs"])

settings = get_settings()


@router.post("/test-connection", response_model=GCPConnectionTestResponse)
async def test_gcp_connection(request: GCPTestConnectionRequest):
    """
    Test GCP connection and credentials.
    
    Args:
        request: Connection test request
    
    Returns:
        Connection test results
    """
    try:
        logger.info(f"Testing GCP connection for project: {request.project_id}")
        
        # Track API call
        cost_metrics.gcp_api_calls_total.labels(
            service='billing',
            operation='test_connection'
        ).inc()
        
        from src.collectors.gcp.billing_client import BillingClient
        
        # Initialize billing client
        billing_client = BillingClient(
            project_id=request.project_id,
            credentials_path=request.credentials_path
        )
        
        # Get billing info
        billing_info = billing_client.get_billing_info()
        
        # Test service access
        accessible_services = []
        
        try:
            from src.collectors.gcp.compute_engine import ComputeEngineCostCollector
            compute_collector = ComputeEngineCostCollector(
                project_id=request.project_id,
                credentials_path=request.credentials_path
            )
            # Try to list instances
            compute_collector._get_all_zones()
            accessible_services.append('Compute Engine')
        except Exception as e:
            logger.warning(f"Compute Engine not accessible: {e}")
        
        try:
            from src.collectors.gcp.cloud_sql import CloudSQLCostCollector
            sql_collector = CloudSQLCostCollector(
                project_id=request.project_id,
                credentials_path=request.credentials_path
            )
            sql_collector._get_all_sql_instances()
            accessible_services.append('Cloud SQL')
        except Exception as e:
            logger.warning(f"Cloud SQL not accessible: {e}")
        
        try:
            from src.collectors.gcp.cloud_storage import CloudStorageCostCollector
            storage_collector = CloudStorageCostCollector(
                project_id=request.project_id,
                credentials_path=request.credentials_path
            )
            list(storage_collector.storage_client.list_buckets(max_results=1))
            accessible_services.append('Cloud Storage')
        except Exception as e:
            logger.warning(f"Cloud Storage not accessible: {e}")
        
        return GCPConnectionTestResponse(
            success=True,
            project_id=request.project_id,
            billing_info=billing_info,
            accessible_services=accessible_services,
            message=f"Successfully connected to GCP project {request.project_id}"
        )
        
    except Exception as e:
        logger.error(f"GCP connection test failed: {e}")
        cost_metrics.gcp_api_errors_total.labels(
            service='billing',
            error_type=type(e).__name__
        ).inc()
        
        return GCPConnectionTestResponse(
            success=False,
            project_id=request.project_id,
            message=f"Connection failed: {str(e)}"
        )


@router.post("/collect", response_model=GCPCostResponse)
async def collect_gcp_costs(
    request: GCPCollectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Collect and analyze GCP costs.
    
    Args:
        request: Collection request
        background_tasks: FastAPI background tasks
    
    Returns:
        Cost analysis results
    """
    try:
        logger.info(f"Starting GCP cost collection for project: {request.project_id}")
        
        # Track collection start
        import time
        start_time = time.time()
        
        cost_metrics.gcp_api_calls_total.labels(
            service='cost_analyzer',
            operation='collect'
        ).inc()
        
        # Initialize analyzer
        analyzer = GCPCostAnalyzer(
            project_id=request.project_id,
            credentials_path=request.credentials_path,
            billing_account_id=request.billing_account_id,
            billing_dataset=request.billing_dataset
        )
        
        # Perform analysis
        analysis_result = analyzer.analyze_all_services(
            start_date=request.start_date,
            end_date=request.end_date,
            lookback_days=request.lookback_days
        )
        
        # Store metrics in background
        background_tasks.add_task(
            store_gcp_metrics,
            request.project_id,
            analysis_result
        )
        
        # Track collection duration
        duration = time.time() - start_time
        cost_metrics.gcp_cost_collection_duration_seconds.observe(duration)
        
        # Update cost metrics
        total_cost = analysis_result.get('total_cost', 0.0)
        cost_metrics.gcp_total_monthly_cost_usd.labels(
            service='all',
            region='all'
        ).set(total_cost)
        
        # Update waste metrics
        total_savings = analysis_result.get('optimization', {}).get('total_potential_savings', 0.0)
        cost_metrics.gcp_waste_identified_usd.labels(service='all').set(total_savings)
        
        # Update opportunity count
        total_opps = analysis_result.get('optimization', {}).get('total_opportunities', 0)
        cost_metrics.gcp_optimization_opportunities.labels(type='all').set(total_opps)
        
        logger.info(f"GCP cost collection completed in {duration:.2f}s")
        
        return GCPCostResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"GCP cost collection failed: {e}")
        cost_metrics.gcp_api_errors_total.labels(
            service='cost_analyzer',
            error_type=type(e).__name__
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/costs/query")
async def query_gcp_costs(request: GCPCostQueryRequest) -> Dict[str, Any]:
    """
    Query GCP costs from storage.
    
    Args:
        request: Query request
    
    Returns:
        Cost data
    """
    try:
        storage = GCPMetricsStorage(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            database=settings.CLICKHOUSE_DATABASE
        )
        
        trends = storage.query_cost_trends(
            project_id=request.project_id,
            days=30,
            service=request.service
        )
        
        return {
            'project_id': request.project_id,
            'trends': trends
        }
        
    except Exception as e:
        logger.error(f"Failed to query GCP costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities")
async def get_gcp_opportunities(request: GCPOpportunitiesRequest) -> Dict[str, Any]:
    """
    Get GCP optimization opportunities.
    
    Args:
        request: Opportunities request
    
    Returns:
        Optimization opportunities
    """
    try:
        storage = GCPMetricsStorage(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            database=settings.CLICKHOUSE_DATABASE
        )
        
        opportunities = storage.query_top_opportunities(
            project_id=request.project_id,
            limit=request.limit
        )
        
        # Filter by service if specified
        if request.service:
            opportunities = [
                opp for opp in opportunities
                if opp['service'] == request.service
            ]
        
        # Filter by minimum savings
        if request.min_savings > 0:
            opportunities = [
                opp for opp in opportunities
                if opp['estimated_savings'] >= request.min_savings
            ]
        
        total_savings = sum(opp['estimated_savings'] for opp in opportunities)
        
        return {
            'project_id': request.project_id,
            'total_opportunities': len(opportunities),
            'total_potential_savings': round(total_savings, 2),
            'opportunities': opportunities
        }
        
    except Exception as e:
        logger.error(f"Failed to get GCP opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{project_id}")
async def get_gcp_forecast(
    project_id: str,
    forecast_days: int = 30
) -> Dict[str, Any]:
    """
    Get GCP cost forecast.
    
    Args:
        project_id: GCP project ID
        forecast_days: Days to forecast
    
    Returns:
        Forecast data
    """
    try:
        from src.collectors.gcp.billing_client import BillingClient
        
        billing_client = BillingClient(
            project_id=project_id,
            credentials_path=settings.GCP_CREDENTIALS_PATH
        )
        
        forecast = billing_client.get_cost_forecast(forecast_days)
        
        return {
            'project_id': project_id,
            'forecast': forecast
        }
        
    except Exception as e:
        logger.error(f"Failed to get GCP forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def store_gcp_metrics(project_id: str, analysis_result: Dict[str, Any]):
    """
    Store GCP metrics in ClickHouse (background task).
    
    Args:
        project_id: GCP project ID
        analysis_result: Analysis results
    """
    try:
        storage = GCPMetricsStorage(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            database=settings.CLICKHOUSE_DATABASE
        )
        
        # Store cost metrics
        storage.store_cost_metrics(
            project_id=project_id,
            cost_data=analysis_result.get('cost_breakdown', {})
        )
        
        # Store service-specific metrics
        services = analysis_result.get('services', {})
        
        if 'compute_engine' in services:
            compute_data = services['compute_engine']
            storage.store_compute_metrics(
                project_id=project_id,
                instances=compute_data.get('instances', [])
            )
        
        if 'cloud_sql' in services:
            sql_data = services['cloud_sql']
            storage.store_sql_metrics(
                project_id=project_id,
                instances=sql_data.get('instances', [])
            )
        
        if 'cloud_functions' in services:
            functions_data = services['cloud_functions']
            storage.store_functions_metrics(
                project_id=project_id,
                functions=functions_data.get('functions', [])
            )
        
        if 'cloud_storage' in services:
            storage_data = services['cloud_storage']
            storage.store_storage_metrics(
                project_id=project_id,
                buckets=storage_data.get('buckets', [])
            )
        
        # Store opportunities
        opportunities = analysis_result.get('optimization', {}).get('opportunities', [])
        storage.store_opportunities(
            project_id=project_id,
            opportunities=opportunities
        )
        
        logger.info(f"Successfully stored GCP metrics for {project_id}")
        
    except Exception as e:
        logger.error(f"Failed to store GCP metrics: {e}")
