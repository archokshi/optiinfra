# PHASE5-5.5 PART1: Kubernetes Deployment - Code Implementation

**Phase**: PHASE5-5.5  
**Component**: Portal & Production - Kubernetes Deployment  
**Estimated Time**: 35 minutes (Code) + 30 minutes (Validation)  
**Dependencies**: ALL services (Cost Agent, Performance Agent, Resource Agent, Application Agent, Portal)

---

## Overview

Create Kubernetes deployment manifests and Helm charts for the complete OptiInfra stack, including all agents, databases, and the portal.

---

## Step 1: Create Kubernetes Directory Structure

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra
mkdir -p k8s\base
mkdir -p k8s\overlays\dev
mkdir -p k8s\overlays\prod
mkdir -p helm\optiinfra\templates
mkdir -p helm\optiinfra\charts
```

---

## Step 2: Create Namespace Configuration

### File: `k8s/base/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: optiinfra
  labels:
    name: optiinfra
    environment: production
```

---

## Step 3: Create PostgreSQL Deployment

### File: `k8s/base/postgresql.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgresql-config
  namespace: optiinfra
data:
  POSTGRES_DB: optiinfra
  POSTGRES_USER: optiinfra_user

---
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-secret
  namespace: optiinfra
type: Opaque
stringData:
  POSTGRES_PASSWORD: optiinfra_password_change_in_production

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-pvc
  namespace: optiinfra
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        envFrom:
        - configMapRef:
            name: postgresql-config
        - secretRef:
            name: postgresql-secret
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: postgresql-storage
        persistentVolumeClaim:
          claimName: postgresql-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: optiinfra
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

---

## Step 4: Create ClickHouse Deployment

### File: `k8s/base/clickhouse.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: clickhouse-pvc
  namespace: optiinfra
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clickhouse
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: clickhouse
  template:
    metadata:
      labels:
        app: clickhouse
    spec:
      containers:
      - name: clickhouse
        image: clickhouse/clickhouse-server:latest
        ports:
        - containerPort: 8123
          name: http
        - containerPort: 9000
          name: native
        volumeMounts:
        - name: clickhouse-storage
          mountPath: /var/lib/clickhouse
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      volumes:
      - name: clickhouse-storage
        persistentVolumeClaim:
          claimName: clickhouse-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  namespace: optiinfra
spec:
  selector:
    app: clickhouse
  ports:
  - port: 8123
    targetPort: 8123
    name: http
  - port: 9000
    targetPort: 9000
    name: native
  type: ClusterIP
```

---

## Step 5: Create Qdrant Deployment

### File: `k8s/base/qdrant.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-pvc
  namespace: optiinfra
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: qdrant-storage
        persistentVolumeClaim:
          claimName: qdrant-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: optiinfra
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
  type: ClusterIP
```

---

## Step 6: Create Cost Agent Deployment

### File: `k8s/base/cost-agent.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-agent-config
  namespace: optiinfra
data:
  AGENT_NAME: "cost-agent"
  AGENT_TYPE: "cost"
  AGENT_PORT: "8001"
  DATABASE_HOST: "postgresql"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "optiinfra"
  CLICKHOUSE_HOST: "clickhouse"
  CLICKHOUSE_PORT: "8123"
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: cost-agent-secret
  namespace: optiinfra
type: Opaque
stringData:
  DATABASE_USER: "optiinfra_user"
  DATABASE_PASSWORD: "optiinfra_password_change_in_production"
  GROQ_API_KEY: "your-groq-api-key-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-agent
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cost-agent
  template:
    metadata:
      labels:
        app: cost-agent
        agent-type: cost
    spec:
      containers:
      - name: cost-agent
        image: optiinfra/cost-agent:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: cost-agent-config
        - secretRef:
            name: cost-agent-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: cost-agent
  namespace: optiinfra
spec:
  selector:
    app: cost-agent
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

---

