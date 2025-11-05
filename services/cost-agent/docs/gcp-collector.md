# GCP Cost Collector Documentation

## Overview

The GCP Cost Collector is a comprehensive cost analysis and optimization system for Google Cloud Platform. It collects cost data, analyzes resource utilization, and identifies optimization opportunities across multiple GCP services.

## Architecture

### Components

1. **Base Collector** (`base.py`)
   - Common functionality for all GCP collectors
   - Rate limiting and API call tracking
   - Credential management (Service Account & ADC)
   - Pagination helpers

2. **BigQuery Helper** (`bigquery_helper.py`)
   - Queries billing export data from BigQuery
   - Provides cost breakdowns by service, project, region
   - Generates daily cost trends

3. **Billing Client** (`billing_client.py`)
   - Wrapper for Cloud Billing API
   - Cost forecasting
   - Committed Use Discount (CUD) analysis
   - Sustained Use Discount (SUD) tracking

4. **Service Collectors**
   - **Compute Engine** (`compute_engine.py`)
     - Instance cost collection
     - Idle/underutilized instance detection
     - Preemptible migration opportunities
     - Persistent disk cost analysis
   
   - **Cloud SQL** (`cloud_sql.py`)
     - Database instance costs
     - Idle database detection
     - HA to zonal conversion opportunities
     - Storage cost analysis
   
   - **Cloud Functions** (`cloud_functions.py`)
     - Function invocation costs
     - Over-provisioned function detection
     - Memory optimization recommendations
   
   - **Cloud Storage** (`cloud_storage.py`)
     - Bucket storage costs
     - Storage class distribution
     - Lifecycle policy recommendations

5. **Cost Analyzer** (`gcp_analyzer.py`)
   - Aggregates data from all collectors
   - Performs comprehensive analysis
   - Detects cost anomalies
   - Prioritizes optimization opportunities

6. **Storage Layer** (`gcp_metrics.py`)
   - ClickHouse integration
   - Time-series cost metrics storage
   - Historical trend analysis
   - Opportunity tracking

## Prerequisites

### 1. GCP Project Setup

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable cloudbilling.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### 2. Service Account Creation

```bash
# Create service account
gcloud iam service-accounts create cost-collector \
    --display-name="Cost Collector Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.viewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.viewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudfunctions.viewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.viewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/billing.viewer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"

# Create and download key
gcloud iam service-accounts keys create ~/gcp-cost-collector-key.json \
    --iam-account=cost-collector@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Billing Export Setup

```bash
# Create BigQuery dataset for billing export
bq mk --dataset --location=US $GCP_PROJECT_ID:billing_export

# Enable billing export in Cloud Console:
# 1. Go to Billing > Billing export
# 2. Select "BigQuery export"
# 3. Choose the dataset created above
# 4. Enable "Detailed usage cost" export
```

### 4. Environment Configuration

```bash
# .env file
GCP_PROJECT_ID=your-project-id
GCP_CREDENTIALS_PATH=/path/to/gcp-cost-collector-key.json
GCP_BILLING_ACCOUNT_ID=your-billing-account-id
GCP_BILLING_DATASET=billing_export

# Collection settings
GCP_COST_LOOKBACK_DAYS=30
GCP_IDLE_CPU_THRESHOLD=5.0
GCP_UNDERUTILIZED_CPU_THRESHOLD=20.0
GCP_PREEMPTIBLE_SAVINGS_TARGET=0.80
GCP_COLLECTION_SCHEDULE="0 3 * * *"

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_DATABASE=cost_agent
```

## API Endpoints

### 1. Test Connection

```bash
POST /api/v1/gcp/test-connection
Content-Type: application/json

{
  "project_id": "your-project-id",
  "credentials_path": "/path/to/key.json"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "your-project-id",
  "billing_info": {
    "billing_account_id": "012345-ABCDEF-678910",
    "display_name": "My Billing Account",
    "open": true
  },
  "accessible_services": [
    "Compute Engine",
    "Cloud SQL",
    "Cloud Storage"
  ],
  "message": "Successfully connected to GCP project your-project-id"
}
```

### 2. Collect Costs

```bash
POST /api/v1/gcp/collect
Content-Type: application/json

{
  "project_id": "your-project-id",
  "credentials_path": "/path/to/key.json",
  "billing_account_id": "012345-ABCDEF-678910",
  "billing_dataset": "billing_export",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "lookback_days": 30,
  "include_utilization": true
}
```

**Response:**
```json
{
  "project_id": "your-project-id",
  "time_period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "total_cost": 5432.10,
  "cost_breakdown": {
    "by_service": {
      "Compute Engine": 3200.50,
      "Cloud SQL": 1500.00,
      "Cloud Storage": 500.00,
      "Cloud Functions": 231.60
    },
    "by_project": {
      "your-project-id": 5432.10
    },
    "daily": [...]
  },
  "services": {
    "compute_engine": {
      "total_instances": 25,
      "total_monthly_cost": 3200.50,
      "idle_instances": 3,
      "underutilized_instances": 5,
      "preemptible_opportunities": 8
    },
    "cloud_sql": {...},
    "cloud_functions": {...},
    "cloud_storage": {...}
  },
  "optimization": {
    "total_opportunities": 18,
    "total_potential_savings": 1250.00,
    "opportunities": [...]
  },
  "anomalies": [],
  "analyzed_at": "2024-01-31T12:00:00Z"
}
```

### 3. Query Costs

```bash
POST /api/v1/gcp/costs/query
Content-Type: application/json

