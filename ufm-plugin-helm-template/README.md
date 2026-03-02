# UFM Plugin Helm Chart Template

This directory is a **Helm chart template** for deploying UFM plugins alongside an existing UFM Enterprise installation. Use it as a base to create a chart for your own plugin or to deploy multiple plugins with a single release.

## Prerequisites

- **UFM Enterprise** must already be installed in the cluster (this chart does not install UFM).
- **Shared PVC**: UFM and plugins use a common PersistentVolumeClaim for `conf/` and `log/` (e.g. `conf/plugins/<plugin_name>`, `log/plugins/<plugin_name>`).
- **UFM ConfigMap**: The chart expects a ConfigMap named `{ufmFullname}-config` with key `UFM_VERSION` (typically provided by the UFM Enterprise chart).
- **RDMA device plugin** (if your plugin uses InfiniBand): Cluster must have the RDMA device plugin so that the resource `rdma/hca_shared` (or your configured name) is available.

## Quick Start

1. Copy this template to your plugin repo or a dedicated charts repo:
   ```bash
   cp -r ufm-plugin-helm-template my-ufm-plugin-chart
   cd my-ufm-plugin-chart
   ```

2. Customize `Chart.yaml`:
   - Set `name` (e.g. `my-ufm-plugin`).
   - Set `description` and `version`/`appVersion` as needed.

3. Put your plugin and UFM settings in the chart’s `values.yaml` (or in a separate file if you prefer). Example for a **plugin-specific chart** (one chart = one plugin):
   ```yaml
   ufmFullname: "ufm-ufm-enterprise"   # Must match the UFM release fullname
   namespace: "ufm-enterprise"

   plugins:
     items:
       - name: my_plugin
         image: my-registry/my-ufm-plugin
         tag: "1.0.0"
         imagePullPolicy: IfNotPresent
         port: 8401
         healthEndpoint: /health
         healthPort: 8401
   ```

4. Install or upgrade:
   - **Plugin-specific chart** (your plugin is in the chart’s default `values.yaml`): you don’t need `-f`. Just run:
     ```bash
     helm upgrade --install my-ufm-plugin . -n ufm-enterprise
     ```
   - Use `-f my-values.yaml` only when you want to override defaults or use a separate values file (e.g. different namespace, image, or one chart deploying multiple plugins).

## Creating a Helm Chart for Your Own Plugin

### 1. Start from this template

- Copy the entire `ufm-plugin-helm-template` directory and rename it (e.g. to your plugin name).
- Optionally remove or simplify `examples/` if you only ship one plugin.

### 2. Adjust `Chart.yaml`

- **name**: Use a unique chart name (e.g. `ufm-plugin-log-streamer`).
- **description**: One line describing your plugin.
- **version**: Semantic version of the chart (e.g. `1.0.0`).
- **appVersion**: Version of the plugin image (e.g. `"1.0.2"`).

### 3. Configure `values.yaml`

Values used by the template:

| Value | Description | Required |
|-------|-------------|----------|
| `ufmFullname` | Full name of the UFM Enterprise release (used for naming and for the UFM config ConfigMap). | Yes |
| `namespace` | Kubernetes namespace (should match UFM). | Yes |
| `existingClaim` | PVC claim name for UFM files. Defaults to `{ufmFullname}-files`. | No |
| `configMapName` | ConfigMap name for `plugins.yaml`. Defaults to `{ufmFullname}-plugins`. | No |
| `ufmUrl` | UFM base URL for health checks. Defaults to `http://{ufmFullname}.{namespace}.svc.cluster.local:8000/app/ufm_version`. Override if UFM is reached differently. | No |
| `rdma.resourceName` | RDMA resource name (e.g. `rdma/hca_shared`). Only used when `rdma.resourceCount` is not `"0"`. | No |
| `rdma.resourceCount` | Number of RDMA resources per plugin pod; default `"0"`. Set to `"1"` (or more) when the plugin uses InfiniBand. | No |
| `plugins.defaultResources` | Default `requests`/`limits` when a plugin does not set `resources`. | No |
| `plugins.items` | List of plugin definitions (see below). | Yes (can be empty) |
| `tolerations` | Pod tolerations. | No |
| `nodeSelector` | Pod node selector. | No |
| `imagePullSecrets` | Image pull secrets. | No |

### 4. Define each plugin in `plugins.items`