## Step 7: Create Performance Agent Deployment

### File: `k8s/base/performance-agent.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-agent-config
  namespace: optiinfra
data:
  AGENT_NAME: "performance-agent"
  AGENT_TYPE: "performance"
  AGENT_PORT: "8002"
  DATABASE_HOST: "postgresql"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "optiinfra"
  CLICKHOUSE_HOST: "clickhouse"
  CLICKHOUSE_PORT: "8123"
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: performance-agent-secret
  namespace: optiinfra
type: Opaque
stringData:
  DATABASE_USER: "optiinfra_user"
  DATABASE_PASSWORD: "optiinfra_password_change_in_production"
  GROQ_API_KEY: "your-groq-api-key-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: performance-agent
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: performance-agent
  template:
    metadata:
      labels:
        app: performance-agent
        agent-type: performance
    spec:
      containers:
      - name: performance-agent
        image: optiinfra/performance-agent:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8002
        envFrom:
        - configMapRef:
            name: performance-agent-config
        - secretRef:
            name: performance-agent-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: performance-agent
  namespace: optiinfra
spec:
  selector:
    app: performance-agent
  ports:
  - port: 8002
    targetPort: 8002
  type: ClusterIP
```

---

## Step 8: Create Resource Agent Deployment

### File: `k8s/base/resource-agent.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: resource-agent-config
  namespace: optiinfra
data:
  AGENT_NAME: "resource-agent"
  AGENT_TYPE: "resource"
  AGENT_PORT: "8003"
  DATABASE_HOST: "postgresql"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "optiinfra"
  CLICKHOUSE_HOST: "clickhouse"
  CLICKHOUSE_PORT: "8123"
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: resource-agent-secret
  namespace: optiinfra
type: Opaque
stringData:
  DATABASE_USER: "optiinfra_user"
  DATABASE_PASSWORD: "optiinfra_password_change_in_production"
  GROQ_API_KEY: "your-groq-api-key-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-agent
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resource-agent
  template:
    metadata:
      labels:
        app: resource-agent
        agent-type: resource
    spec:
      containers:
      - name: resource-agent
        image: optiinfra/resource-agent:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8003
        envFrom:
        - configMapRef:
            name: resource-agent-config
        - secretRef:
            name: resource-agent-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: resource-agent
  namespace: optiinfra
spec:
  selector:
    app: resource-agent
  ports:
  - port: 8003
    targetPort: 8003
  type: ClusterIP
```

---

## Step 9: Create Application Agent Deployment

### File: `k8s/base/application-agent.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: application-agent-config
  namespace: optiinfra
data:
  AGENT_NAME: "application-agent"
  AGENT_TYPE: "application"
  AGENT_PORT: "8004"
  DATABASE_HOST: "postgresql"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "optiinfra"
  CLICKHOUSE_HOST: "clickhouse"
  CLICKHOUSE_PORT: "8123"
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
  LOG_LEVEL: "INFO"

---
apiVersion: v1
kind: Secret
metadata:
  name: application-agent-secret
  namespace: optiinfra
type: Opaque
stringData:
  DATABASE_USER: "optiinfra_user"
  DATABASE_PASSWORD: "optiinfra_password_change_in_production"
  GROQ_API_KEY: "your-groq-api-key-here"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: application-agent
  namespace: optiinfra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: application-agent
  template:
    metadata:
      labels:
        app: application-agent
        agent-type: application
    spec:
      containers:
      - name: application-agent
        image: optiinfra/application-agent:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8004
        envFrom:
        - configMapRef:
            name: application-agent-config
        - secretRef:
            name: application-agent-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: application-agent
  namespace: optiinfra
spec:
  selector:
    app: application-agent
  ports:
  - port: 8004
    targetPort: 8004
  type: ClusterIP
```

---

## Step 10: Create Portal Deployment

### File: `k8s/base/portal.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: portal-config
  namespace: optiinfra
