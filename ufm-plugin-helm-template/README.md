# UFM Plugin Helm Chart Template

This directory is a **Helm chart template** for deploying UFM plugins alongside an existing UFM Enterprise installation. Use it as a base to create a chart for your own plugin or to deploy multiple plugins with a single release.

## Prerequisites

- **UFM Enterprise** must already be installed in the cluster (this chart does not install UFM).
- **`namespace` and `ufmFullname`**: Set these to the same values used when you installed UFM. The chart does not discover them automatically. To find them: `helm list -A | grep ufm` (namespace is the NAMESPACE column, release name is the NAME column; `ufmFullname` is typically `ufm-<release-name>`—see your UFM install docs). In CI, use the same variables you use for the UFM install.
- **Shared PVC**: UFM has a single PVC for its data. This chart uses that same PVC and mounts subpaths `conf/plugins/<plugin_name>` and `log/plugins/<plugin_name>` for each plugin. UFM does not create or manage these subpaths—the plugin chart does. Default claim name is `{ufmFullname}-files`; set `existingClaim` if your UFM uses a different PVC name.
- **UFM ConfigMap**: The chart expects a ConfigMap named `{ufmFullname}-config` with key `UFM_VERSION` in the same namespace (typically provided by the UFM Enterprise chart). The init container reads `UFM_VERSION` from this ConfigMap and passes it to `/init.sh -ufm_version`. **If this ConfigMap or key is missing, plugin pods will not start** (Kubernetes will report the missing reference). Install UFM first or create the ConfigMap before deploying plugins.
- **RDMA device plugin** (if your plugin uses InfiniBand): Cluster must have the RDMA device plugin so that the resource `rdma/hca_shared` (or your configured name) is available. Some plugins may also require components from the NVIDIA Network Operator; see your plugin’s documentation.

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
         livenessProbe:
           httpGet: { path: /health, port: 8401 }
           initialDelaySeconds: 60
           periodSeconds: 30
         readinessProbe:
           httpGet: { path: /health, port: 8401 }
           initialDelaySeconds: 10
           periodSeconds: 10
   ```

4. Install:
   ```bash
   helm install my-ufm-plugin . -n ufm-enterprise
   ```
   To override values or use a separate values file, add `-f my-values.yaml` to the command.

## Creating a Helm Chart for Your Own Plugin

### 1. Start from this template

- Copy the `ufm-plugin-helm-template` directory and rename it (e.g. to your plugin name). You can omit the `examples/` folder when copying if you only need the chart files; see the repo’s `examples/` for sample values.

### 2. Adjust `Chart.yaml`

- **name**: Use a unique chart name (e.g. `ufm-plugin-log-streamer`).
- **description**: One line describing your plugin.
- **version**: Semantic version of the chart (e.g. `1.0.0`).
- **appVersion**: Version of the plugin image (e.g. `"1.0.2"`).

### 3. Configure `values.yaml`

Values used by the template:

| Value | Description | Required |
|-------|-------------|----------|
| `ufmFullname` | Full name of the UFM Enterprise release (used for naming and for the UFM config ConfigMap). Must match the namespace and release name used when you installed UFM. | Yes |
| `namespace` | Kubernetes namespace. Must match the namespace where UFM is installed (see Prerequisites for how to find it). | Yes |
| `existingClaim` | PVC claim name for UFM files. Defaults to `{ufmFullname}-files` to match the UFM Enterprise chart. Set this if your UFM uses a different PVC name. | No |
| `configMapName` | ConfigMap name for `plugins.yaml`. Defaults to `{ufmFullname}-plugins`. | No |
| `rdma.resourceName` | RDMA resource name (e.g. `rdma/hca_shared`). Only used when `rdma.resourceCount` is not `"0"`. | No |
| `rdma.resourceCount` | Number of RDMA resources per plugin pod; default `"0"`. Set to `"1"` (or more) when the plugin uses InfiniBand. | No |
| `plugins.defaultResources` | Default `requests`/`limits` when a plugin does not set `resources`. | No |
| `plugins.items` | List of plugin definitions (see below). | Yes (can be empty) |
| `affinity` | Optional pod affinity (e.g. to run on same node as UFM or in specific node pools). See Kubernetes affinity docs. | No |
| `tolerations` | Pod tolerations. | No |
| `nodeSelector` | Pod node selector. | No |
| `imagePullSecrets` | Image pull secrets. | No |

### 4. Define each plugin in `plugins.items`

Each item must have `name`, `image`, and `tag`; entries missing any of these are skipped (no Deployment or `plugins.yaml` entry is created).

Each item can have:

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Plugin name (used in paths and labels; use underscores, e.g. `my_plugin`). | Yes |
| `image` | Container image repository (no tag). | Yes |
| `tag` | Image tag. | Yes |
| `imagePullPolicy` | e.g. `IfNotPresent` or `Always`. | No (default: IfNotPresent) |
| `port` | Main TCP port the plugin listens on: written to `plugins.yaml` so UFM can reach the plugin. If you add a Service or Ingress, use this as the target container port. If the plugin exposes multiple ports, set this to the one UFM uses. | No |
| `host` | Host written into `plugins.yaml` for this plugin; UFM uses it with `port` to reach the plugin. Default `127.0.0.1` (plugin on same host as UFM). Override for remote or in-cluster hostnames. | No |
| `resources` | `requests`/`limits` for this plugin; overrides `plugins.defaultResources`. **Recommended**: set `resources.requests` (and optionally `limits`) per plugin so the cluster can schedule and limit pods correctly. | No |
| `livenessProbe` | Full [liveness probe](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes) spec (e.g. `exec`, `httpGet`, `tcpSocket`). You configure it; the chart does not set a default. | No |
| `readinessProbe` | Full [readiness probe](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes) spec. You configure it; the chart does not set a default. | No |

Example for a plugin with custom resources and user-defined probes:

```yaml
plugins:
  items:
    - name: my_plugin
      image: my-registry/my-ufm-plugin
      tag: "1.0.0"
      port: 8401
      resources:
        requests:
          memory: "256Mi"
          cpu: "100m"
        limits:
          memory: "512Mi"
          cpu: "500m"
      # Probes are your choice; no defaults from the chart.
      livenessProbe:
        httpGet:
          path: /health
          port: 8401
        initialDelaySeconds: 60
        periodSeconds: 30
      readinessProbe:
        httpGet:
          path: /health
          port: 8401
        initialDelaySeconds: 10
        periodSeconds: 10
