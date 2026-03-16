# UFM Plugins Helm Chart

Generic Helm chart for deploying UFM plugins. You **install the chart once** and pass a **plugins definition file** (a Helm values file) that lists the plugins you want to deploy. No need to copy or customize the chart—just define your plugins in a YAML file and use `-f` when installing or upgrading.

## Prerequisites

- **UFM Enterprise** must already be installed in the cluster (this chart does not install UFM).
- **Namespace**: Can be **discovered at install time** when `namespaceSearchList` is set and Helm has cluster access (chart looks up ConfigMap `{ufmFullname}-config` in those namespaces only). Otherwise set `namespace` in your file or rely on default **`ufm-enterprise`**. 
- **`ufmFullname`**: Set in your plugins file to match your UFM release (e.g. `ufm-<release-name>`). Required.
- **Shared PVC**: This chart uses the same PVC as UFM and mounts subpaths `conf/plugins/<plugin_name>` and `log/plugins/<plugin_name>`. Default claim name is `{ufmFullname}-files`; set `existingClaim` in your file if UFM uses a different PVC name.
- **UFM ConfigMap**: A ConfigMap named `{ufmFullname}-config` with key `UFM_VERSION` must exist (typically from the UFM Enterprise chart). If missing, plugin pods will not start.
- **RDMA** (if needed): If your plugins use InfiniBand, set `rdma.resourceCount` and ensure the cluster has the RDMA device plugin. Some plugins may need the NVIDIA Network Operator.

## Quick Start

1. **Create a plugins definition file** (e.g. `my-plugins.yaml`) with the plugins you want to deploy and UFM connection details:

   ```yaml
   ufmFullname: "ufm-ufm-enterprise"
   # namespace: optional; set or use namespaceSearchList for discovery

   plugins:
     items:
       - name: my_plugin
         image: my-registry/my-ufm-plugin
         tag: "1.0.0"
         port: 8401
         healthEndpoint: /health
         healthPort: 8401
       - name: another_plugin
         image: my-registry/another-plugin
         tag: "1.0.0"
   ```

2. **Install the chart** and pass your file:

   ```bash
   helm install ufm-plugins ./ufm-plugin-helm-template -f my-plugins.yaml -n ufm-enterprise
   ```

   Or from a packaged chart:

   ```bash
   helm install ufm-plugins ufm-plugins-0.0.0.tgz -f my-plugins.yaml -n ufm-enterprise
   ```

3. **To add or change plugins**, edit `my-plugins.yaml` and upgrade:

   ```bash
   helm upgrade ufm-plugins ./ufm-plugin-helm-template -f my-plugins.yaml -n ufm-enterprise
   ```

## Plugins definition file

The file you pass with `-f` is a standard Helm values file. It must define:

- **`ufmFullname`** – UFM release full name (e.g. `ufm-ufm-enterprise`).
- **`plugins.items`** – List of plugins to deploy. Each item must have `name`, `image`, and `tag`; all other fields are optional.

You can override any chart value in this file (namespace, existingClaim, rdma, affinity, etc.). See the values reference below.

### Values reference (what you can set in your plugins file)

| Value | Description | Required |
|-------|-------------|----------|
| `ufmFullname` | Full name of the UFM Enterprise release (used for naming and for the UFM config ConfigMap). Must match the namespace and release name used when you installed UFM. | Yes |
| `namespace` | Kubernetes namespace for chart resources. When `namespaceSearchList` is set and Helm has cluster access, the chart discovers it by looking up ConfigMap `{ufmFullname}-config` in each listed namespace (no cluster-wide permissions). Otherwise falls back to this value, then **`ufm-enterprise`**. | No |
| `namespaceSearchList` | Optional list of namespaces to search for `{ufmFullname}-config` at install time (e.g. `["ufm-enterprise"]`). Only requires **get ConfigMap** in those namespaces. Omit or set to `[]` to skip discovery and use `namespace` / default. | No |
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

### Plugin item fields (`plugins.items[]`)

