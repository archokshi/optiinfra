# Kubernetes Deployment Manifests

This directory contains Kubernetes manifests for deploying OptiInfra.

## Structure

```
k8s/
├── base/                 # Base manifests (environment-agnostic)
│   ├── namespace.yaml
│   ├── databases/        # PostgreSQL, ClickHouse, Qdrant, Redis
│   ├── orchestrator/     # Orchestrator deployment
│   ├── agents/           # All agent deployments
│   ├── portal/           # Portal deployment
│   └── kustomization.yaml
├── overlays/             # Environment-specific overlays
│   ├── development/
│   ├── staging/
│   └── production/
└── README.md
```

## Usage

### Deploy to Development

```bash
kubectl apply -k k8s/overlays/development
```

### Deploy to Staging

```bash
kubectl apply -k k8s/overlays/staging
```

### Deploy to Production

```bash
kubectl apply -k k8s/overlays/production
```

## Prerequisites

1. **Kubernetes cluster** (1.24+)
2. **kubectl** configured
3. **Secrets created**:
   ```bash
   kubectl create secret generic postgres-credentials \
     --from-literal=username=optiinfra \
     --from-literal=password=your-password \
     -n optiinfra
   
   kubectl create secret generic api-keys \
     --from-literal=openai-api-key=sk-your-key \
     --from-literal=anthropic-api-key=sk-ant-your-key \
     -n optiinfra
   ```

## Kustomize

We use Kustomize for managing environment-specific configurations:

- **base/**: Common resources shared across all environments
- **overlays/**: Environment-specific patches and configurations

### Example Overlay Structure

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: optiinfra

bases:
  - ../../base

patchesStrategicMerge:
  - replica-patch.yaml
  - resource-patch.yaml

configMapGenerator:
  - name: optiinfra-config
    literals:
      - LOG_LEVEL=info
      - ENVIRONMENT=production
```

## Monitoring

Prometheus ServiceMonitors are included in `base/monitoring/`.

## Scaling

Horizontal Pod Autoscalers (HPA) are configured for:
- Orchestrator
- All agents
- Portal

## Storage

Persistent volumes are used for:
- PostgreSQL data
- ClickHouse data
- Qdrant data
- Redis data

## Networking

- **Services**: ClusterIP for internal communication
- **Ingress**: For external access to portal and API
- **Network Policies**: Restrict traffic between services

## Security

- RBAC roles and bindings
- Pod Security Policies
- Network Policies
- Secret management

## Backup

See [DEPLOYMENT.md](../docs/DEPLOYMENT.md) for backup and recovery procedures.