data:
  NEXT_PUBLIC_API_URL: "http://localhost:3000"
  COST_AGENT_URL: "http://cost-agent:8001"
  PERFORMANCE_AGENT_URL: "http://performance-agent:8002"
  RESOURCE_AGENT_URL: "http://resource-agent:8003"
  APPLICATION_AGENT_URL: "http://application-agent:8004"

---
apiVersion: v1
kind: Secret
metadata:
  name: portal-secret
  namespace: optiinfra
type: Opaque
stringData:
  AUTH_SECRET: "optiinfra-secret-key-change-in-production"
  AUTH_URL: "http://localhost:3000"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portal
  namespace: optiinfra
spec:
  replicas: 2
  selector:
    matchLabels:
      app: portal
  template:
    metadata:
      labels:
        app: portal
    spec:
      containers:
      - name: portal
        image: optiinfra/portal:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: portal-config
        - secretRef:
            name: portal-secret
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: portal
  namespace: optiinfra
spec:
  selector:
    app: portal
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
```

---

## Step 11: Create Ingress Configuration

### File: `k8s/base/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: optiinfra-ingress
  namespace: optiinfra
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: optiinfra.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: portal
            port:
              number: 3000
      - path: /api/cost
        pathType: Prefix
        backend:
          service:
            name: cost-agent
            port:
              number: 8001
      - path: /api/performance
        pathType: Prefix
        backend:
          service:
            name: performance-agent
            port:
              number: 8002
      - path: /api/resource
        pathType: Prefix
        backend:
          service:
            name: resource-agent
            port:
              number: 8003
      - path: /api/application
        pathType: Prefix
        backend:
          service:
            name: application-agent
            port:
              number: 8004
```

---

## Step 12: Create Kustomization File

### File: `k8s/base/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: optiinfra

resources:
  - namespace.yaml
  - postgresql.yaml
  - clickhouse.yaml
  - qdrant.yaml
  - cost-agent.yaml
  - performance-agent.yaml
  - resource-agent.yaml
  - application-agent.yaml
  - portal.yaml
  - ingress.yaml

commonLabels:
  app.kubernetes.io/name: optiinfra
  app.kubernetes.io/version: "1.0.0"
```

---

## Step 13: Create Helm Chart Structure

### File: `helm/optiinfra/Chart.yaml`

```yaml
apiVersion: v2
name: optiinfra
description: A Helm chart for OptiInfra - AI-Powered LLM Infrastructure Optimization
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - optiinfra
  - llm
  - optimization
  - ai
maintainers:
  - name: OptiInfra Team
    email: team@optiinfra.com
```

---

## Step 14: Create Helm Values File

### File: `helm/optiinfra/values.yaml`

```yaml
# Default values for optiinfra

global:
  namespace: optiinfra
  imagePullPolicy: IfNotPresent

# PostgreSQL Configuration
postgresql:
  enabled: true
  image: postgres:15-alpine
  storage: 10Gi
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  config:
    database: optiinfra
    user: optiinfra_user
    password: optiinfra_password_change_in_production

# ClickHouse Configuration
clickhouse:
  enabled: true
  image: clickhouse/clickhouse-server:latest
  storage: 20Gi
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

# Qdrant Configuration
qdrant:
  enabled: true
  image: qdrant/qdrant:latest
  storage: 10Gi
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

# Cost Agent Configuration
costAgent:
  enabled: true
  replicas: 1
  image: optiinfra/cost-agent:latest
  port: 8001
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  groqApiKey: "your-groq-api-key-here"

# Performance Agent Configuration
performanceAgent:
  enabled: true
  replicas: 1
  image: optiinfra/performance-agent:latest
  port: 8002
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  groqApiKey: "your-groq-api-key-here"

# Resource Agent Configuration
resourceAgent:
  enabled: true
  replicas: 1
  image: optiinfra/resource-agent:latest
  port: 8003
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  groqApiKey: "your-groq-api-key-here"