Each plugin in `plugins.items` must have `name`, `image`, and `tag`; entries missing any of these are skipped. Optional fields:

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Plugin name (used in paths and labels; use underscores, e.g. `my_plugin`). | Yes |
| `image` | Container image repository (no tag). | Yes |
| `tag` | Image tag. | Yes |
| `imagePullPolicy` | e.g. `IfNotPresent` or `Always`. | No (default: IfNotPresent) |
| `port` | Main TCP port the plugin listens on: written to `plugins.yaml` so UFM can reach the plugin. When set (and no `healthEndpoint`), the **default liveness** probe uses native **tcpSocket** on this port. If you add a Service or Ingress, use this as the target container port. | No |
| `healthEndpoint` | HTTP path for the **default liveness** probe (e.g. `/health`). When set, the chart uses native **httpGet** on this path (and `healthPort`/`port`). No bash script—Kubernetes probes only. | No |
| `healthPort` | Port for the default liveness **httpGet** probe; defaults to `port`. Only used when `healthEndpoint` is set. | No |
| `host` | Host written into `plugins.yaml` for this plugin; UFM uses it with `port` to reach the plugin. Default `127.0.0.1` (plugin on same host as UFM). Override for remote or in-cluster hostnames. | No |
| `resources` | `requests`/`limits` for this plugin; overrides `plugins.defaultResources`. **Recommended**: set `resources.requests` (and optionally `limits`) per plugin so the cluster can schedule and limit pods correctly. | No |
| `livenessProbe` | Full [liveness probe](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes) spec. If not set, the chart uses a **default**: **httpGet** when `healthEndpoint` is set, or **tcpSocket** when `port` is set; otherwise no default liveness. Override with your own spec to replace the default. | No |
| `disableLivenessProbe` | Set to `true` to omit the liveness probe entirely (no default probe, no custom probe). | No |
| `readinessProbe` | Full [readiness probe](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes) spec. **No default**; set this if you want a readiness probe (e.g. `httpGet` or `tcpSocket`). | No |
| `extraCapabilities` | List of additional [Linux capabilities](https://kubernetes.io/docs/concepts/security/capabilities/) to add (e.g. `["SYS_PTRACE"]`). When RDMA is enabled, `IPC_LOCK` is always added; use this to add more. | No |
| `env` | List of extra environment variables for the main container (same format as Kubernetes `env`). Appended after the chart’s `PLUGIN_PORT` / `HEALTH_*`. | No |
| `volumes` | List of extra [volumes](https://kubernetes.io/docs/concepts/storage/volumes/) for the pod (same format as Kubernetes `spec.volumes`). | No |
| `volumeMounts` | List of extra [volumeMounts](https://kubernetes.io/docs/concepts/storage/volumes/) for the main container. Use with `volumes` to mount additional volumes. | No |

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
      # Omit livenessProbe to use the chart default (native httpGet on /health)
      healthEndpoint: /health
      healthPort: 8401
      # Readiness has no default; set it if you want the pod to be ready only when the plugin is up
      readinessProbe:
        httpGet:
          path: /health
          port: 8401
        initialDelaySeconds: 10
        periodSeconds: 10
```
To use your own liveness probe instead of the default script, set `livenessProbe` (e.g. `httpGet` or `tcpSocket`).

### 5. What the chart generates

- **Deployment per plugin**: One Deployment per entry in `plugins.items`, with:
  - Init container that runs `/init.sh -ufm_version ${UFM_VERSION}`; `UFM_VERSION` is read from the ConfigMap `{ufmFullname}-config` (see Prerequisites). Mounts plugin config/log dirs from the shared PVC.
  - Main container with the same mounts, optional `PLUGIN_PORT` and `HEALTH_ENDPOINT`/`HEALTH_PORT` (for the default liveness script), and RDMA resources when configured.
  - Optional placement control via `affinity`, `nodeSelector`, and `tolerations` (no default affinity; set `affinity` if you want e.g. same node as UFM).
  - **Liveness**: default is **native Kubernetes**—**httpGet** when `healthEndpoint` is set, **tcpSocket** when `port` is set; otherwise no default. Override with `livenessProbe`.
  - **Readiness**: no default; set `readinessProbe` if you want a readiness probe.
- **ConfigMap `plugins.yaml`**: One ConfigMap (name from `configMapName` / default `{ufmFullname}-plugins`) containing a `plugins.yaml` consumed by UFM (list of name, host, port, tag).
- **Health scripts ConfigMap** (optional): A ConfigMap with `health-check.sh` (source: `scripts/health-check.sh` in the chart), mounted at `/health-scripts`. Not used by the default liveness (which uses httpGet/tcpSocket). Use it only if you set a custom `livenessProbe` with `exec` and the script.

### 6. Plugin image expectations

Your plugin image should:

- Provide **`/init.sh`** that accepts `-ufm_version <version>` and initializes config under `/config` and logs under `/log` (these are mounted from the shared PVC subpaths `conf/plugins/<name>` and `log/plugins/<name>`).
- **Default liveness** uses native Kubernetes **httpGet** (when `healthEndpoint` is set) or **tcpSocket** (when `port` is set); no script or `/bin/sh` required. Override with `livenessProbe` or set `disableLivenessProbe: true` to omit. **Readiness** has no default; set `readinessProbe` if needed. The chart also ships `scripts/health-check.sh` (included in a ConfigMap at `/health-scripts`) for optional use in custom exec probes.

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

### 9. CI example: building and publishing the chart

To lint, template, and package the generic chart in your pipeline:

```bash
helm lint ufm-plugin-helm-template -f ufm-plugin-helm-template/ci-values.yaml
helm template ufm-plugins ufm-plugin-helm-template -f ufm-plugin-helm-template/ci-values.yaml -n ufm-enterprise
helm package ufm-plugin-helm-template
```

This repo’s CI (see `.ci/ci_matrix.yaml` and `.ci/do_create_ufm_plugin_helm_chart.sh`) builds and publishes the chart; consumers install it and pass their own plugins file with `-f`.

## Examples

- **examples/log-streamer-config.yaml** – Example plugins definition file for the log_streamer plugin. Use as reference: `helm install ufm-plugins . -f examples/log-streamer-config.yaml -n ufm-enterprise`.
- To deploy no plugins (only the `plugins.yaml` ConfigMap for UFM to mount), use a file with `plugins.items: []`.

## Packaging and distributing

The chart is packaged and published for reuse. Users install it once and always pass their plugins file with `-f`:

```bash
helm package .
helm install ufm-plugins ufm-plugins-0.0.0.tgz -f my-plugins.yaml -n ufm-enterprise
helm upgrade ufm-plugins ufm-plugins-0.0.0.tgz -f my-plugins.yaml -n ufm-enterprise
```

## Summary

1. **Create a plugins definition file** (YAML) with `ufmFullname` and `plugins.items` (each plugin: `name`, `image`, `tag`; add `port`, `healthEndpoint`, `rdma`, probes as needed).
2. **Install** with `helm install ufm-plugins <chart> -f <your-file> -n <namespace>`.
3. **To add or change plugins**, edit your file and run `helm upgrade ufm-plugins <chart> -f <your-file> -n <namespace>`.
4. Plugin images must provide `/init.sh`. Set `healthEndpoint`/`port` for the default liveness (native httpGet/tcpSocket), or define `livenessProbe` and `readinessProbe` in your file.
