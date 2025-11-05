"""
AWS Cost Collection API Endpoints

FastAPI endpoints for AWS cost collection and analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.models.aws_models import (
    AWSCollectionRequest,
    AWSCollectionResponse,
    AWSCostResponse,
    AWSOpportunitiesResponse,
    AWSAnalysisRequest,
    AWSAnalysisResponse,
    AWSConnectionTestResponse,
    AWSJobStatusResponse
)
from src.analyzers.aws_analyzer import AWSCostAnalyzer
from src.storage.aws_metrics import AWSMetricsStorage
from src.config import settings
from src.metrics import cost_metrics

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job tracking (in production, use Redis)
active_jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/test-connection", response_model=AWSConnectionTestResponse)
async def test_aws_connection():
    """
    Test AWS connection and permissions.
    
    Returns:
        Connection test results
    """
    try:
        analyzer = AWSCostAnalyzer(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Test credentials
        account_id = analyzer.cost_explorer.get_account_id()
        
        # Test Cost Explorer access
        try:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            analyzer.cost_explorer.get_cost_and_usage(start_date, end_date)
            cost_explorer_available = True
        except Exception as e:
            logger.warning(f"Cost Explorer not available: {e}")
            cost_explorer_available = False
        
        # Get regions
        regions = analyzer.cost_explorer.get_regions()
        
        return AWSConnectionTestResponse(
            status="connected",
            account_id=account_id,
            regions=regions[:5],  # Return first 5 regions
            cost_explorer_available=cost_explorer_available,
            permissions_valid=True
        )
        
    except Exception as e:
        logger.error(f"AWS connection test failed: {e}")
        return AWSConnectionTestResponse(
            status="failed",
            cost_explorer_available=False,
            permissions_valid=False,
            error=str(e)
        )


@router.post("/collect", response_model=AWSCollectionResponse)
async def collect_aws_costs(request: AWSCollectionRequest):
    """
    Trigger AWS cost collection.
    
    Args:
        request: Collection request parameters
    
    Returns:
        Collection job details
    """
    try:
        job_id = f"aws-collect-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Validate dates
        try:
            start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')
            
            if start_dt >= end_dt:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be before end_date"
                )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {e}"
            )
        
        # Determine services to collect
        services = request.services or ['EC2', 'RDS', 'Lambda', 'S3']
        
        # Create job record
        active_jobs[job_id] = {
            'job_id': job_id,
            'status': 'running',
            'progress': 0.0,
            'started_at': datetime.utcnow().isoformat(),
            'services': services,
            'dry_run': request.dry_run
        }
        
        # Start collection in background
        asyncio.create_task(
            _run_collection(
                job_id,
                request.start_date,
                request.end_date,
                services,
                request.analyze,
                request.dry_run
            )
        )
        
        # Update metrics
        cost_metrics.aws_api_calls_total.labels(
            service='cost_agent',
            operation='collect'
        ).inc()
        
        return AWSCollectionResponse(
            status="started",
            job_id=job_id,
            estimated_duration_seconds=30,
            services_to_collect=len(services),
            regions_to_scan=len(settings.AWS_REGIONS)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=AWSJobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of collection job.
    
    Args:
        job_id: Job ID
    
    Returns:
        Job status
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    return AWSJobStatusResponse(**job)


@router.get("/costs", response_model=AWSCostResponse)
async def get_aws_costs(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    service: Optional[str] = Query(None, description="Filter by service"),
    region: Optional[str] = Query(None, description="Filter by region")
):
    """
    Get AWS cost data.
    
    Args:
        start_date: Start date
        end_date: End date
        service: Optional service filter
        region: Optional region filter
    
    Returns:
        Cost data
    """
    try:
        analyzer = AWSCostAnalyzer(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Get cost data
        cost_data = analyzer.cost_explorer.get_cost_and_usage(
            start_date,
            end_date,
            granularity='DAILY',
            group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        # Filter if requested
        if service:
            cost_data['by_service'] = {
                k: v for k, v in cost_data['by_service'].items()
                if service.lower() in k.lower()
            }
        
        return AWSCostResponse(
            time_period={'start': start_date, 'end': end_date},
            total_cost=cost_data['total_cost'],
            by_service=cost_data['by_service'],
            by_region=cost_data.get('by_region', {}),
            daily_breakdown=cost_data['daily_breakdown']
        )
        
    except Exception as e:
        logger.error(f"Failed to get costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/ec2")
async def get_ec2_costs(
    include_instances: bool = Query(False, description="Include instance details")
):
    """
    Get EC2-specific costs.
    
    Args:
        include_instances: Include instance details
    
    Returns:
        EC2 cost breakdown
    """
    try:
        from src.collectors.aws.ec2 import EC2CostCollector
        
        collector = EC2CostCollector(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Get instance costs
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        instances = collector.collect_instance_costs(
            start_date,
            end_date,
            include_utilization=True
        )
        
        # Calculate totals
        total_cost = sum(inst.get('monthly_cost', 0) for inst in instances)
        
        # Group by instance type
        by_type = {}
        for inst in instances:
            inst_type = inst['instance_type']
            if inst_type not in by_type:
                by_type[inst_type] = {'count': 0, 'cost': 0.0}
            by_type[inst_type]['count'] += 1
            by_type[inst_type]['cost'] += inst.get('monthly_cost', 0)
        
        # Get EBS costs
        ebs_costs = collector.get_ebs_costs()
        
        response = {
            'total_ec2_cost': round(total_cost, 2),
            'instance_count': len(instances),
            'by_instance_type': by_type,
            'ebs_cost': ebs_costs.get('total_ebs_cost', 0),
            'data_transfer_cost': 0.0  # Would need actual data
        }
        
        if include_instances:
            response['instances'] = instances
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get EC2 costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/rds")
async def get_rds_costs():
    """
    Get RDS-specific costs.
    
    Returns:
        RDS cost breakdown
    """
    try:
        from src.collectors.aws.rds import RDSCostCollector
        
        collector = RDSCostCollector(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        instances = collector.collect_rds_costs(include_utilization=True)
        
        total_cost = sum(inst.get('monthly_cost', 0) for inst in instances)
        
        # Group by engine
        by_engine = {}
        for inst in instances:
            engine = inst['engine']
            if engine not in by_engine:
                by_engine[engine] = {'count': 0, 'cost': 0.0}
            by_engine[engine]['count'] += 1
            by_engine[engine]['cost'] += inst.get('monthly_cost', 0)
        
        # Get storage costs
        storage_costs = collector.analyze_storage_costs()
        
        return {
            'total_rds_cost': round(total_cost, 2),
            'instance_count': len(instances),
            'by_engine': by_engine,
            'storage_cost': storage_costs.get('total_storage_cost', 0),
            'backup_cost': storage_costs.get('total_backup_cost', 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get RDS costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities", response_model=AWSOpportunitiesResponse)
async def get_optimization_opportunities(
    min_savings: float = Query(0.0, description="Minimum savings threshold"),
    service: Optional[str] = Query(None, description="Filter by service"),
    opportunity_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """
    Get optimization opportunities.
    
    Args:
        min_savings: Minimum savings threshold
        service: Service filter
        opportunity_type: Type filter
        priority: Priority filter
    
    Returns:
        List of opportunities
    """
    try:
        analyzer = AWSCostAnalyzer(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Get opportunities
        opportunities = analyzer._identify_all_opportunities()
        
        # Apply filters
        filtered = opportunities
        
        if min_savings > 0:
            filtered = [o for o in filtered if o.get('estimated_savings', 0) >= min_savings]
        
        if service:
            filtered = [o for o in filtered if o.get('service', '').lower() == service.lower()]
        
        if opportunity_type:
            filtered = [o for o in filtered if o.get('type', '').lower() == opportunity_type.lower()]
        
        if priority:
            filtered = [o for o in filtered if o.get('priority', '').lower() == priority.lower()]
        
        total_savings = sum(o.get('estimated_savings', 0) for o in filtered)
        
        return AWSOpportunitiesResponse(
            total_opportunities=len(filtered),
            total_potential_savings=round(total_savings, 2),
            opportunities=filtered
        )
        
    except Exception as e:
        logger.error(f"Failed to get opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis", response_model=AWSAnalysisResponse)
async def run_comprehensive_analysis(request: AWSAnalysisRequest):
    """
    Run comprehensive AWS cost analysis.
    
    Args:
        request: Analysis parameters
    
    Returns:
        Complete analysis results
    """
    try:
        analyzer = AWSCostAnalyzer(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Date range: last 30 days
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Run analysis
        analysis = analyzer.analyze_all_services(
            start_date,
            end_date,
            detect_anomalies=request.detect_anomalies,
            forecast=request.forecast_30d
        )
        
        # Generate summary
        summary_report = analyzer.generate_summary_report(analysis)
        
        return AWSAnalysisResponse(
            analysis_id=analysis['analysis_id'],
            timestamp=analysis['timestamp'],
            summary=analysis['summary'],
            trends=analysis.get('trends') if request.analyze_trends else None,
            anomalies=analysis.get('anomalies') if request.detect_anomalies else None,
            forecast=analysis.get('forecast') if request.forecast_30d else None,
            recommendations_summary=summary_report
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_aws_data():
    """
    Force refresh of AWS cost data.
    
    Returns:
        Refresh status
    """
    try:
        # Trigger collection for last 7 days
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        request = AWSCollectionRequest(
            start_date=start_date,
            end_date=end_date,
            analyze=True,
            dry_run=False
        )
        
        return await collect_aws_costs(request)
        
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_collection(
    job_id: str,
    start_date: str,
    end_date: str,
    services: List[str],
    analyze: bool,
    dry_run: bool
):
    """
    Background task to run cost collection.
    
    Args:
        job_id: Job ID
        start_date: Start date
        end_date: End date
        services: Services to collect
        analyze: Run analysis
        dry_run: Dry run mode
    """
    try:
        # Update job status
        active_jobs[job_id]['current_service'] = 'initializing'
        active_jobs[job_id]['progress'] = 0.1
        
        # Initialize analyzer
        analyzer = AWSCostAnalyzer(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_DEFAULT_REGION
        )
        
        # Run analysis
        active_jobs[job_id]['current_service'] = 'analyzing'
        active_jobs[job_id]['progress'] = 0.5
        
        analysis = analyzer.analyze_all_services(
            start_date,
            end_date,
            detect_anomalies=analyze,
            forecast=analyze
        )
        
        # Store results if not dry run
        if not dry_run:
            active_jobs[job_id]['current_service'] = 'storing'
            active_jobs[job_id]['progress'] = 0.8
            
            storage = AWSMetricsStorage()
            storage.store_cost_metrics(analysis['cost_breakdown'])
            storage.store_optimization_opportunities(analysis['opportunities'])
        
        # Update job status
        active_jobs[job_id]['status'] = 'completed'
        active_jobs[job_id]['progress'] = 1.0
        active_jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
        active_jobs[job_id]['duration_seconds'] = (
            datetime.fromisoformat(active_jobs[job_id]['completed_at']) -
            datetime.fromisoformat(active_jobs[job_id]['started_at'])
        ).total_seconds()
        active_jobs[job_id]['results'] = {
            'total_cost': analysis['summary']['total_monthly_cost'],
            'services_collected': len(services),
            'resources_analyzed': sum(
                len(analysis['service_details'][svc].get('instances', []))
                for svc in ['ec2', 'rds', 'lambda', 's3']
                if svc in analysis['service_details']
            ),
            'opportunities_identified': len(analysis['opportunities']),
            'estimated_savings': analysis['summary']['optimization_potential']
        }
        
        # Update metrics
        cost_metrics.aws_total_monthly_cost_usd.labels(
            service='total',
            region='all'
        ).set(analysis['summary']['total_monthly_cost'])
        
        cost_metrics.aws_waste_identified_usd.labels(
            service='all'
        ).set(analysis['summary']['total_waste'])
        
        logger.info(f"Collection job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Collection job {job_id} failed: {e}")
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)
        active_jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()
