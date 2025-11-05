# OptiInfra Collector Architecture Summary

## Collector Strategy

### Two-Tier Collection Architecture

**Tier 1: Dedicated Collectors (Big 3)**
- AWS, GCP, Azure
- Use native SDKs (boto3, google-cloud, azure-sdk)
- Deep integration with provider APIs
- Comprehensive cost, performance, resource data

**Tier 2: Generic Collector (All Others)**
- 12+ providers using universal approach
- Prometheus scraping (required)
- DCGM GPU metrics (optional)
- Provider API (optional, for billing)

---

## Provider Coverage Table

| Provider | Collector Type | SDK/Method | Status | Category |
|----------|---------------|------------|--------|----------|
| **AWS** | Dedicated | boto3 | ✅ Active | Big 3 |
| **GCP** | Dedicated | google-cloud-* | ✅ Active | Big 3 |
| **Azure** | Dedicated | azure-mgmt-* | ✅ Active | Big 3 |
| **Vultr** | Generic | Prometheus + REST API | ✅ Active | GPU Cloud |
| **RunPod** | Generic | Prometheus + GraphQL API | ✅ Active | GPU Cloud |
| **Lambda Labs** | Generic | Prometheus + REST API | ✅ Active | GPU Cloud |
| **CoreWeave** | Generic | Prometheus + K8s API | ✅ Active | GPU Cloud |
| **Paperspace** | Generic | Prometheus + REST API | ✅ Active | GPU Cloud |
| **DigitalOcean** | Generic | Prometheus + REST API | ✅ Active | General Compute |
| **Linode** | Generic | Prometheus + REST API | ✅ Active | General Compute |
| **Hetzner** | Generic | Prometheus + REST API | ✅ Active | General Compute |
| **OVHcloud** | Generic | Prometheus + REST API | ✅ Active | General Compute |
| **On-Premises** | Generic | Prometheus + DCGM | ✅ Active | Self-Hosted |
| **Kubernetes** | Generic | Prometheus + K8s API | ✅ Active | Self-Hosted |
| **Docker** | Generic | Prometheus + Docker API | ✅ Active | Self-Hosted |

**Total: 15 Providers**
- Dedicated Collectors: 3
- Generic Collector: 12

---

## Collector Comparison

| Feature | Dedicated (AWS/GCP/Azure) | Generic (Others) |
|---------|---------------------------|------------------|
| **Implementation** | Separate collector per provider | Single collector for all |
| **Data Sources** | Native SDK + CloudWatch/Monitoring | Prometheus + Optional API |
| **Cost Data** | Native billing APIs | Provider API (optional) |
| **Performance** | CloudWatch/Monitoring APIs | Prometheus metrics |
| **GPU Metrics** | Provider-specific | DCGM (universal) |
| **Setup Time** | 1-2 weeks per provider | <1 hour per provider |
| **Maintenance** | High (SDK updates) | Low (config only) |
| **Code Lines** | ~500-1000 per provider | ~600 total (shared) |

---

## Collection Methods by Provider

### Dedicated Collectors (3 providers)

**AWS:**
- Cost: AWS Cost Explorer API
- Performance: CloudWatch Metrics
- Resources: EC2, S3, RDS APIs
- Application: Custom metrics

**GCP:**
- Cost: Cloud Billing API
- Performance: Cloud Monitoring API
- Resources: Compute Engine API
- Application: Custom metrics

**Azure:**
- Cost: Cost Management API
- Performance: Azure Monitor
- Resources: Resource Manager API
- Application: Custom metrics

### Generic Collector (12 providers)

**All Generic Providers:**
- Performance: Prometheus `/metrics` endpoint
- GPU: DCGM exporter (if available)
- Resources: Prometheus node_exporter
- Application: vLLM/custom Prometheus metrics
- Cost: Provider REST/GraphQL API (optional)

---

## Why This Architecture?

### Dedicated for Big 3:
1. **Rich APIs**: Comprehensive billing and monitoring
2. **Enterprise Features**: Advanced cost allocation, tagging
3. **Deep Integration**: Native SDK support
4. **Customer Demand**: Most customers use Big 3

### Generic for Others:
1. **Standardization**: Prometheus is universal
2. **Rapid Onboarding**: Add provider in <1 hour
3. **Low Maintenance**: No SDK dependencies
4. **GPU Focus**: DCGM works everywhere
5. **Scalability**: One codebase for 12+ providers

---

## Adding New Providers

### To Add a New Generic Provider:

1. **Add to `providers.yaml`** (5 minutes)
   ```yaml
   new_provider:
     enabled: true
     collector_type: "generic"
     prometheus_url: "http://..."
   ```

2. **Add to `.env.example`** (2 minutes)
   ```bash
   NEW_PROVIDER_ENABLED=false
   NEW_PROVIDER_PROMETHEUS_URL=
   ```

3. **Add to `config.py`** (5 minutes)
   ```python
   NEW_PROVIDER_ENABLED = os.getenv("NEW_PROVIDER_ENABLED", "false")
   NEW_PROVIDER_PROMETHEUS_URL = os.getenv("NEW_PROVIDER_PROMETHEUS_URL", "")
   ```

4. **Add to `main.py` helper** (5 minutes)
   ```python
   "new_provider": {
       "enabled": config.NEW_PROVIDER_ENABLED,
       "prometheus_url": config.NEW_PROVIDER_PROMETHEUS_URL,
   }
   ```

5. **Optional: Create API adapter** (30-60 minutes)
   - Only if provider has billing API
   - Copy existing adapter template
   - Implement `get_billing_info()` and `get_instance_info()`

**Total Time: <1 hour** (without API adapter) or **1-2 hours** (with API adapter)

---

## Code Reuse

### Generic Collector Reuse:
- **1 codebase** serves 12 providers
- **~600 lines** total
- **~50 lines per provider** (just configuration)

### Dedicated Collector:
- **~500-1000 lines per provider**
- **3 providers = ~2000 lines**

### Savings:
- Without Generic Collector: Would need ~12,000 lines (12 providers × 1000 lines)
- With Generic Collector: Only ~600 lines
- **Code reduction: 95%**

---

## Future Expansion

### Easy to Add:
- Vast.ai (GPU cloud)
- Jarvis Labs (GPU cloud)
- Genesis Cloud (GPU cloud)
- Oracle Cloud (general compute)
- IBM Cloud (general compute)
- Alibaba Cloud (general compute)

### Just Need:
1. Prometheus endpoint URL
2. Optional: Provider API key
3. Configuration in 4 files
4. **Total time: <1 hour**
