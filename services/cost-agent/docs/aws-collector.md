# AWS Cost Collector Documentation

## Overview

The AWS Cost Collector is a comprehensive system for collecting, analyzing, and optimizing AWS cloud costs. It integrates with AWS Cost Explorer, CloudWatch, and various AWS service APIs to provide actionable insights.

## Features

- **Cost Collection**: Automatic collection of AWS costs via Cost Explorer API
- **Resource Analysis**: Deep analysis of EC2, RDS, Lambda, and S3 resources
- **Idle Detection**: Identifies idle resources (CPU < 5%, no network traffic)
- **Underutilization Detection**: Finds underutilized resources (CPU < 20%)
- **Spot Opportunities**: Identifies instances eligible for spot migration
- **Rightsizing Recommendations**: Suggests optimal instance sizes
- **Cost Forecasting**: 30-day cost projections
- **Anomaly Detection**: Detects unusual cost spikes
- **Historical Storage**: Stores metrics in ClickHouse for trending

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ API     │
    │ Layer   │
    └────┬────┘
         │
    ┌────┴─────────────────────┐
    │                          │
┌───┴────┐              ┌──────┴──────┐
│ AWS    │              │  Cost       │
│ Costs  │              │  Analyzer   │
│ API    │              └──────┬──────┘
└───┬────┘                     │
    │                    ┌─────┴─────┐
    │                    │           │
┌───┴──────────┐    ┌───┴────┐ ┌───┴────┐
│  Collectors  │    │Storage │ │Metrics │
├──────────────┤    └────────┘ └────────┘
│ - EC2        │         │          │
│ - RDS        │    ┌────┴────┐ ┌──┴────┐
│ - Lambda     │    │ClickHouse│ │Prometheus│
│ - S3         │    └─────────┘ └────────┘
│ - Cost Exp.  │
└──────────────┘
```

## Setup

### 1. AWS Credentials

Set environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

Or use IAM roles (recommended for production).

### 2. IAM Permissions

Required IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetReservationUtilization",
        "ce:GetSavingsPlansUtilization",
        "ce:GetRightsizingRecommendation",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "cloudwatch:GetMetricStatistics",
        "rds:DescribeDBInstances",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Enable Cost Explorer

Cost Explorer must be enabled in your AWS account:
1. Go to AWS Cost Explorer in console
2. Click "Enable Cost Explorer"
3. Wait 24 hours for data to populate

### 4. Install Dependencies

```bash
pip install boto3==1.34.0 moto==4.2.0
```

## API Endpoints

### Test Connection

```bash
POST /api/v1/aws/test-connection
```

Tests AWS credentials and Cost Explorer access.

**Response:**
```json
{
  "status": "connected",
  "account_id": "123456789012",
  "regions": ["us-east-1", "us-west-2"],
  "cost_explorer_available": true,
  "permissions_valid": true
}
```

### Collect Costs

```bash
POST /api/v1/aws/collect
Content-Type: application/json

{
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "services": ["EC2", "RDS", "Lambda", "S3"],
  "analyze": true,
  "dry_run": false
}
```

**Response:**
```json
{
  "status": "started",
  "job_id": "aws-collect-20251021-103045",
  "estimated_duration_seconds": 30,
  "services_to_collect": 4,
  "regions_to_scan": 3
}
```

### Get Job Status

```bash
GET /api/v1/aws/jobs/{job_id}
```

### Query Costs

```bash
GET /api/v1/aws/costs?start_date=2025-10-01&end_date=2025-10-31
```

**Response:**
```json
{
  "time_period": {
    "start": "2025-10-01",
    "end": "2025-10-31"
  },
  "total_cost": 120000.50,
  "by_service": {
    "AmazonEC2": 85000.00,
    "AmazonRDS": 20000.00,
    "AWSLambda": 8000.50,
    "AmazonS3": 5000.00
  },
  "by_region": {
    "us-east-1": 70000.00,
    "us-west-2": 35000.00
  },
  "daily_breakdown": [...]
}
```

### Get EC2 Costs

```bash
GET /api/v1/aws/costs/ec2?include_instances=true
```

### Get RDS Costs

```bash
GET /api/v1/aws/costs/rds
```

### Get Optimization Opportunities

```bash
GET /api/v1/aws/opportunities?min_savings=1000
```

**Response:**
```json
{
  "total_opportunities": 23,
  "total_potential_savings": 58000.00,
  "opportunities": [
    {
      "id": "opp-001",
      "type": "spot_migration",
      "service": "EC2",
      "resource_ids": ["i-abc123", "i-def456"],
      "description": "Migrate 15 instances to spot",
      "estimated_savings": 18000.00,
      "confidence": 0.85,
      "priority": "high",
      "effort": "medium",
      "risk": "low"
    }
  ]
}
```

### Run Comprehensive Analysis

```bash
POST /api/v1/aws/analysis
Content-Type: application/json

{
  "analyze_trends": true,
  "detect_anomalies": true,
  "forecast_30d": true
}
```

## Configuration

Configuration via environment variables or `src/config.py`:

```python
# AWS Settings
AWS_ACCESS_KEY_ID = "your-key"
AWS_SECRET_ACCESS_KEY = "your-secret"
AWS_DEFAULT_REGION = "us-east-1"
AWS_REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]

