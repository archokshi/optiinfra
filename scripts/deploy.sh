#!/bin/bash
set -e

echo "🚀 OptiInfra Deployment Script"
echo "=============================="
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to a Kubernetes cluster."
    echo "Please configure kubectl to connect to your cluster."
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"
echo ""

# Prompt for environment
echo "Select deployment environment:"
echo "1) Development"
echo "2) Staging"
echo "3) Production"
read -p "Enter choice [1-3]: " env_choice

case $env_choice in
    1)
        ENVIRONMENT="development"
        ;;
    2)
        ENVIRONMENT="staging"
        ;;
    3)
        ENVIRONMENT="production"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Deploying to: $ENVIRONMENT"
echo ""

# Apply Kubernetes manifests
echo "📦 Applying Kubernetes manifests..."
kubectl apply -k k8s/overlays/$ENVIRONMENT

echo ""
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/optiinfra-orchestrator \
    deployment/optiinfra-cost-agent \
    deployment/optiinfra-performance-agent \
    deployment/optiinfra-resource-agent \
    deployment/optiinfra-application-agent \
    -n optiinfra

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Run 'kubectl get pods -n optiinfra' to check pod status"
echo "Run 'kubectl logs -f deployment/optiinfra-orchestrator -n optiinfra' to view logs"