Each item can have:

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Plugin name (used in paths and labels; use underscores, e.g. `my_plugin`). | Yes |
| `image` | Container image repository (no tag). | Yes |
| `tag` | Image tag. | Yes |
| `imagePullPolicy` | e.g. `IfNotPresent` or `Always`. | No (default: IfNotPresent) |
| `port` | TCP port the plugin listens on (exposed to UFM/config). | No |
| `healthEndpoint` | HTTP path for health checks (e.g. `/health`). | No |
| `healthPort` | Port for health HTTP check; defaults to `port`. | No |
| `host` | Host in generated `plugins.yaml`; default `127.0.0.1`. | No |
| `resources` | `requests`/`limits` for this plugin; overrides `plugins.defaultResources`. | No |
| `livenessInitialDelay` | Liveness probe initial delay (seconds). | No |
| `livenessPeriod` | Liveness probe period (seconds). | No |
| `livenessTimeout` | Liveness probe timeout (seconds). | No |
| `livenessFailureThreshold` | Liveness failure threshold. | No |
| `readinessInitialDelay` | Readiness probe initial delay (seconds). | No |
| `readinessPeriod` | Readiness probe period (seconds). | No |
| `readinessTimeout` | Readiness probe timeout (seconds). | No |
| `readinessFailureThreshold` | Readiness failure threshold. | No |

Example for a plugin with HTTP health and custom resources:

```yaml
plugins:
  items:
    - name: my_plugin
      image: my-registry/my-ufm-plugin
      tag: "1.0.0"
      port: 8401
      healthEndpoint: /health
      healthPort: 8401
      resources:
        requests:
          memory: "256Mi"
          cpu: "100m"
        limits:
          memory: "512Mi"
          cpu: "500m"
```

### 5. What the chart generates

- **Deployment per plugin**: One Deployment per entry in `plugins.items`, with:
  - Init container that runs `/init.sh -ufm_version ${UFM_VERSION}` and mounts plugin config/log dirs from the shared PVC.
  - Main container with the same mounts, optional `PLUGIN_PORT`/`HEALTH_ENDPOINT`/`HEALTH_PORT`, and RDMA resources when configured.
  - Pod affinity so the plugin runs on the same node as the UFM pod (`app: {ufmFullname}`).
  - Liveness and readiness probes using a generated health script (ConfigMap).
- **ConfigMap `plugins.yaml`**: One ConfigMap (name from `configMapName` / default `{ufmFullname}-plugins`) containing a `plugins.yaml` consumed by UFM (list of name, host, port, tag).
- **Health scripts ConfigMap**: A ConfigMap with `health-check.sh` that verifies UFM is reachable and, if configured, the plugin’s health endpoint or port.

### 6. Plugin image expectations

Your plugin image should:

- Provide **`/init.sh`** that accepts `-ufm_version <version>` and initializes config under `/config` and logs under `/log` (these are mounted from the shared PVC subpaths `conf/plugins/<name>` and `log/plugins/<name>`).
- If you use health checks: either expose an HTTP **health endpoint** (set `healthEndpoint` and optionally `healthPort`) or a **TCP port** (set `port`); the chart’s health script will use it.

### 7. RDMA / InfiniBand

If your plugin does **not** use RDMA devices, you can still use the chart by setting `rdma.resourceCount: "0"` and ensuring the cluster does not require that resource for scheduling (or adjust the deployment template to make the RDMA limit conditional). If your cluster uses a different RDMA resource name, set `rdma.resourceName` accordingly.

### 8. Validation and CI

- Run a dry-run with your values:
  ```bash
  helm template my-ufm-plugin . -f my-values.yaml -n ufm-enterprise
  ```
- Lint the chart:
  ```bash
  helm lint . -f ci-values.yaml
  ```
- Use `ci-values.yaml` in CI; it provides minimal required values (including `rdma`) so that `helm template` and `helm lint` succeed.

## Examples

- **examples/empty-plugins-config.yaml** – No plugins; use to create only the `plugins.yaml` ConfigMap so UFM can mount it before adding plugins later.
- **examples/log-streamer-config.yaml** – Sample values for the log_streamer plugin.

## Packaging and distributing

```bash
helm package .
# Install from tgz (no -f needed if your chart’s values.yaml already has the plugin):
helm install my-ufm-plugin ufm-plugin-1.0.0.tgz -n ufm-enterprise
# Or override / use a custom values file:
helm install my-ufm-plugin ufm-plugin-1.0.0.tgz -n ufm-enterprise -f my-values.yaml
```

## Summary

1. Copy this template and set `Chart.yaml` and `values.yaml` (put your plugin in `plugins.items` in the chart’s `values.yaml` for a plugin-specific chart).
2. Set `ufmFullname` and `namespace` to match your UFM install.
3. Add your plugin under `plugins.items` with at least `name`, `image`, and `tag`; set `port`/`healthEndpoint`/`healthPort` and `rdma` as needed.
4. Ensure your image has `/init.sh` and, if used, a health endpoint or port.
5. Install with `helm upgrade --install` (no `-f` needed if defaults are in the chart); use `-f` only to override or use a separate values file.
