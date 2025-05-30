## Final Project (Phase 3) - Helm Package Management, VC and CI/CD

- QuakeWatch is a Flask-based web application that monitors and displays earthquake data.  
---

### 1. Package Management with Helm

**a. Goal**  
Migrate from static Kubernetes manifests (in Phase 2) to a reusable and versioned Helm chart.

**b. Steps**

1. Create `Chart.yaml` and `values.yaml` to define the chart and configurable inputs.
2. Migrate all Kubernetes manifests (`Deployment`, `Service`, `PVC`, `ConfigMap`) into `templates/`.
3. Templatize configuration using `.Values` references.

**Important!** Tag chart version with a `v` prefix (e.g.,`v1.0.0`) in `version` field of Chart.yaml
- Many CI pipelines, especially `GitHub Actions` use this prefix to correctly trigger workflows
```yaml
# Chart.yaml
apiVersion: v2
name: quakewatch-web-chart
description: Helm chart for the QuakeWatch earthquake monitoring app
type: application

version: v1.0.0 # Important! Prefix with 'v'

appVersion: "1.0.0" # informational only
```


**c. Key Manifests**

- `templates/deployment.yaml` – Flask app pod with volume mount and env vars.
- `templates/service.yaml` – Exposes port `5011` via LoadBalancer.
- `templates/pvc.yaml` – Claims storage for shared log files.
- `templates/configmap.yaml` – Defines log path (`/shared-logs`).
- `templates/tests/*.yaml` – Helm test hooks

**d. Verification**

- 1. Dry Run Render Validation

```bash
   helm upgrade --install quakewatch-init-release ./quakewatch-web-chart --dry-run --debug
```
- 2. Helm Test Automation

  - Note: This chart includes automated test hooks using `helm.sh/hook: test` 

   - Goal: ensure that key components (service, volume, storage) work correctly after deployment.
   - Test Manifests:

| File                                | Description                                       | Image     |
|-------------------------------------|---------------------------------------------------|-----------|
| `test-connection.yaml`              | Verifies service responds over HTTP               | `curlimages/curl` |
| `test-logs-path.yaml`               | Ensures PVC is mounted and log directory exists   | `busybox` |
| `test-pvc-access.yaml`              | Writes, reads, and deletes a file in the log path | `busybox` |

```bash
    # add the tests above in templates/tests, upgrade and process 
    helm upgrade --install quakewatch-init-release ./quakewatch-web-chart
    helm test quakewatch-init-release
    
    # verify tests
    kubectl logs -l "helm.sh/hook=test"
```
---

#### Helm Chart Publishing to OCI (Docker Hub)
##### a. Goal
  Use Helm's **native OCI support** to push packaged charts to Docker Hub as **OCI artifacts**.

 ##### b. Steps
  
```bash
   # Authenticate to Docker Hub
   helm registry login registry-1.docker.io \
   --username alkon100 \
   --password-stdin
```   
```bash
  # Package the chart 
  helm package ./quakewatch-web-chart
  
  # Output: quakewatch-web-chart-v1.0.0.tgz 
 ```
```bash
   # If there are few packaged charts, take the name of the latest one
   # Note: Sort these names in ascending order and take the last
   CHART_FILE=$(ls -1 quakewatch-web-chart-*.tgz | sort -V | tail -n1)
   echo $CHART_FILE
```


```bash
  # Push the chart to Docker Hub as an OCI Artifact 
  # helm push <chart-name>-<version>.tgz oci://<registry>/<namespace>
  # Note: <namespace> is usually username or org name 
  
  helm push "$CHART_FILE" oci://registry-1.docker.io/alkon100
  #helm push quakewatch-web-chart-v1.0.0.tgz oci://registry-1.docker.io/alkon100
```
---

### Deploy Stage: GitHub Actions → Argo CD → Kubernetes

This section describes how to wire **remote GitHub-hosted runner** into a **local Kubernetes cluster** running Argo CD, to trigger a full GitOps sync remotely.

---

#### 1. Declaratively expose Argo CD via NodePort + Ingress
a. Use `nip.io` for **DNS**

```bash
# 1. Fetch the public IP
PUBLIC_IP=$(curl -s ifconfig.me)

# 2. Build the nip.io hostname
INGRESS_HOST="${PUBLIC_IP}.nip.io"
echo {$INGRESS_HOST}

# 3. (Optional) verify it resolves
ping -c1 "$INGRESS_HOST"
```
- The networking flow:
```text
  [ External client ]
      ↓ DNS (via nip.io)
[ Ingress-NGINX controller Pod ]
      ↓ proxies HTTPS → 
[ argocd-server Service (ClusterIP port 443) ]
      ↓ forwards to Pod port 8080 (TLS)
[ argocd-server Pod ]

```
- Note 1: `hostNetwork: true` on the controller means the controller Pod listens on the host’s network
- Note 2: The Service still needs to be of `type: NodePort`, so that Argo CD’s own TLS port 443 is exposed internally, but Ingress talks to its clusterIP on port 443 (matching the ingress.yaml rule).

b. Configure GitHub Secrets 
     
- In the current GitHub repo: Settings → Secrets and variables → Actions, create:

`ARGOCD_SERVER` - The DNS name, i.e. the $INGRESS_HOST above 

`ARGOCD_APP` - The name of the Argo CD Application CR (the value in its `metadata.name` field)


Under the project `argocd-manifests/infra/` folder, add:

```yaml
# argocd-manifests/infra/service-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: argocd-server
  namespace: argocd
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: argocd-server
  ports:
    - name: https
      port: 443
      targetPort: 8080
      nodePort: 31000        # pick an unused port in 30000–32767
```

 