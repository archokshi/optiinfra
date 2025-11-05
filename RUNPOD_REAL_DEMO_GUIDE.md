# 🚀 RunPod Real Demo - Complete Guide

## 🎯 Goal
Deploy a **real vLLM workload on RunPod** and see live data flowing to your OptiInfra dashboard.

---

## 📋 Prerequisites
- ✅ RunPod API Key (you have this)
- ✅ RunPod account with credits ($10.00)
- ✅ OptiInfra services running (data-collector, portal)

---

## 🎬 Option 1: Quick vLLM Demo (Recommended - 15 minutes)

### **Step 1: Deploy vLLM on RunPod**

#### **1.1 Go to RunPod Console**
- Visit: https://www.runpod.io/console/pods
- Click: **+ Deploy**

#### **1.2 Select GPU**
Choose one of these (cheapest to most expensive):
- **RTX 4090** (~$0.69/hour) ← Recommended for demo
- **RTX A6000** (~$0.79/hour)
- **A100 40GB** (~$1.89/hour)

#### **1.3 Select Template**
- Search for: **"vLLM"**
- Select: **"vLLM OpenAI Compatible"** template
- Or use Docker image: `vllm/vllm-openai:latest`

#### **1.4 Configure Pod**
```yaml
Container Image: vllm/vllm-openai:latest
Container Disk: 50 GB
Volume Disk: 0 GB (not needed for demo)

Environment Variables:
  MODEL: meta-llama/Llama-2-7b-chat-hf
  # or use: microsoft/phi-2 (smaller, faster)
  
Expose HTTP Ports:
  - 8000 (vLLM API)
  - 9090 (Prometheus - if available)

Start Command:
  python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000
```

#### **1.5 Deploy**
- Click: **Deploy On-Demand**
- Wait 2-3 minutes for pod to start
- Note the **Pod ID** and **Public IP**

---

### **Step 2: Verify vLLM is Running**

#### **2.1 Get Pod URL**
RunPod will give you a URL like:
```
https://YOUR_POD_ID-8000.proxy.runpod.net
```

#### **2.2 Test vLLM API**
```powershell
# Test if vLLM is responding
$vllmUrl = "https://YOUR_POD_ID-8000.proxy.runpod.net"
Invoke-WebRequest -Uri "$vllmUrl/health" -Method GET
```

Expected response: `{"status": "ok"}`

#### **2.3 Send Test Request**
```powershell
$body = @{
    model = "meta-llama/Llama-2-7b-chat-hf"
    messages = @(
        @{
            role = "user"
            content = "Hello! Tell me a joke."
        }
    )
    max_tokens = 50
} | ConvertTo-Json

Invoke-WebRequest -Uri "$vllmUrl/v1/chat/completions" -Method POST -Body $body -ContentType "application/json"
```

✅ If you get a response, vLLM is working!

---

### **Step 3: Expose Prometheus Metrics**

#### **Problem**: vLLM doesn't expose Prometheus metrics by default on RunPod

#### **Solution**: We'll use RunPod API to get metrics instead

Since RunPod pods don't easily expose Prometheus, we'll collect data using:
1. **RunPod API** (for cost and instance info)
2. **Simulated metrics** (for demo purposes)

---

### **Step 4: Update OptiInfra Credentials**

#### **4.1 Get Your RunPod Pod Info**
```powershell
# Get your RunPod API key
$runpodApiKey = "YOUR_RUNPOD_API_KEY"

# Test RunPod API
$headers = @{
    "Authorization" = "Bearer $runpodApiKey"
}
Invoke-WebRequest -Uri "https://api.runpod.io/graphql" -Headers $headers -Method POST -Body '{"query":"{ myself { id } }"}' -ContentType "application/json"
```

#### **4.2 Update Credentials in OptiInfra**
```powershell
# Update RunPod credentials with API key
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod Production"
    credentials = @{
        api_key = $runpodApiKey
        prometheus_url = "http://prometheus:9090"  # Placeholder for now
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"
```

---

### **Step 5: Trigger Collection**

#### **5.1 Trigger RunPod Collection**
```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("cost")
    async_mode = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"
```

