# Grafana Dashboards for RunPod L4

## 🚀 Real-Time Agent Dashboards

### Dashboard Order (Consistent with Implementation)
1. **Cost Agent Dashboard** - `cost-agent-dashboard.json`
2. **Performance Agent Dashboard** - `performance-agent-dashboard.json`
3. **Resource Agent Dashboard** - `resource-agent-dashboard.json`
4. **Application Agent Dashboard** - `application-agent-dashboard.json`

## 📊 Real-Time Data Validation ✅

All dashboards query real-time data from ClickHouse with:
- **30-second refresh intervals**
- **Latest timestamp filtering** (last 1 hour for current values, 24 hours for trends)
- **Actual Prometheus metrics** from port 9090

### Data Sources Verified:
- ✅ **Cost Metrics**: 67 rows, latest: 2025-11-07 10:28:19
- ✅ **Performance Metrics**: 12 rows, latest: 2025-11-07 10:28:24 (GPU: 98%)
- ✅ **Resource Metrics**: 20 rows, latest: 2025-11-07 10:28:21 (Temp: 66°C)
- ✅ **Application Metrics**: 8 rows, latest: 2025-11-07 10:28:21 (Health: 100%)

## 🔧 Import Instructions

### Step 1: Access Grafana
- **URL**: http://localhost:3000
- **Login**: admin/admin

### Step 2: Install ClickHouse Plugin
1. Go to **Configuration → Plugins**
2. Search for **"ClickHouse"**
3. Install **"ClickHouse data source"**

### Step 3: Configure ClickHouse Data Source ✅
1. Go to **Configuration → Data Sources**
2. Add **ClickHouse**
3. Settings:
   - **URL**: `http://clickhouse:8123`
   - **Protocol**: `HTTP` ⚠️ **IMPORTANT: Select HTTP**
   - **Database**: `default` (leave empty or type "default")
   - **User**: `optiinfra`
   - **Password**: `optiinfra_dev_password`
   - **Skip TLS Verify**: ✅ Enable this

### Step 4: Import Dashboards
1. Go to **Dashboards → Import**
2. Upload each JSON file in order:
   - `cost-agent-dashboard.json` ✅ FIXED
   - `performance-agent-dashboard.json` ✅ FIXED
   - `resource-agent-dashboard.json` ✅ FIXED
   - `application-agent-dashboard.json` ✅ FIXED

**Note**: All dashboards now use correct database prefix `optiinfra_metrics.*`

## 🎯 Key Metrics Displayed

### Cost Agent Dashboard
- Total Accumulated Cost (Big number)
- Daily Cost Trend (Time series)
- GPU Hourly Rate, GPU Accumulated Cost, Savings Potential

### Performance Agent Dashboard
- GPU Utilization % (98% real-time)
- Request Latency P95, Throughput
- Total Requests, Tokens Generated, Batch Latency

### Resource Agent Dashboard
- GPU Utilization % & Memory Utilization
- GPU Temperature (66°C real-time)
- GPU Power Draw (72.5W real-time)

### Application Agent Dashboard
- Service Health % (100% real-time)
- Quality Score, Load Phase Active
- GPU Cost/Hour

## 🔄 Real-Time Updates
- **Refresh Rate**: Every 30 seconds
- **Data Source**: Prometheus → Data Collector → ClickHouse → Grafana
- **Latency**: < 1 minute from Prometheus to Dashboard

All dashboards are ready for real-time monitoring! 🎉
