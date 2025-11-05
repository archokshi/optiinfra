"""
Prometheus metrics for spot migration workflow.
Production-ready metrics for monitoring and alerting.
"""
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Counters
spot_migrations_total = Counter(
    'spot_migrations_total',
    'Total number of spot migrations',
    ['customer_id', 'cloud_provider', 'status']
)

spot_migration_errors_total = Counter(
    'spot_migration_errors_total',
    'Total number of spot migration errors',
    ['customer_id', 'error_type']
)

spot_opportunities_identified_total = Counter(
    'spot_opportunities_identified_total',
    'Total number of spot opportunities identified',
    ['customer_id', 'cloud_provider']
)

# Histograms
spot_migration_duration_seconds = Histogram(
    'spot_migration_duration_seconds',
    'Duration of spot migration workflow in seconds',
    ['customer_id', 'phase'],
    buckets=[1, 2, 5, 10, 30, 60, 120, 300, 600]
)

spot_savings_amount_dollars = Histogram(
    'spot_savings_amount_dollars',
    'Amount saved through spot migration in dollars',
    ['customer_id', 'cloud_provider'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
)

spot_instances_analyzed = Histogram(
    'spot_instances_analyzed',
    'Number of instances analyzed for spot migration',
    ['customer_id', 'cloud_provider'],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

# Gauges
spot_opportunities_found = Gauge(
    'spot_opportunities_found',
    'Number of spot opportunities currently identified',
    ['customer_id']
)

spot_instances_migrated = Gauge(
    'spot_instances_migrated',
    'Number of instances migrated to spot',
    ['customer_id', 'phase']
)

spot_migration_success_rate = Gauge(
    'spot_migration_success_rate',
    'Success rate of spot migrations (0-1)',
    ['customer_id']
)


def record_migration_start(customer_id: str, cloud_provider: str):
    """
    Record the start of a spot migration.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider (aws, gcp, azure)
    """
    try:
        spot_migrations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='started'
        ).inc()
        
        logger.debug(
            f"Recorded migration start for {customer_id} on {cloud_provider}",
            extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
        )
    except Exception as e:
        logger.error(f"Failed to record migration start metric: {e}")


def record_migration_complete(
    customer_id: str,
    cloud_provider: str,
    duration: float,
    savings: float,
    opportunities: int = 0
):
    """
    Record successful completion of a spot migration.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider (aws, gcp, azure)
        duration: Duration in seconds
        savings: Total savings in dollars
        opportunities: Number of opportunities found
    """
    try:
        spot_migrations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='success'
        ).inc()
        
        spot_migration_duration_seconds.labels(
            customer_id=customer_id,
            phase='complete'
        ).observe(duration)
        
        spot_savings_amount_dollars.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).observe(savings)
        
        if opportunities > 0:
            spot_opportunities_found.labels(customer_id=customer_id).set(opportunities)
        
        logger.debug(
            f"Recorded migration complete for {customer_id}: ${savings:.2f} saved",
            extra={
                "customer_id": customer_id,
                "savings": savings,
                "duration": duration
            }
        )
    except Exception as e:
        logger.error(f"Failed to record migration complete metric: {e}")


def record_migration_error(customer_id: str, error_type: str):
    """
    Record a spot migration error.
    
    Args:
        customer_id: Customer identifier
        error_type: Type of error (auth, throttling, validation, etc.)
    """
    try:
        spot_migration_errors_total.labels(
            customer_id=customer_id,
            error_type=error_type
        ).inc()
        
        logger.debug(
            f"Recorded migration error for {customer_id}: {error_type}",
            extra={"customer_id": customer_id, "error_type": error_type}
        )
    except Exception as e:
        logger.error(f"Failed to record migration error metric: {e}")