#### **5.2 Check Collection Status**
```powershell
# Check if data was collected
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT provider, COUNT(*) as count, MAX(timestamp) as last FROM optiinfra_metrics.cost_metrics GROUP BY provider;"
```

---

### **Step 6: View Dashboard**

#### **6.1 Check Dashboard API**
```powershell
Invoke-WebRequest -Uri "http://localhost:8005/api/v1/dashboard?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11&provider=runpod" | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

#### **6.2 Open Portal UI**
- Open browser: `http://localhost:3001/dashboard`
- Should see RunPod data in:
  - Cost trends
  - Provider breakdown
  - Agent status

---

## 🎬 Option 2: Full Prometheus Setup (Advanced - 45 minutes)

If you want **real-time performance metrics** (CPU, GPU, latency), you need to:

### **Step 1: Deploy with Custom Docker Image**

Create a custom Dockerfile:
```dockerfile
FROM vllm/vllm-openai:latest

# Install Prometheus exporters
RUN apt-get update && apt-get install -y \
    prometheus-node-exporter \
    && rm -rf /var/lib/apt/lists/*

# Expose ports
EXPOSE 8000 9090 9100

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
```

Create `start.sh`:
```bash
#!/bin/bash

# Start Node Exporter (port 9100)
node_exporter --web.listen-address=:9100 &

# Start vLLM (port 8000)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-chat-hf \
  --host 0.0.0.0 \
  --port 8000
```

### **Step 2: Deploy to RunPod**
- Build and push to Docker Hub
- Deploy on RunPod with custom image
- Expose ports: 8000, 9100

### **Step 3: Update Credentials**
```powershell
$prometheusUrl = "https://YOUR_POD_ID-9100.proxy.runpod.net"

# Update credentials with real Prometheus URL
```

---

## 🎯 Quick Demo Script (5 minutes)

### **What to Show:**

1. **Show RunPod Console**
   - Pod running
   - GPU utilization
   - Cost per hour

2. **Show vLLM Working**
   - Send test request
   - Get response

3. **Show OptiInfra Dashboard**
   - Cost trends showing RunPod
   - Provider breakdown
   - Real-time updates

4. **Show Collection Working**
   - Trigger collection
   - Check logs
   - Verify data in ClickHouse

5. **Show Portal UI**
   - Dashboard with RunPod data
   - Agent status
   - Cost analysis

---

## 🐛 Troubleshooting

### **Issue: No data collected**
```powershell
# Check logs
docker logs optiinfra-data-collector --tail 50

# Check credentials
Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/runpod?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
```

### **Issue: vLLM not responding**
- Check RunPod pod status
- Verify pod is running
- Check logs in RunPod console

### **Issue: Dashboard shows 0 cost**
- RunPod API might not return cost data immediately
- Insert sample data for demo (see below)

---

## 🎭 Demo Data Fallback

If RunPod API doesn't return data immediately, insert sample data:

```powershell
docker exec optiinfra-clickhouse clickhouse-client --query "
INSERT INTO optiinfra_metrics.cost_metrics 
(timestamp, customer_id, provider, instance_id, cost_type, amount, currency) 
VALUES 
('2025-11-01 00:00:00', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'runpod', 'YOUR_POD_ID', 'compute', 0.69, 'USD'),
('2025-11-01 01:00:00', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'runpod', 'YOUR_POD_ID', 'compute', 0.69, 'USD'),
('2025-11-01 02:00:00', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'runpod', 'YOUR_POD_ID', 'compute', 0.69, 'USD');
"
```

---

## ✅ Success Criteria

- [ ] vLLM pod running on RunPod
- [ ] vLLM responding to API requests
- [ ] OptiInfra collecting RunPod data
- [ ] Dashboard showing RunPod metrics
- [ ] Portal UI displaying real-time data

---

## 🚀 Ready to Start?

**Next Steps:**
1. Deploy vLLM on RunPod (Step 1)
2. Test vLLM API (Step 2)
3. Update OptiInfra credentials (Step 4)
4. Trigger collection (Step 5)
5. View dashboard (Step 6)

**Estimated Time**: 15-20 minutes for full setup

---

*Let me know when you're ready to start, and I'll guide you through each step!* 🎯
