# Cost Agent User Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Table of Contents

- [Getting Started](#getting-started)
- [Common Use Cases](#common-use-cases)
- [Workflows](#workflows)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Getting Started

### Prerequisites

- API key or JWT token for authentication
- Cloud provider credentials configured
- Basic understanding of cloud cost optimization

### Quick Start

1. **Get an API Key**:
```bash
curl -X POST http://localhost:8001/api/v1/auth/api-key/create \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"customer_id": "your-customer-id", "name": "My API Key"}'
```

2. **Collect Cost Data**:
```bash
curl -X POST http://localhost:8001/api/v1/aws/costs/collect \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }'
```

3. **Generate Recommendations**:
```bash
curl -X POST http://localhost:8001/api/v1/recommendations/generate \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "provider": "aws"
  }'
```

---

## Common Use Cases

### 1. Cost Analysis

**Objective**: Understand your cloud spending patterns

**Steps**:
1. Collect cost data from your cloud providers
2. Run analysis to detect anomalies and trends
3. Review the analysis report

**Example**:
```bash
# Analyze AWS costs
curl -X POST http://localhost:8001/api/v1/analyze \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "provider": "aws",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "analysis_types": ["anomaly", "trend", "forecast"]
  }'
```

**Expected Output**:
- Detected anomalies with severity levels
- Cost trends (increasing/decreasing)
- Forecast for next month
- Summary and insights

---

### 2. Spot Instance Migration

**Objective**: Migrate on-demand instances to spot instances for 30-40% savings

**Steps**:
1. Generate spot migration recommendations
2. Review and approve recommendations
3. Execute migration with gradual rollout
4. Monitor execution progress
5. Verify savings

**Example**:
```bash
# Generate recommendations
curl -X POST http://localhost:8001/api/v1/recommendations/generate \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "provider": "aws",
    "recommendation_types": ["spot"]
  }'

# Approve recommendation
curl -X POST http://localhost:8001/api/v1/recommendations/rec-xyz789/approve \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "approved_by": "user@example.com"
  }'

# Execute with gradual rollout
curl -X POST http://localhost:8001/api/v1/execution/execute \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "recommendation_id": "rec-xyz789",
    "execution_mode": "gradual",
    "auto_rollback": true
  }'
```

---

### 3. Reserved Instance Recommendations

**Objective**: Identify opportunities to purchase Reserved Instances for 40-60% savings

**Steps**:
1. Analyze usage patterns
2. Generate RI recommendations
3. Review ROI calculations
4. Purchase recommended RIs

**Example**:
```bash
curl -X POST http://localhost:8001/api/v1/recommendations/generate \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "provider": "aws",
    "recommendation_types": ["reserved_instances"]
  }'
```

---

### 4. Right-Sizing

**Objective**: Identify over-provisioned resources and right-size them for 20-30% savings

**Steps**:
1. Collect resource utilization data
2. Generate right-sizing recommendations
3. Review recommendations
4. Execute right-sizing changes

**Example**:
```bash
curl -X POST http://localhost:8001/api/v1/recommendations/generate \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "your-customer-id",
    "provider": "aws",
    "recommendation_types": ["right_sizing"]
  }'
```

---

## Workflows

### Cost Optimization Workflow

```
1. Collect Costs → 2. Analyze → 3. Generate Recommendations → 4. Review → 5. Execute → 6. Monitor
```

**Detailed Steps**:

1. **Collect Costs**: Gather cost data from cloud providers
2. **Analyze**: Detect anomalies, trends, and waste
3. **Generate Recommendations**: AI-powered optimization suggestions
4. **Review**: Human review and approval
5. **Execute**: Automated execution with safety mechanisms
6. **Monitor**: Track results and measure savings

---

### Spot Migration Workflow

```
1. Analyze → 2. Identify Opportunities → 3. Approve → 4. Execute (10% → 50% → 100%) → 5. Monitor
```

**Gradual Rollout**:
- **Phase 1 (10%)**: Test with 10% of instances
- **Phase 2 (50%)**: Expand to 50% if successful
- **Phase 3 (100%)**: Complete migration

**Auto-Rollback**:
- Automatically rolls back if error rate exceeds threshold
- Monitors performance degradation
- Ensures service stability

---

## Best Practices

### 1. Regular Analysis

- **Frequency**: Run cost analysis weekly
- **Scope**: Analyze all cloud providers
- **Action**: Review and act on recommendations promptly

### 2. Gradual Rollouts

- **Always use gradual rollout** for production changes
- **Enable auto-rollback** for safety
- **Monitor metrics** during execution

### 3. Approval Workflow

- **Review recommendations** before approval
- **Verify prerequisites** are met
- **Plan maintenance windows** for high-impact changes

### 4. Monitoring

- **Set up alerts** for anomalies
- **Track savings** over time
- **Review execution outcomes** regularly

### 5. Feedback Loop

- **Provide feedback** on execution outcomes
- **Report issues** promptly
- **Share insights** with the team

---

## FAQ

### General Questions

**Q: How often should I run cost analysis?**  
A: Weekly for active monitoring, daily for high-spend environments.

**Q: Are recommendations guaranteed to save money?**  
A: Recommendations are estimates based on historical data. Actual savings may vary.

**Q: Can I rollback changes?**  
A: Yes, all executions support rollback. Enable auto-rollback for automatic recovery.

### Technical Questions

**Q: What cloud providers are supported?**  
A: AWS, GCP, Azure, and Vultr.

**Q: How long does analysis take?**  
A: Typically 10-30 seconds depending on data volume.

**Q: Can I schedule executions?**  
A: Yes, use the `scheduled_time` parameter in execution requests.

### Security Questions

**Q: How is my data secured?**  
A: All data is encrypted at rest and in transit. We follow SOC 2 compliance standards.

**Q: Who can access my cost data?**  
A: Only authenticated users with valid API keys or JWT tokens for your customer ID.

**Q: How long is data retained?**  
A: Cost data is retained for 13 months. Execution history for 12 months.

---

## Support

- **Documentation**: https://docs.optiinfra.com
- **Email**: support@optiinfra.com
- **Community**: https://community.optiinfra.com

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0
