# 🚀 RunPod Demo Deployment - Step-by-Step Guide

## 📋 What You'll Deploy

**vLLM Chatbot with Full Monitoring Stack:**
- ✅ vLLM Server (Llama-3.1-8B-Instruct)
- ✅ Chat API (FastAPI with metrics)
- ✅ Prometheus (metrics collection)
- ✅ DCGM Exporter (GPU metrics)
- ✅ Locust (load testing)

**All 4 OptiInfra Agents Can Optimize:**
- 💰 Cost Agent: GPU utilization, instance sizing
- ⚡ Performance Agent: KV cache, latency
- 📊 Resource Agent: GPU consolidation
- 🎯 Application Agent: Quality monitoring

---

## 🎬 Step 1: Deploy RunPod Pod

### 1.1 Go to RunPod Console
Visit: https://www.runpod.io/console/pods

### 1.2 Click "+ Deploy"

### 1.3 Select GPU
Choose one of:
- **RTX 4090** (~$0.69/hour) ← **Recommended**
- **RTX A6000** (~$0.79/hour)
- **A100 40GB** (~$1.89/hour)

### 1.4 Select Template
- **Template**: Ubuntu 22.04 with CUDA
- **Or**: Any template with Docker support

### 1.5 Configure Pod
```yaml
Container Disk: 50 GB
Volume Disk: 50 GB (for model storage)

Expose HTTP Ports:
  - 8100 (vLLM)
  - 8200 (Chat API)
  - 9091 (Prometheus)
  - 9401 (DCGM)
  - 8090 (Locust)

Start Command: (leave default or use /bin/bash)
```

### 1.6 Deploy
- Click: **Deploy On-Demand**
- Wait 1-2 minutes for pod to start
- Click **Connect** → **Start Web Terminal** or **SSH**

---

## 🎬 Step 2: Run Setup Script

### 2.1 Connect to Pod
Use RunPod web terminal or SSH

### 2.2 Download and Run Script
```bash
# Download the setup script
curl -o runpod-demo-setup.sh https://raw.githubusercontent.com/YOUR_REPO/optiinfra/main/runpod-demo-setup.sh

# Or copy-paste the script content (see runpod-demo-setup.sh)

# Make it executable
chmod +x runpod-demo-setup.sh

# Run it
bash runpod-demo-setup.sh
```

### 2.3 Start Services
```bash
cd /workspace/runpod-demo-app
./scripts/start.sh
```

**⏰ First run takes 10-15 minutes** to download Llama-3.1-8B model (~16GB)

---

## 🎬 Step 3: Verify Services

### 3.1 Check Status
```bash
./scripts/status.sh
```

Expected output:
```
=== Services ===
NAME              STATUS    PORTS
vllm-server       Up        0.0.0.0:8100->8000/tcp
chat-api          Up        0.0.0.0:8200->8080/tcp
prometheus-demo   Up        0.0.0.0:9091->9090/tcp
dcgm-exporter     Up        0.0.0.0:9401->9400/tcp
locust            Up        0.0.0.0:8090->8089/tcp

=== GPU ===
85%, 12000 MiB, 24564 MiB

=== URLs ===
vLLM:       http://YOUR_IP:8100
Chat API:   http://YOUR_IP:8200
Prometheus: http://YOUR_IP:9091
DCGM:       http://YOUR_IP:9401
Locust:     http://YOUR_IP:8090
```

### 3.2 Test Chat API
```bash
./scripts/test.sh
```

Expected response:
```json
{
  "response": "Hello! How can I help you today?",
  "tokens_generated": 12,
  "latency_ms": 245.3,
  "model": "meta-llama/Llama-3.1-8B-Instruct"
}
```

### 3.3 Check Prometheus
```bash
# Get your RunPod IP
RUNPOD_IP=$(curl -s ifconfig.me)
echo "Prometheus: http://$RUNPOD_IP:9091"

# Test Prometheus
curl http://localhost:9091/api/v1/query?query=up
```

---

## 🎬 Step 4: Start Load Testing

### 4.1 Open Locust UI
```bash
RUNPOD_IP=$(curl -s ifconfig.me)
echo "Locust UI: http://$RUNPOD_IP:8090"
```

### 4.2 Configure Load Test
- Open browser: `http://YOUR_RUNPOD_IP:8090`
- Number of users: **10**
- Spawn rate: **2 users/second**
- Click **Start Swarming**

### 4.3 Watch Metrics
- **Locust**: See requests/sec, response times
- **Prometheus**: `http://YOUR_RUNPOD_IP:9091`
  - Query: `chat_requests_total`
  - Query: `chat_request_duration_seconds`
  - Query: `DCGM_FI_DEV_GPU_UTIL` (GPU utilization)

---

## 🎬 Step 5: Configure OptiInfra

### 5.1 Get Prometheus URL
```bash
RUNPOD_IP=$(curl -s ifconfig.me)
echo "Prometheus URL: http://$RUNPOD_IP:9091"
```