# Collection Settings
AWS_COST_LOOKBACK_DAYS = 30
AWS_IDLE_CPU_THRESHOLD = 5.0  # CPU < 5% = idle
AWS_UNDERUTILIZED_CPU_THRESHOLD = 20.0  # CPU < 20% = underutilized
AWS_SPOT_SAVINGS_TARGET = 0.35  # 35% target savings
AWS_COLLECTION_SCHEDULE = "0 2 * * *"  # Daily at 2 AM
```

## Collectors

### EC2 Collector

**Features:**
- Instance cost collection
- Idle instance detection (CPU < 5%, network < 1MB/day)
- Underutilized instance detection (CPU < 20%)
- Spot migration opportunities
- Rightsizing recommendations
- EBS cost analysis
- Unattached volume detection

**Usage:**
```python
from src.collectors.aws.ec2 import EC2CostCollector

collector = EC2CostCollector(region="us-east-1")
instances = collector.collect_instance_costs(
    start_date="2025-10-01",
    end_date="2025-10-31",
    include_utilization=True
)
```

### RDS Collector

**Features:**
- Database cost collection
- Idle database detection (0 connections)
- Storage cost analysis
- Multi-AZ optimization opportunities
- Reserved instance recommendations

### Lambda Collector

**Features:**
- Function cost calculation
- Over-provisioned function detection
- Memory optimization recommendations
- Invocation metrics

### S3 Collector

**Features:**
- Bucket cost analysis
- Storage class distribution
- Lifecycle policy recommendations
- Incomplete upload detection

### Cost Explorer Client

**Features:**
- Cost and usage data retrieval
- Cost forecasting
- Savings Plans utilization
- Reserved Instance utilization
- Rightsizing recommendations from AWS

## Storage

Metrics are stored in ClickHouse for historical analysis:

### Tables Used

- `cost_metrics`: Daily cost time-series
- `resource_metrics`: Per-resource utilization
- `optimization_opportunities`: Identified opportunities

### Queries

```python
from src.storage.aws_metrics import AWSMetricsStorage

storage = AWSMetricsStorage()

# Query cost trends
trends = storage.query_cost_trends(
    start_date="2025-10-01",
    end_date="2025-10-31",
    service="AmazonEC2"
)

# Get idle resources
idle = storage.get_idle_resources(lookback_days=7)
```

## Metrics

Prometheus metrics exposed at `/metrics`:

```
# AWS-specific metrics
aws_total_monthly_cost_usd{service="AmazonEC2",region="us-east-1"} 85000.0
aws_waste_identified_usd{service="EC2"} 38000.0
aws_optimization_opportunities{type="spot_migration"} 15
aws_idle_resources_count{service="EC2"} 8
aws_underutilized_resources_count{service="EC2"} 35
aws_api_calls_total{service="cost_explorer",operation="GetCostAndUsage"} 12
aws_cost_collection_duration_seconds_bucket{le="30"} 1
```

## Troubleshooting

### No Credentials Error

```
ERROR: botocore.exceptions.NoCredentialsError
```

**Solution:** Set AWS credentials via environment variables or AWS CLI configuration.

### Cost Explorer Not Enabled

```
ERROR: AccessDeniedException: Cost Explorer is not enabled
```

**Solution:** Enable Cost Explorer in AWS Console and wait 24 hours.

### Rate Limiting

```
ERROR: ThrottlingException: Rate exceeded
```

**Solution:** Cost Explorer has a limit of 400 requests/hour. The collector implements automatic retry with backoff.

### No Cost Data

**Solution:** Ensure:
- Cost Explorer enabled for 24+ hours
- Date range is valid
- AWS account has recent usage

## Best Practices

1. **Use IAM Roles**: Prefer IAM roles over access keys in production
2. **Cache Results**: Cost Explorer API is expensive; cache responses
3. **Schedule Collection**: Run daily at off-peak hours
4. **Monitor Rate Limits**: Track API call rates
5. **Validate Opportunities**: Review recommendations before taking action
6. **Test in Dev First**: Use dry_run mode to test collection

## Examples

### Collect Last 30 Days

```bash
curl -X POST http://localhost:8001/api/v1/aws/collect \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "analyze": true
  }'
```

### Find Idle Resources

```bash
curl "http://localhost:8001/api/v1/aws/opportunities?type=idle_resource&min_savings=100"
```

### Get Cost Forecast

```bash
curl -X POST http://localhost:8001/api/v1/aws/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_30d": true
  }'
```

## Support

For issues or questions:
- Check logs: `tail -f logs/cost-agent.log`
- Review metrics: `curl http://localhost:8001/metrics | grep aws_`
- Test connection: `POST /api/v1/aws/test-connection`

## Next Steps

After AWS Cost Collector is working:
1. **PHASE1-1.3**: Implement GCP Cost Collector
2. **PHASE1-1.4**: Implement Azure Cost Collector
3. **PHASE1-1.5**: Multi-cloud cost aggregation