```

### 5. What the chart generates

- **Deployment per plugin**: One Deployment per entry in `plugins.items`, with:
  - Init container that runs `/init.sh -ufm_version ${UFM_VERSION}`; `UFM_VERSION` is read from the ConfigMap `{ufmFullname}-config` (see Prerequisites). Mounts plugin config/log dirs from the shared PVC.
  - Main container with the same mounts, optional `PLUGIN_PORT`, and RDMA resources when configured.
  - Optional placement control via `affinity`, `nodeSelector`, and `tolerations` (no default affinity; set `affinity` if you want e.g. same node as UFM).
  - Liveness and readiness probes only if you set `livenessProbe` and/or `readinessProbe` per plugin (no defaults).
- **ConfigMap `plugins.yaml`**: One ConfigMap (name from `configMapName` / default `{ufmFullname}-plugins`) containing a `plugins.yaml` consumed by UFM (list of name, host, port, tag).

### 6. Plugin image expectations

Your plugin image should:

- Provide **`/init.sh`** that accepts `-ufm_version <version>` and initializes config under `/config` and logs under `/log` (these are mounted from the shared PVC subpaths `conf/plugins/<name>` and `log/plugins/<name>`).
- For health checks, configure `livenessProbe` and/or `readinessProbe` per plugin (e.g. `httpGet` or `tcpSocket`);

### 7. RDMA / InfiniBand

The default `rdma.resourceCount` is `"0"` (no RDMA). Set it to `"1"` (or more) when your plugin uses InfiniBand and the cluster provides the RDMA device plugin. If your cluster uses a different RDMA resource name, set `rdma.resourceName` accordingly.

### 8. Validation and CI

- Run a dry-run with your values:
  ```bash
  helm template my-ufm-plugin . -f my-values.yaml -n ufm-enterprise
  ```
- Lint the chart:
  ```bash
  helm lint . -f ci-values.yaml
  ```
- Use `ci-values.yaml` in CI; it provides minimal required values (including `rdma`) so that `helm template` and `helm lint` succeed. CI also runs `helm template` with `ci-values-empty-plugins.yaml` (no plugins) and with `examples/log-streamer-config.yaml` to validate those scenarios.

### 9. CI example: building the chart as part of CI

To lint, template, and package the chart in your pipeline (e.g. Jenkins or GitHub Actions):

```bash
helm lint ufm-plugin-helm-template -f ufm-plugin-helm-template/ci-values.yaml
helm template ufm-plugin-test ufm-plugin-helm-template -f ufm-plugin-helm-template/ci-values.yaml -n ufm-enterprise
helm package ufm-plugin-helm-template
```

This repo’s own CI (see `.ci/ci_matrix.yaml` and `.ci/do_create_ufm_plugin_helm_chart.sh`) runs these steps and publishes the packaged chart; you can use it as a reference for your plugin’s CI.

## Examples

- **examples/log-streamer-config.yaml** – Sample values for the log_streamer plugin. To create only the `plugins.yaml` ConfigMap with no plugins (e.g. for UFM to mount before adding plugins later), use `plugins.items: []` in your values.

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
3. Add your plugin under `plugins.items` with at least `name`, `image`, and `tag`; set `port` and `rdma` as needed, and `livenessProbe`/`readinessProbe` if you want health checks.
4. Ensure your image has `/init.sh`.
5. Install with `helm install` (use `-f my-values.yaml` to override or use a separate values file).