### 5.2 Update RunPod Credentials in OptiInfra
```powershell
# On your local machine (Windows)
$runpodIp = "YOUR_RUNPOD_IP"  # Replace with actual IP
$prometheusUrl = "http://${runpodIp}:9091"

$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod Demo"
    credentials = @{
        api_key = "YOUR_RUNPOD_API_KEY"
        prometheus_url = $prometheusUrl
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"
```

### 5.3 Trigger Collection
```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("cost", "performance", "resource")
    async_mode = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"
```

### 5.4 Check Dashboard
```powershell
# View RunPod data
Invoke-WebRequest -Uri "http://localhost:8005/api/v1/dashboard?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11&provider=runpod" | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 3

# Open Portal UI
Start-Process "http://localhost:3001/dashboard"
```

---

## 🎯 Demo Script (5 Minutes)

### **Slide 1: Show RunPod Console**
- Pod running with GPU
- Show cost: $0.69/hour

### **Slide 2: Show Services Running**
```bash
./scripts/status.sh
```
- All 5 services up
- GPU at 85% utilization

### **Slide 3: Test Chat API**
```bash
./scripts/test.sh
```
- Show response
- Show latency (~250ms)

### **Slide 4: Show Locust Load Testing**
- Open: `http://YOUR_IP:8090`
- 10 users generating traffic
- ~5 requests/second

### **Slide 5: Show Prometheus Metrics**
- Open: `http://YOUR_IP:9091`
- Query: `chat_requests_total`
- Query: `DCGM_FI_DEV_GPU_UTIL`

### **Slide 6: Show OptiInfra Dashboard**
- Open: `http://localhost:3001/dashboard`
- **Cost trends**: RunPod showing $0.69/hour
- **Performance**: GPU at 85%, latency 250ms
- **Recommendations**: "GPU underutilized, downsize to save $150/month"

### **Slide 7: Show All 4 Agents**
- **Cost Agent**: "GPU at 85%, consider smaller instance"
- **Performance Agent**: "KV cache too small, increase for 2x throughput"
- **Resource Agent**: "Consolidate workloads to save costs"
- **Application Agent**: "Quality baseline: 87%, monitoring for regression"

---

## 📊 Expected Metrics

### **Performance Metrics**
- **Latency**: 200-300ms per request
- **Throughput**: 5-10 requests/second
- **GPU Utilization**: 70-90%
- **Tokens/Second**: 50-100

### **Cost Metrics**
- **RTX 4090**: $0.69/hour = $16.56/day
- **With 85% GPU util**: Potential savings by downsizing
- **OptiInfra recommendation**: Save $150/month

---

## 🐛 Troubleshooting

### **Issue: Services not starting**
```bash
# Check logs
docker logs vllm-server
docker logs chat-api
docker logs prometheus-demo
```

### **Issue: vLLM downloading model slowly**
- First run takes 10-15 minutes
- Model is ~16GB
- Check: `docker logs vllm-server --follow`

### **Issue: GPU not detected**
```bash
# Check NVIDIA
nvidia-smi

# Check Docker runtime
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### **Issue: Prometheus not scraping**
```bash
# Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# Should show: chat-api, vllm, dcgm-exporter all UP
```

### **Issue: OptiInfra not collecting data**
```bash
# Check if Prometheus is accessible from outside
curl http://YOUR_RUNPOD_IP:9091/api/v1/query?query=up

# Make sure port 9091 is exposed in RunPod
```

---

## 🎬 Quick Commands Reference

```bash
# Start services
./scripts/start.sh

# Check status
./scripts/status.sh

# Test API
./scripts/test.sh

# View logs
docker logs vllm-server --follow
docker logs chat-api --follow

# Stop services
./scripts/stop.sh

# Restart a service
docker-compose restart vllm
docker-compose restart chat-api
```

---

## ✅ Success Checklist

- [ ] RunPod pod deployed with GPU
- [ ] All 5 services running
- [ ] Chat API responding
- [ ] Prometheus collecting metrics
- [ ] DCGM showing GPU metrics
- [ ] Locust generating load
- [ ] OptiInfra collecting from Prometheus
- [ ] Dashboard showing RunPod data
- [ ] All 4 agents providing recommendations

---

## 🚀 Ready to Deploy?

1. **Copy `runpod-demo-setup.sh` to your RunPod pod**
2. **Run: `bash runpod-demo-setup.sh`**
3. **Start services: `./scripts/start.sh`**
4. **Wait 10-15 minutes for model download**
5. **Test: `./scripts/test.sh`**
6. **Configure OptiInfra with Prometheus URL**
7. **Demo! 🎉**

---

**Total Setup Time**: 20-25 minutes (including model download)

**Demo Time**: 5-10 minutes

**Cost**: ~$0.69/hour on RTX 4090

---

*Need help? Check logs with `docker logs <container-name>` or run `./scripts/status.sh`*
