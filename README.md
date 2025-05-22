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
  Use Helm's **native OCI support** to push packaged charts to Docker Hub as OCI artifacts.

 ##### b. Steps
  
```bash
   # Authenticate 
   helm registry login registry-1.docker.io \
   --username alkon100 \
   --password-stdin
```   
```bash
  # Package the chart
  helm package ./quakewatch-web-chart
  
  # Save the chart to local OCI cache
  helm chart save quakewatch-web-chart-0.1.0.tgz \
    oci://registry-1.docker.io/alkon100/quakewatch-web-chart:v0.1.0
  
  # Push the chart to Docker Hub
  helm chart push oci://registry-1.docker.io/alkon100/quakewatch-web-chart:v0.1.0
```
 - **Important!** Tag charts as v0.1.0 (with a `v` prefix) to match Git tags and GitHub Actions conventions.
      This improves consistency across CI pipelines, Helm charts, and Git history.