# Application Agent Configuration
applicationAgent:
  enabled: true
  replicas: 1
  image: optiinfra/application-agent:latest
  port: 8004
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  groqApiKey: "your-groq-api-key-here"

# Portal Configuration
portal:
  enabled: true
  replicas: 2
  image: optiinfra/portal:latest
  port: 3000
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  authSecret: "optiinfra-secret-key-change-in-production"
  authUrl: "http://localhost:3000"

# Ingress Configuration
ingress:
  enabled: true
  className: nginx
  host: optiinfra.local
  annotations: {}
```

---

## Step 15: Create Docker Build Scripts

### File: `scripts/build-images.sh`

```bash
#!/bin/bash

# Build Docker images for all services

echo "Building OptiInfra Docker images..."

# Build Cost Agent
echo "Building Cost Agent..."
cd services/cost-agent
docker build -t optiinfra/cost-agent:latest .
cd ../..

# Build Performance Agent
echo "Building Performance Agent..."
cd services/performance-agent
docker build -t optiinfra/performance-agent:latest .
cd ../..

# Build Resource Agent
echo "Building Resource Agent..."
cd services/resource-agent
docker build -t optiinfra/resource-agent:latest .
cd ../..

# Build Application Agent
echo "Building Application Agent..."
cd services/application-agent
docker build -t optiinfra/application-agent:latest .
cd ../..

# Build Portal
echo "Building Portal..."
cd portal
docker build -t optiinfra/portal:latest .
cd ..

echo "All images built successfully!"
```

---

## Step 16: Create Deployment Script

### File: `scripts/deploy.sh`

```bash
#!/bin/bash

# Deploy OptiInfra to Kubernetes

echo "Deploying OptiInfra to Kubernetes..."

# Apply base configurations
kubectl apply -k k8s/base/

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/postgresql \
  deployment/clickhouse \
  deployment/qdrant \
  deployment/cost-agent \
  deployment/performance-agent \
  deployment/resource-agent \
  deployment/application-agent \
  deployment/portal \
  -n optiinfra

echo "Deployment complete!"
echo "Access the portal at: http://optiinfra.local"
```

---

## Summary

**Files Created:**
1. `k8s/base/namespace.yaml` - Namespace configuration
2. `k8s/base/postgresql.yaml` - PostgreSQL deployment
3. `k8s/base/clickhouse.yaml` - ClickHouse deployment
4. `k8s/base/qdrant.yaml` - Qdrant deployment
5. `k8s/base/cost-agent.yaml` - Cost Agent deployment
6. `k8s/base/performance-agent.yaml` - Performance Agent deployment
7. `k8s/base/resource-agent.yaml` - Resource Agent deployment
8. `k8s/base/application-agent.yaml` - Application Agent deployment
9. `k8s/base/portal.yaml` - Portal deployment
10. `k8s/base/ingress.yaml` - Ingress configuration
11. `k8s/base/kustomization.yaml` - Kustomize configuration
12. `helm/optiinfra/Chart.yaml` - Helm chart metadata
13. `helm/optiinfra/values.yaml` - Helm values
14. `scripts/build-images.sh` - Docker build script
15. `scripts/deploy.sh` - Kubernetes deployment script

**Kubernetes Resources:**
- ✅ Namespace
- ✅ ConfigMaps (6)
- ✅ Secrets (5)
- ✅ PersistentVolumeClaims (3)
- ✅ Deployments (8)
- ✅ Services (8)
- ✅ Ingress (1)

**Features:**
- ✅ Complete stack deployment
- ✅ Resource limits and requests
- ✅ Health checks (liveness & readiness)
- ✅ Persistent storage
- ✅ Service discovery
- ✅ Ingress routing
- ✅ Helm chart support
- ✅ Kustomize support

---

**Next**: PHASE5-5.5_PART2_Execution_and_Validation.md