def record_analysis_phase(
    customer_id: str,
    cloud_provider: str,
    instances_count: int,
    opportunities_count: int,
    duration: float
):
    """
    Record metrics for the analysis phase.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
        instances_count: Number of instances analyzed
        opportunities_count: Number of opportunities found
        duration: Duration in seconds
    """
    try:
        spot_instances_analyzed.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).observe(instances_count)
        
        spot_opportunities_identified_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).inc(opportunities_count)
        
        spot_migration_duration_seconds.labels(
            customer_id=customer_id,
            phase='analyze'
        ).observe(duration)
        
        logger.debug(
            f"Recorded analysis phase: {instances_count} instances, {opportunities_count} opportunities",
            extra={
                "customer_id": customer_id,
                "instances_count": instances_count,
                "opportunities_count": opportunities_count
            }
        )
    except Exception as e:
        logger.error(f"Failed to record analysis phase metrics: {e}")


def record_execution_phase(
    customer_id: str,
    phase: str,
    instances_migrated: int,
    duration: float
):
    """
    Record metrics for the execution phase.
    
    Args:
        customer_id: Customer identifier
        phase: Execution phase (10%, 50%, 100%)
        instances_migrated: Number of instances migrated
        duration: Duration in seconds
    """
    try:
        spot_instances_migrated.labels(
            customer_id=customer_id,
            phase=phase
        ).set(instances_migrated)
        
        spot_migration_duration_seconds.labels(
            customer_id=customer_id,
            phase=f'execute_{phase}'
        ).observe(duration)
        
        logger.debug(
            f"Recorded execution phase {phase}: {instances_migrated} instances migrated",
            extra={
                "customer_id": customer_id,
                "phase": phase,
                "instances_migrated": instances_migrated
            }
        )
    except Exception as e:
        logger.error(f"Failed to record execution phase metrics: {e}")


def update_success_rate(customer_id: str, success_rate: float):
    """
    Update the spot migration success rate gauge.
    
    Args:
        customer_id: Customer identifier
        success_rate: Success rate (0.0 to 1.0)
    """
    try:
        spot_migration_success_rate.labels(
            customer_id=customer_id
        ).set(success_rate)
        
        logger.debug(
            f"Updated success rate for customer {customer_id}: {success_rate:.2%}",
            extra={"customer_id": customer_id, "success_rate": success_rate}
        )
    except Exception as e:
        logger.error(f"Failed to update success rate: {e}")


# ============================================================================
# RI Optimization Metrics
# ============================================================================

# Counters
ri_optimizations_total = Counter(
    'ri_optimizations_total',
    'Total RI optimizations',
    ['customer_id', 'cloud_provider', 'status']
)

ri_optimization_errors_total = Counter(
    'ri_optimization_errors_total',
    'Total RI optimization errors',
    ['customer_id', 'error_type']
)

ri_recommendations_total = Counter(
    'ri_recommendations_total',
    'Total RI recommendations generated',
    ['customer_id', 'service_type', 'term']
)

