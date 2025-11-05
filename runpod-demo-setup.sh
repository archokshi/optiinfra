#!/bin/bash
# OptiInfra RunPod Demo - Complete Setup Script
# Copy this script to your RunPod pod and run: bash runpod-demo-setup.sh

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=================================="
echo "OptiInfra RunPod Demo Setup"
echo "=================================="

# Get RunPod public IP
RUNPOD_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
PROJECT_DIR="/workspace/runpod-demo-app"

echo -e "${GREEN}Creating project at: $PROJECT_DIR${NC}"
mkdir -p $PROJECT_DIR && cd $PROJECT_DIR

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}Creating application files...${NC}"

# Docker Compose
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.9'
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm-server
    runtime: nvidia
    command: --model meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0 --port 8000 --max-model-len 4096 --max-num-seqs 8 --gpu-memory-utilization 0.7 --kv-cache-dtype fp16 --dtype float16 --trust-remote-code
    ports: ["8100:8000"]
    volumes: ["./models:/root/.cache/huggingface"]
    deploy:
      resources:
        reservations:
          devices: [{driver: nvidia, count: 1, capabilities: [gpu]}]
    restart: unless-stopped
  
  chat-api:
    build: {context: ./chat-api}
    container_name: chat-api
    environment: {VLLM_URL: "http://vllm:8000"}
    ports: ["8200:8080"]
    depends_on: [vllm]
    restart: unless-stopped
  
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-demo
    command: ['--config.file=/etc/prometheus/prometheus.yml', '--storage.tsdb.retention.time=7d']
    ports: ["9091:9090"]
    volumes: ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]
    restart: unless-stopped
  
  dcgm-exporter:
    image: nvcr.io/nvidia/k8s/dcgm-exporter:3.1.8-3.1.5-ubuntu22.04
    container_name: dcgm-exporter
    runtime: nvidia
    ports: ["9401:9400"]
    deploy:
      resources:
        reservations:
          devices: [{driver: nvidia, count: 1, capabilities: [gpu]}]
    restart: unless-stopped
  
  locust:
    build: {context: ./load-generator}
    container_name: locust
    environment: {CHAT_API_URL: "http://chat-api:8080"}
    ports: ["8090:8089"]
    depends_on: [chat-api]
    command: -f /locust/locustfile.py --host=http://chat-api:8080
    restart: unless-stopped
COMPOSE_EOF

mkdir -p chat-api monitoring load-generator scripts

# Chat API
cat > chat-api/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

cat > chat-api/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
prometheus-client==0.19.0
pydantic==2.5.0
EOF

cat > chat-api/main.py << 'CHATAPI_EOF'
import time, logging, httpx, os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000")
app = FastAPI(title="OptiInfra RunPod Demo")
http_client = httpx.AsyncClient(timeout=60.0)

