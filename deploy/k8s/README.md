# Kubernetes Deployment

This folder contains a minimal-but-complete deployment for running the feature producer and model consumer services on a Kubernetes cluster where they can be scaled independently.

## Components

| File | Purpose |
| --- | --- |
| `namespace.yaml` | Creates the dedicated `hm-sense` namespace. |
| `configmap.yaml` | Holds shared configuration used by both services. Override values or mount a Secret if you need credentials. |
| `feature-producer.yaml` | Deployment + ClusterIP Service for the feature API. Default image placeholder `ghcr.io/your-org/feature-producer:latest`. |
| `model-consumer.yaml` | Deployment + Service for the prediction API. Points at the in-cluster feature service (`http://feature-producer.hm-sense.svc.cluster.local:8000/api`). |
| `hpa.yaml` | HorizontalPodAutoscalers that scale pods between 2–6 replicas based on 50% CPU utilization. |

## Usage

1. Build and push container images (or publish via your CI pipeline). Update the image references in the deployment manifests if you use a different registry.
2. Apply the manifests:
   ```bash
   kubectl apply -f deploy/k8s/namespace.yaml
   kubectl apply -f deploy/k8s/configmap.yaml
   kubectl apply -f deploy/k8s/feature-producer.yaml
   kubectl apply -f deploy/k8s/model-consumer.yaml
   kubectl apply -f deploy/k8s/hpa.yaml
   ```
3. Expose the `model-consumer` service externally (e.g., via an Ingress or LoadBalancer) if clients outside the cluster need to call `/api/predictions`.
4. Adjust replica counts, resource requests/limits, and HPA thresholds to match real traffic once metrics are available.

Because both Deployments are stateless and read configuration from environment variables, they can scale horizontally without additional changes. If you need per-environment settings, create environment-specific overlays (e.g., using Kustomize or Helm) that swap out the ConfigMap values and image tags.