# Histograms
ri_savings_amount_dollars = Histogram(
    'ri_savings_amount_dollars',
    'RI savings amount distribution',
    ['customer_id', 'term'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

ri_breakeven_months = Histogram(
    'ri_breakeven_months',
    'RI break-even period distribution',
    ['customer_id', 'payment_option'],
    buckets=[3, 6, 9, 12, 18, 24, 30, 36]
)

ri_optimization_duration_seconds = Histogram(
    'ri_optimization_duration_seconds',
    'RI optimization duration',
    ['customer_id', 'cloud_provider'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Gauges
ri_coverage_percent = Gauge(
    'ri_coverage_percent',
    'RI coverage percentage',
    ['customer_id', 'service_type']
)

ri_utilization_percent = Gauge(
    'ri_utilization_percent',
    'RI utilization percentage',
    ['customer_id', 'service_type']
)


def record_ri_optimization_start(customer_id: str, cloud_provider: str):
    """
    Record RI optimization start.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
    """
    try:
        ri_optimizations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='started'
        ).inc()
        
        logger.debug(
            f"Recorded RI optimization start for customer {customer_id}",
            extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
        )
    except Exception as e:
        logger.error(f"Failed to record RI optimization start: {e}")


def record_ri_optimization_complete(
    customer_id: str,
    cloud_provider: str,
    duration: float,
    savings: float,
    recommendations: int
):
    """
    Record RI optimization completion.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
        duration: Duration in seconds
        savings: Total annual savings
        recommendations: Number of recommendations
    """
    try:
        ri_optimizations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='completed'
        ).inc()
        
        ri_optimization_duration_seconds.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).observe(duration)
        
        logger.info(
            f"Recorded RI optimization completion: {recommendations} recommendations, ${savings:.2f} savings",
            extra={
                "customer_id": customer_id,
                "cloud_provider": cloud_provider,
                "duration": duration,
                "savings": savings,
                "recommendations": recommendations
            }
        )
    except Exception as e:
        logger.error(f"Failed to record RI optimization completion: {e}")


def record_ri_optimization_error(customer_id: str, error_type: str):
    """
    Record RI optimization error.
    
    Args:
        customer_id: Customer identifier
        error_type: Type of error
    """
    try:
        ri_optimization_errors_total.labels(
            customer_id=customer_id,
            error_type=error_type
        ).inc()
        
        logger.debug(
            f"Recorded RI optimization error for customer {customer_id}: {error_type}",
            extra={"customer_id": customer_id, "error_type": error_type}
        )
    except Exception as e:
        logger.error(f"Failed to record RI optimization error: {e}")


def record_ri_recommendation(
    customer_id: str,
    service_type: str,
    term: str,
    savings: float,
    breakeven_months: int,
    payment_option: str
):
    """
    Record individual RI recommendation.
    
    Args:
        customer_id: Customer identifier
        service_type: Service type (ec2, rds, etc.)
        term: RI term (1year or 3year)
        savings: Annual savings
        breakeven_months: Break-even period in months
        payment_option: Payment option
    """
    try:
        ri_recommendations_total.labels(
            customer_id=customer_id,
            service_type=service_type,
            term=term
        ).inc()
        
        ri_savings_amount_dollars.labels(
            customer_id=customer_id,
            term=term
        ).observe(savings)
        
        ri_breakeven_months.labels(
            customer_id=customer_id,
            payment_option=payment_option
        ).observe(breakeven_months)
        
        logger.debug(
            f"Recorded RI recommendation: {service_type} {term}, ${savings:.2f} savings",
            extra={
                "customer_id": customer_id,
                "service_type": service_type,
                "term": term,
                "savings": savings
            }
        )
    except Exception as e:
        logger.error(f"Failed to record RI recommendation: {e}")


def update_ri_coverage(customer_id: str, service_type: str, coverage: float):
    """
    Update RI coverage metric.
    
    Args:
        customer_id: Customer identifier
        service_type: Service type
        coverage: Coverage percentage (0-100)
    """
    try:
        ri_coverage_percent.labels(
            customer_id=customer_id,
            service_type=service_type
        ).set(coverage)
        
        logger.debug(
            f"Updated RI coverage for {customer_id}/{service_type}: {coverage:.1f}%",
            extra={"customer_id": customer_id, "service_type": service_type, "coverage": coverage}
        )
    except Exception as e:
        logger.error(f"Failed to update RI coverage: {e}")


def update_ri_utilization(customer_id: str, service_type: str, utilization: float):
    """
    Update RI utilization metric.
    
    Args:
        customer_id: Customer identifier
        service_type: Service type
        utilization: Utilization percentage (0-100)
    """
    try:
        ri_utilization_percent.labels(
            customer_id=customer_id,
            service_type=service_type
        ).set(utilization)
        
        logger.debug(
            f"Updated RI utilization for {customer_id}/{service_type}: {utilization:.1f}%",
            extra={"customer_id": customer_id, "service_type": service_type, "utilization": utilization}
        )
    except Exception as e:
        logger.error(f"Failed to update RI utilization: {e}")


# ============================================================================
# Right-Sizing Optimization Metrics
# ============================================================================

# Counters
rightsizing_optimizations_total = Counter(
    'rightsizing_optimizations_total',
    'Total right-sizing optimizations',
    ['customer_id', 'cloud_provider', 'status']
)

rightsizing_optimization_errors_total = Counter(
    'rightsizing_optimization_errors_total',
    'Total right-sizing optimization errors',
    ['customer_id', 'error_type']
)

rightsizing_recommendations_total = Counter(
    'rightsizing_recommendations_total',
    'Total right-sizing recommendations generated',
    ['customer_id', 'optimization_type', 'risk_level']
)

# Histograms
rightsizing_savings_percent = Histogram(
    'rightsizing_savings_percent',
    'Right-sizing savings percentage distribution',
    ['customer_id', 'optimization_type'],
    buckets=[10, 20, 30, 40, 50, 60, 70, 80]
)

rightsizing_utilization_gap = Histogram(
    'rightsizing_utilization_gap',
    'Utilization gap (over/under-provisioning)',
    ['customer_id', 'resource_type'],
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90]
)