{
  "project_id": "your-project-id",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "service": "Compute Engine"
}
```

### 4. Get Opportunities

```bash
POST /api/v1/gcp/opportunities
Content-Type: application/json

{
  "project_id": "your-project-id",
  "service": "Compute Engine",
  "min_savings": 50.0,
  "limit": 20
}
```

### 5. Get Forecast

```bash
GET /api/v1/gcp/forecast/your-project-id?forecast_days=30
```

## Optimization Opportunities

### 1. Idle Instances (Compute Engine)

**Detection Criteria:**
- CPU utilization < 5%
- Network traffic < 1 GB/day
- Duration: 14 days

**Recommendation:** Terminate instance

**Savings:** Full instance cost

### 2. Underutilized Instances (Compute Engine)

**Detection Criteria:**
- CPU utilization < 20%
- Not classified as idle

**Recommendation:** Downsize to smaller machine type

**Savings:** Cost difference between current and recommended type

### 3. Preemptible Migration (Compute Engine)

**Detection Criteria:**
- Workload type: batch processing, development, testing
- Not already preemptible

**Recommendation:** Convert to preemptible instance

**Savings:** ~80% of instance cost

### 4. Idle Databases (Cloud SQL)

**Detection Criteria:**
- Average connections < 1
- Duration: 14 days

**Recommendation:** Terminate database

**Savings:** Full database cost

### 5. HA to Zonal Conversion (Cloud SQL)

**Detection Criteria:**
- Regional (HA) configuration
- Environment: dev, test, staging

**Recommendation:** Convert to zonal instance

**Savings:** ~50% of instance cost

### 6. Over-provisioned Functions (Cloud Functions)

**Detection Criteria:**
- Execution time < 100ms
- Memory allocation higher than needed

**Recommendation:** Reduce memory allocation

**Savings:** Memory cost reduction

### 7. Lifecycle Policies (Cloud Storage)

**Detection Criteria:**
- Standard storage class
- Size > 100 GB
- No lifecycle policy configured

**Recommendation:** Add lifecycle transitions to Nearline/Coldline

**Savings:** ~50% of storage cost

## Metrics

### Prometheus Metrics

```
# API Metrics
gcp_api_calls_total{service, operation}
gcp_api_errors_total{service, error_type}

# Collection Metrics
gcp_cost_collection_duration_seconds

# Cost Metrics
gcp_total_monthly_cost_usd{service, region}
gcp_waste_identified_usd{service}

# Opportunity Metrics
gcp_optimization_opportunities{type}
gcp_idle_resources_count{service}
gcp_underutilized_resources_count{service}
```

## ClickHouse Schema

### Tables

1. **gcp_cost_metrics** - Overall cost metrics
2. **gcp_compute_metrics** - Compute Engine instance metrics
3. **gcp_sql_metrics** - Cloud SQL instance metrics
4. **gcp_functions_metrics** - Cloud Functions metrics
5. **gcp_storage_metrics** - Cloud Storage bucket metrics
6. **gcp_opportunities** - Optimization opportunities

## Best Practices

### 1. Authentication

- Use Service Accounts for production
- Rotate keys regularly
- Follow principle of least privilege
- Use Workload Identity when running in GKE

### 2. Cost Optimization

- Run collection daily during off-peak hours
- Review opportunities weekly
- Implement automated actions for low-risk opportunities
- Track savings over time

### 3. Monitoring

- Set up alerts for cost anomalies
- Monitor API quota usage
- Track collection success rate
- Review error logs regularly

### 4. Data Retention

- Keep 90 days of detailed metrics
- Aggregate older data for long-term trends
- Archive opportunities for audit trail

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: Could not load credentials
Solution: Verify GCP_CREDENTIALS_PATH is correct and file exists
```

**2. API Not Enabled**
```
Error: API [service] is not enabled
Solution: Enable the API using gcloud services enable
```

**3. Insufficient Permissions**
```
Error: Permission denied on resource
Solution: Grant required IAM roles to service account
```

**4. Billing Export Not Found**
```
Error: Table not found
Solution: Verify billing export is enabled and dataset name is correct
```

**5. Rate Limiting**
```
Error: ResourceExhausted
Solution: Collector automatically retries with exponential backoff
```

## Future Enhancements

1. **Additional Services**
   - Cloud Run
   - GKE (Google Kubernetes Engine)
   - Cloud Dataflow
   - Cloud Pub/Sub

2. **Advanced Analysis**
   - ML-based anomaly detection
   - Predictive cost modeling
   - Multi-project consolidation
   - Cross-region optimization

3. **Automation**
   - Automatic rightsizing
   - Scheduled instance start/stop
   - Automated lifecycle policies
   - Budget alerts integration

4. **Reporting**
   - PDF cost reports
   - Executive dashboards
   - Slack/Teams notifications
   - Custom report templates

## Support

For issues or questions:
- Check logs in `/var/log/cost-agent/`
- Review Prometheus metrics at `/metrics`
- Consult API documentation at `/docs`
- Contact: optiinfra-support@example.com
