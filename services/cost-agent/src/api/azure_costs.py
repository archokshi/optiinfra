"""
Azure Cost API Endpoints

FastAPI endpoints for Azure cost collection and analysis.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from ..models.azure_models import (
    AzureTestConnectionRequest,
    AzureTestConnectionResponse,
    AzureCollectionRequest,
    AzureCollectionResponse,
    AzureCostQuery,
    AzureOpportunityQuery,
    AzureOpportunityResponse,
    AzureForecastResponse
)
from ..analyzers.azure_analyzer import AzureCostAnalyzer
from ..storage.azure_metrics import AzureMetricsStorage
from ..collectors.azure import AzureCostManagementClient

router = APIRouter(prefix="/api/v1/azure", tags=["azure"])
logger = logging.getLogger(__name__)


@router.post("/test-connection", response_model=AzureTestConnectionResponse)
async def test_azure_connection(request: AzureTestConnectionRequest):
    """
    Test Azure credentials and connection
    
    Args:
        request: Azure credentials
        
    Returns:
        Connection test results
    """
    try:
        # Try to create a Cost Management client
        client = AzureCostManagementClient(
            subscription_id=request.subscription_id,
            tenant_id=request.tenant_id,
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        # Try to get subscription costs (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        result = await client.get_subscription_costs(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get available services
        services_with_costs = await client.get_costs_by_service(
            start_date=start_date,
            end_date=end_date
        )
        
        accessible_services = list(services_with_costs.keys())
        
        return AzureTestConnectionResponse(
            success=True,
            subscription_id=request.subscription_id,
            tenant_id=request.tenant_id,
            message=f"Successfully connected to Azure subscription {request.subscription_id}",
            accessible_services=accessible_services
        )
        
    except Exception as e:
        logger.error(f"Azure connection test failed: {str(e)}")
        return AzureTestConnectionResponse(
            success=False,
            subscription_id=request.subscription_id,
            tenant_id=request.tenant_id,
            message=f"Connection failed: {str(e)}",
            accessible_services=[]
        )


@router.post("/collect", response_model=AzureCollectionResponse)
async def collect_azure_costs(request: AzureCollectionRequest):
    """
    Trigger Azure cost collection and analysis
    
    Args:
        request: Collection parameters
        
    Returns:
        Complete cost analysis
    """
    try:
        logger.info(f"Starting Azure cost collection for subscription {request.subscription_id}")
        
        # Create analyzer
        analyzer = AzureCostAnalyzer(
            subscription_id=request.subscription_id,
            tenant_id=request.tenant_id,
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        # Perform analysis
        analysis = await analyzer.analyze(
            lookback_days=request.lookback_days,
            include_utilization=request.include_utilization
        )
        
        # Store metrics in ClickHouse
        # TODO: Get ClickHouse client from config
        # storage = AzureMetricsStorage(clickhouse_client)
        # await storage.store_cost_metrics(...)
        # await storage.store_vm_metrics(...)
        # await storage.store_opportunities(...)
        
        logger.info(f"Azure cost collection completed for subscription {request.subscription_id}")
        
        return AzureCollectionResponse(**analysis)
        
    except Exception as e:
        logger.error(f"Azure cost collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


@router.post("/costs/query")
async def query_azure_costs(query: AzureCostQuery):
    """
    Query Azure cost data from ClickHouse
    
    Args:
        query: Query parameters
        
    Returns:
        Cost data matching query
    """
    try:
        # TODO: Get ClickHouse client from config
        # storage = AzureMetricsStorage(clickhouse_client)
        
        start_date = query.start_date or (datetime.utcnow() - timedelta(days=30))
        end_date = query.end_date or datetime.utcnow()
        
        # costs = await storage.query_costs(
        #     subscription_id=query.subscription_id,
        #     start_date=start_date,
        #     end_date=end_date,
        #     service=query.service
        # )
        
        # Placeholder response
        return {
            "subscription_id": query.subscription_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "costs": []
        }
        
    except Exception as e:
        logger.error(f"Azure cost query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/opportunities", response_model=AzureOpportunityResponse)
async def get_azure_opportunities(query: AzureOpportunityQuery):
    """
    Get Azure optimization opportunities
    
    Args:
        query: Query parameters
        
    Returns:
        List of optimization opportunities
    """
    try:
        # TODO: Get ClickHouse client from config
        # storage = AzureMetricsStorage(clickhouse_client)
        
        # opportunities = await storage.query_opportunities(
        #     subscription_id=query.subscription_id,
        #     min_savings=query.min_savings,
        #     limit=query.limit
        # )
        
        # Filter by service and priority if specified
        # if query.service:
        #     opportunities = [o for o in opportunities if o['service'] == query.service]
        # if query.priority:
        #     opportunities = [o for o in opportunities if o['priority'] == query.priority]
        
        # total_savings = sum(o['estimated_savings'] for o in opportunities)
        
        # Placeholder response
        return AzureOpportunityResponse(
            subscription_id=query.subscription_id,
            total_opportunities=0,
            total_potential_savings=0.0,
            opportunities=[]
        )
        
    except Exception as e:
        logger.error(f"Azure opportunities query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/forecast/{subscription_id}", response_model=AzureForecastResponse)
async def get_azure_forecast(
    subscription_id: str,
    forecast_days: int = Query(30, ge=1, le=90, description="Days to forecast")
):
    """
    Get Azure cost forecast
    
    Args:
        subscription_id: Azure subscription ID
        forecast_days: Number of days to forecast
        
    Returns:
        Cost forecast
    """
    try:
        # Get historical costs
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        client = AzureCostManagementClient(subscription_id=subscription_id)
        
        result = await client.get_subscription_costs(
            start_date=start_date,
            end_date=end_date,
            granularity="Daily"
        )
        
        daily_costs = result.get('daily_costs', [])
        
        # Simple forecast calculation
        if daily_costs:
            costs = [day['cost'] for day in daily_costs]
            avg_daily_cost = sum(costs) / len(costs)
            projected_cost = avg_daily_cost * forecast_days
            
            forecast = {
                "next_30_days": projected_cost,
                "average_daily_cost": avg_daily_cost,
                "confidence_interval": {
                    "lower": projected_cost * 0.9,
                    "upper": projected_cost * 1.1
                }
            }
        else:
            forecast = {
                "next_30_days": 0,
                "average_daily_cost": 0,
                "confidence_interval": {"lower": 0, "upper": 0}
            }
        
        return AzureForecastResponse(
            subscription_id=subscription_id,
            forecast=forecast,
            analyzed_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Azure forecast failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")