rightsizing_optimization_duration_seconds = Histogram(
    'rightsizing_optimization_duration_seconds',
    'Right-sizing optimization duration',
    ['customer_id', 'cloud_provider'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Gauges
rightsizing_optimization_candidates = Gauge(
    'rightsizing_optimization_candidates',
    'Number of instances eligible for right-sizing',
    ['customer_id', 'provisioning_issue']
)

rightsizing_average_cpu_utilization = Gauge(
    'rightsizing_average_cpu_utilization',
    'Average CPU utilization across instances',
    ['customer_id', 'instance_family']
)

rightsizing_average_memory_utilization = Gauge(
    'rightsizing_average_memory_utilization',
    'Average memory utilization across instances',
    ['customer_id', 'instance_family']
)


def record_rightsizing_optimization_start(customer_id: str, cloud_provider: str):
    """
    Record right-sizing optimization start.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
    """
    try:
        rightsizing_optimizations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='started'
        ).inc()
        
        logger.debug(
            f"Recorded right-sizing optimization start for customer {customer_id}",
            extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
        )
    except Exception as e:
        logger.error(f"Failed to record right-sizing optimization start: {e}")


def record_rightsizing_optimization_complete(
    customer_id: str,
    cloud_provider: str,
    duration: float,
    savings: float,
    recommendations: int
):
    """
    Record right-sizing optimization completion.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
        duration: Duration in seconds
        savings: Total annual savings
        recommendations: Number of recommendations
    """
    try:
        rightsizing_optimizations_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            status='completed'
        ).inc()
        
        rightsizing_optimization_duration_seconds.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).observe(duration)
        
        logger.info(
            f"Recorded right-sizing optimization completion: {recommendations} recommendations, ${savings:.2f} savings",
            extra={
                "customer_id": customer_id,
                "cloud_provider": cloud_provider,
                "duration": duration,
                "savings": savings,
                "recommendations": recommendations
            }
        )
    except Exception as e:
        logger.error(f"Failed to record right-sizing optimization completion: {e}")


def record_rightsizing_recommendation(
    customer_id: str,
    optimization_type: str,
    risk_level: str,
    savings_percent: float
):
    """
    Record a right-sizing recommendation.
    
    Args:
        customer_id: Customer identifier
        optimization_type: Type of optimization (downsize, upsize, family_change)
        risk_level: Risk level (low, medium, high)
        savings_percent: Savings percentage
    """
    try:
        rightsizing_recommendations_total.labels(
            customer_id=customer_id,
            optimization_type=optimization_type,
            risk_level=risk_level
        ).inc()
        
        rightsizing_savings_percent.labels(
            customer_id=customer_id,
            optimization_type=optimization_type
        ).observe(savings_percent)
        
        logger.debug(
            f"Recorded right-sizing recommendation: {optimization_type}, {risk_level} risk, {savings_percent:.1f}% savings",
            extra={
                "customer_id": customer_id,
                "optimization_type": optimization_type,
                "risk_level": risk_level,
                "savings_percent": savings_percent
            }
        )
    except Exception as e:
        logger.error(f"Failed to record right-sizing recommendation: {e}")