chat_requests_total = Counter('chat_requests_total', 'Total requests', ['status'])
chat_request_duration = Histogram('chat_request_duration_seconds', 'Duration')
chat_tokens_generated = Counter('chat_tokens_generated_total', 'Tokens')

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = Field(default=200, ge=1, le=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class ChatResponse(BaseModel):
    response: str
    tokens_generated: int
    latency_ms: float
    model: str

@app.get("/health")
async def health_check():
    try:
        response = await http_client.get(f"{VLLM_URL}/health", timeout=5.0)
        return {"status": "healthy" if response.status_code == 200 else "degraded"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    try:
        vllm_request = {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": request.message}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        response = await http_client.post(f"{VLLM_URL}/v1/chat/completions", json=vllm_request)
        response.raise_for_status()
        result = response.json()
        assistant_message = result["choices"][0]["message"]["content"]
        tokens_used = result["usage"]["completion_tokens"]
        latency = (time.time() - start_time) * 1000
        
        chat_requests_total.labels(status="success").inc()
        chat_request_duration.observe(time.time() - start_time)
        chat_tokens_generated.inc(tokens_used)
        
        return ChatResponse(response=assistant_message, tokens_generated=tokens_used, latency_ms=latency, model="meta-llama/Llama-3.1-8B-Instruct")
    except Exception as e:
        chat_requests_total.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
CHATAPI_EOF

# Load Generator
cat > load-generator/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /locust
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY locustfile.py .
EXPOSE 8089
ENTRYPOINT ["locust"]
EOF

cat > load-generator/requirements.txt << 'EOF'
locust==2.17.0
httpx==0.25.1
EOF

cat > load-generator/locustfile.py << 'LOCUST_EOF'
import random
from locust import HttpUser, task, between

QUERIES = [
    "What is 2+2?", "Hello!", "Tell me a joke",
    "Explain machine learning", "What is cloud computing?",
    "Write a detailed explanation of transformers"
]

class ChatUser(HttpUser):
    wait_time = between(2, 10)
    
    @task
    def send_query(self):
        self.client.post("/chat", json={"message": random.choice(QUERIES), "max_tokens": 150})
LOCUST_EOF

# Prometheus
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'chat-api'
    static_configs: [{targets: ['chat-api:8080']}]
  - job_name: 'vllm'
    static_configs: [{targets: ['vllm:8000']}]
  - job_name: 'gpu'
    static_configs: [{targets: ['dcgm-exporter:9400']}]
EOF

# Scripts
cat > scripts/start.sh << 'EOF'
#!/bin/bash
echo "Starting services (10-15 min first run)..."
docker-compose up -d
EOF
chmod +x scripts/start.sh

cat > scripts/stop.sh << 'EOF'
#!/bin/bash
docker-compose down
EOF
chmod +x scripts/stop.sh

cat > scripts/status.sh << 'STATUSEOF'
#!/bin/bash
echo "=== Services ==="
docker-compose ps
echo ""
echo "=== GPU ==="
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "N/A"
echo ""
RUNPOD_IP=$(curl -s ifconfig.me)
echo "=== URLs ==="
echo "vLLM:       http://$RUNPOD_IP:8100"
echo "Chat API:   http://$RUNPOD_IP:8200"
echo "Prometheus: http://$RUNPOD_IP:9091"
echo "DCGM:       http://$RUNPOD_IP:9401"
echo "Locust:     http://$RUNPOD_IP:8090"
STATUSEOF
chmod +x scripts/status.sh

cat > scripts/test.sh << 'EOF'
#!/bin/bash
curl -X POST http://localhost:8200/chat -H "Content-Type: application/json" -d '{"message":"Hello!","max_tokens":50}' | python3 -m json.tool
EOF
chmod +x scripts/test.sh

cat > README.md << README_EOF
# OptiInfra RunPod Demo - Llama-3.1-8B Chatbot

## Quick Start
\`\`\`bash
./scripts/start.sh    # Start all services
./scripts/status.sh   # Check status
./scripts/test.sh     # Test chat API
\`\`\`

## Services
- vLLM:       http://$RUNPOD_IP:8100
- Chat API:   http://$RUNPOD_IP:8200
- Prometheus: http://$RUNPOD_IP:9091
- DCGM:       http://$RUNPOD_IP:9401
- Locust:     http://$RUNPOD_IP:8090

## OptiInfra Integration
Prometheus URL: http://$RUNPOD_IP:9091

Setup complete! Run ./scripts/start.sh
README_EOF

echo ""
echo -e "${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "  1. ./scripts/start.sh"
echo "  2. ./scripts/status.sh (wait 10-15 min)"
echo "  3. ./scripts/test.sh"
echo ""
echo "URLs:"
echo "  vLLM:        http://$RUNPOD_IP:8100"
echo "  Chat API:    http://$RUNPOD_IP:8200"
echo "  Prometheus:  http://$RUNPOD_IP:9091"
echo "  DCGM:        http://$RUNPOD_IP:9401"
echo "  Locust:      http://$RUNPOD_IP:8090"
echo ""
echo "For OptiInfra: Use Prometheus URL http://$RUNPOD_IP:9091"
echo ""