def update_utilization_metrics(
    customer_id: str,
    instance_family: str,
    avg_cpu: float,
    avg_memory: float
):
    """
    Update utilization metrics for an instance family.
    
    Args:
        customer_id: Customer identifier
        instance_family: Instance family (e.g., t3, m5)
        avg_cpu: Average CPU utilization
        avg_memory: Average memory utilization
    """
    try:
        rightsizing_average_cpu_utilization.labels(
            customer_id=customer_id,
            instance_family=instance_family
        ).set(avg_cpu)
        
        rightsizing_average_memory_utilization.labels(
            customer_id=customer_id,
            instance_family=instance_family
        ).set(avg_memory)
        
        logger.debug(
            f"Updated utilization metrics for {customer_id}/{instance_family}: CPU={avg_cpu:.1f}%, Memory={avg_memory:.1f}%",
            extra={
                "customer_id": customer_id,
                "instance_family": instance_family,
                "avg_cpu": avg_cpu,
                "avg_memory": avg_memory
            }
        )
    except Exception as e:
        logger.error(f"Failed to update utilization metrics: {e}")


def record_optimization_candidates(
    customer_id: str,
    over_provisioned: int,
    under_provisioned: int
):
    """
    Record optimization candidate counts.
    
    Args:
        customer_id: Customer identifier
        over_provisioned: Number of over-provisioned instances
        under_provisioned: Number of under-provisioned instances
    """
    try:
        rightsizing_optimization_candidates.labels(
            customer_id=customer_id,
            provisioning_issue='over_provisioned'
        ).set(over_provisioned)
        
        rightsizing_optimization_candidates.labels(
            customer_id=customer_id,
            provisioning_issue='under_provisioned'
        ).set(under_provisioned)
        
        logger.debug(
            f"Recorded optimization candidates for {customer_id}: over={over_provisioned}, under={under_provisioned}",
            extra={
                "customer_id": customer_id,
                "over_provisioned": over_provisioned,
                "under_provisioned": under_provisioned
            }
        )
    except Exception as e:
        logger.error(f"Failed to record optimization candidates: {e}")


# ============================================================================
# Analysis Engine Metrics
# ============================================================================

# Counters
analysis_engine_runs_total = Counter(
    'analysis_engine_runs_total',
    'Total analysis engine runs',
    ['customer_id', 'cloud_provider', 'analysis_type', 'status']
)

idle_resources_detected_total = Counter(
    'idle_resources_detected_total',
    'Total idle resources detected',
    ['customer_id', 'resource_type', 'severity']
)

anomalies_detected_total = Counter(
    'anomalies_detected_total',
    'Total anomalies detected',
    ['customer_id', 'anomaly_type', 'severity']
)

# Histograms
idle_resource_waste_dollars = Histogram(
    'idle_resource_waste_dollars',
    'Idle resource waste amount distribution',
    ['customer_id', 'resource_type'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

anomaly_deviation_percent = Histogram(
    'anomaly_deviation_percent',
    'Anomaly deviation percentage distribution',
    ['customer_id', 'anomaly_type'],
    buckets=[10, 25, 50, 100, 200, 500, 1000]
)

analysis_engine_duration_seconds = Histogram(
    'analysis_engine_duration_seconds',
    'Analysis engine execution duration',
    ['customer_id', 'cloud_provider'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# Gauges
total_idle_resources = Gauge(
    'total_idle_resources',
    'Current number of idle resources',
    ['customer_id', 'severity']
)

total_monthly_waste_dollars = Gauge(
    'total_monthly_waste_dollars',
    'Total monthly waste from idle resources',
    ['customer_id']
)

active_anomalies = Gauge(
    'active_anomalies',
    'Current number of active anomalies',
    ['customer_id', 'anomaly_type']
)


def record_analysis_engine_start(customer_id: str, cloud_provider: str):
    """
    Record analysis engine start.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
    """
    try:
        analysis_engine_runs_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            analysis_type='idle,anomaly',
            status='started'
        ).inc()
        
        logger.debug(
            f"Recorded analysis engine start for customer {customer_id}",
            extra={"customer_id": customer_id, "cloud_provider": cloud_provider}
        )
    except Exception as e:
        logger.error(f"Failed to record analysis engine start: {e}")


def record_analysis_engine_complete(
    customer_id: str,
    cloud_provider: str,
    duration: float,
    idle_resources: int,
    anomalies: int
):
    """
    Record analysis engine completion.
    
    Args:
        customer_id: Customer identifier
        cloud_provider: Cloud provider
        duration: Duration in seconds
        idle_resources: Number of idle resources found
        anomalies: Number of anomalies detected
    """
    try:
        analysis_engine_runs_total.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider,
            analysis_type='idle,anomaly',
            status='completed'
        ).inc()
        
        analysis_engine_duration_seconds.labels(
            customer_id=customer_id,
            cloud_provider=cloud_provider
        ).observe(duration)
        
        logger.info(
            f"Recorded analysis engine completion: {idle_resources} idle resources, {anomalies} anomalies",
            extra={
                "customer_id": customer_id,
                "cloud_provider": cloud_provider,
                "duration": duration,
                "idle_resources": idle_resources,
                "anomalies": anomalies
            }
        )
    except Exception as e:
        logger.error(f"Failed to record analysis engine completion: {e}")


def record_idle_resource_detected(
    customer_id: str,
    resource_type: str,
    severity: str,
    monthly_waste: float
):
    """
    Record an idle resource detection.
    
    Args:
        customer_id: Customer identifier
        resource_type: Resource type
        severity: Idle severity
        monthly_waste: Monthly waste amount
    """
    try:
        idle_resources_detected_total.labels(
            customer_id=customer_id,
            resource_type=resource_type,
            severity=severity
        ).inc()
        
        idle_resource_waste_dollars.labels(
            customer_id=customer_id,
            resource_type=resource_type
        ).observe(monthly_waste)
        
        logger.debug(
            f"Recorded idle resource: {resource_type}, {severity} severity, ${monthly_waste:.2f}/mo",
            extra={
                "customer_id": customer_id,
                "resource_type": resource_type,
                "severity": severity,
                "monthly_waste": monthly_waste
            }
        )
    except Exception as e:
        logger.error(f"Failed to record idle resource: {e}")


def record_anomaly_detected(
    customer_id: str,
    anomaly_type: str,
    severity: str,
    deviation_percent: float
):
    """
    Record an anomaly detection.
    
    Args:
        customer_id: Customer identifier
        anomaly_type: Anomaly type
        severity: Anomaly severity
        deviation_percent: Deviation percentage
    """
    try:
        anomalies_detected_total.labels(
            customer_id=customer_id,
            anomaly_type=anomaly_type,
            severity=severity
        ).inc()
        
        anomaly_deviation_percent.labels(
            customer_id=customer_id,
            anomaly_type=anomaly_type
        ).observe(abs(deviation_percent))
        
        logger.debug(
            f"Recorded anomaly: {anomaly_type}, {severity} severity, {deviation_percent:.1f}% deviation",
            extra={
                "customer_id": customer_id,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "deviation_percent": deviation_percent
            }
        )
    except Exception as e:
        logger.error(f"Failed to record anomaly: {e}")


def update_waste_metrics(
    customer_id: str,
    total_monthly_waste: float,
    idle_by_severity: Dict[str, int]
):
    """
    Update waste metrics gauges.
    
    Args:
        customer_id: Customer identifier
        total_monthly_waste: Total monthly waste
        idle_by_severity: Idle resources by severity
    """
    try:
        total_monthly_waste_dollars.labels(
            customer_id=customer_id
        ).set(total_monthly_waste)
        
        for severity, count in idle_by_severity.items():
            total_idle_resources.labels(
                customer_id=customer_id,
                severity=severity
            ).set(count)
        
        logger.debug(
            f"Updated waste metrics for {customer_id}: ${total_monthly_waste:.2f}/mo",
            extra={
                "customer_id": customer_id,
                "monthly_waste": total_monthly_waste,
                "idle_by_severity": idle_by_severity
            }
        )
    except Exception as e:
        logger.error(f"Failed to update waste metrics: {e}")
