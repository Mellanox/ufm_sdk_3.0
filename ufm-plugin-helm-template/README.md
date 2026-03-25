# UFM Plugins Helm Chart

Generic Helm chart for deploying UFM plugins. You **install the chart once** and pass a **plugins definition file** (a Helm values file) that lists the plugins you want to deploy. Plugins are defined as a **map keyed by plugin name**, so you can upgrade or reconfigure a single plugin without restating the entire plugin list.

## Prerequisites

- **UFM Enterprise** must already be installed in the cluster (this chart does not install UFM).
- **Namespace**: Can be **discovered at install time** when `namespaceSearchList` is set and Helm has cluster access (chart looks up ConfigMap `{ufmFullname}-config` in those namespaces only). Otherwise set `namespace` in your file or rely on default **`ufm-enterprise`**.
- **`ufmFullname`**: Set in your plugins file to match your UFM release (e.g. `ufm-<release-name>`). Required.
- **Shared PVC**: This chart uses the same PVC as UFM and mounts subpaths `conf/plugins/<plugin_name>` and `log/plugins/<plugin_name>`. Default claim name is `{ufmFullname}-files`; set `existingClaim` in your file if UFM uses a different PVC name.
- **UFM ConfigMap**: A ConfigMap named `{ufmFullname}-config` with key `UFM_VERSION` must exist (typically from the UFM Enterprise chart). If missing, plugin pods will not start.
- **RDMA** (if needed): If your plugins use InfiniBand, set `rdma.resourceCount` and ensure the cluster has the RDMA device plugin. Some plugins may need the NVIDIA Network Operator.

## Quick Start

1. **Create a plugins definition file** (e.g. `my-plugins.yaml`):

   ```yaml
   ufmFullname: "ufm-ufm-enterprise"

   plugins:
     entries:
       my_plugin:
         image: my-registry/my-ufm-plugin
         tag: "1.0.0"
         port: 8401
         healthEndpoint: /health
         healthPort: 8401
       another_plugin:
         image: my-registry/another-plugin
         tag: "1.0.0"
   ```

2. **Install the chart**:

   ```bash
   helm install ufm-plugins ./ufm-plugin-helm-template -f my-plugins.yaml -n ufm-enterprise
   ```

3. **To upgrade a single plugin** without touching the others, create a file with only that plugin's entry and use `--reuse-values`:

   ```bash
   helm upgrade ufm-plugins ./ufm-plugin-helm-template --reuse-values -f my-plugin-upgrade.yaml -n ufm-enterprise
   ```

   Where `my-plugin-upgrade.yaml` contains only:

   ```yaml
   plugins:
     entries:
       my_plugin:
         image: my-registry/my-ufm-plugin
         tag: "2.0.0"
         port: 8401
         healthEndpoint: /health
         healthPort: 8401
   ```

   Helm merges the map by key — `my_plugin` is updated, `another_plugin` stays as-is. No restart, no config change for untouched plugins.

4. **To disable a plugin** without removing its configuration, set `enabled: false`:

   ```yaml
   plugins:
     entries:
       my_plugin:
         enabled: false
         image: my-registry/my-ufm-plugin
         tag: "2.0.0"
   ```

5. **Full reconcile** — when you want to set the exact desired state of all plugins (e.g. after a chart version upgrade), use `--reset-values` with all plugin files:

   ```bash
   helm upgrade ufm-plugins ./ufm-plugin-helm-template --reset-values -f base.yaml -f plugins/my-plugin.yaml -f plugins/another-plugin.yaml -n ufm-enterprise
   ```

## Plugins definition file

The file you pass with `-f` is a standard Helm values file. It must define:

- **`ufmFullname`** – UFM release full name (e.g. `ufm-ufm-enterprise`).
- **`plugins.entries`** – Map of plugins to deploy, keyed by plugin name. Each entry must have `image` and `tag`; all other fields are optional.

You can override any chart value in this file (namespace, existingClaim, rdma, affinity, etc.). See the values reference below.

### Values reference (what you can set in your plugins file)

| Value | Description | Required |
|-------|-------------|----------|
| `ufmFullname` | Full name of the UFM Enterprise release. Must match the release name used when you installed UFM. | Yes |
| `namespace` | Kubernetes namespace for chart resources. When `namespaceSearchList` is set and Helm has cluster access, the chart discovers it by looking up ConfigMap `{ufmFullname}-config` in each listed namespace. Otherwise falls back to this value, then **`ufm-enterprise`**. | No |
| `namespaceSearchList` | Optional list of namespaces to search for `{ufmFullname}-config` at install time (e.g. `["ufm-enterprise"]`). Only requires **get ConfigMap** in those namespaces. Omit or set to `[]` to skip discovery. | No |
| `existingClaim` | PVC claim name for UFM files. Defaults to `{ufmFullname}-files`. | No |
| `configMapName` | ConfigMap name for `plugins.yaml`. Defaults to `{ufmFullname}-plugins`. | No |
| `rdma.resourceName` | RDMA resource name (e.g. `rdma/hca_shared`). Only used when `rdma.resourceCount` is not `"0"`. | No |
| `rdma.resourceCount` | Number of RDMA resources per plugin pod; default `"0"`. Set to `"1"` when the plugin uses InfiniBand. | No |
| `watchdog.enabled` | Enable watchdog monitoring for plugin pods. Default `true`. | No |
| `watchdog.restartThreshold` | Chart-level default for max restarts before marking a node unhealthy. Default `3`. Per-plugin override available. | No |
| `watchdog.timeWindowSeconds` | Chart-level default time window for counting restarts. Default `120`. Per-plugin override available. | No |
| `plugins.defaultResources` | Default `requests`/`limits` when a plugin does not set `resources`. | No |
| `plugins.entries` | Map of plugin definitions keyed by plugin name (see below). | Yes (can be empty `{}`) |
| `podSecurityContext` | Optional pod-level securityContext (e.g. `runAsNonRoot: true`). | No |
| `affinity` | Optional pod affinity. | No |
| `tolerations` | Pod tolerations. | No |
| `nodeSelector` | Pod node selector. | No |
| `imagePullSecrets` | Image pull secrets. | No |

### Plugin entry fields (`plugins.entries.<name>`)

Each plugin is a map entry keyed by its canonical name (use underscores, e.g. `log_streamer`). The key becomes the plugin name in all generated resources. Required fields are `image` and `tag`; entries missing either are skipped.

| Field | Description | Required |
|-------|-------------|----------|
| `enabled` | Set to `false` to skip this plugin (removes Deployment and `plugins.yaml` entry). Default `true`. | No |
| `image` | Container image repository (no tag). | Yes |
| `tag` | Image tag. | Yes |
| `imagePullPolicy` | e.g. `IfNotPresent` or `Always`. | No (default: IfNotPresent) |
| `port` | Main TCP port the plugin listens on. Written to `plugins.yaml` so UFM can reach the plugin. When set (and no `healthEndpoint`), the default liveness probe uses native tcpSocket on this port. | No |
| `ports` | Additional container ports (list of integers). | No |
| `healthEndpoint` | HTTP path for the default liveness probe (e.g. `/health`). When set, the chart uses native httpGet on this path. | No |
| `healthPort` | Port for the default liveness httpGet probe; defaults to `port`. | No |
| `host` | Host written into `plugins.yaml`. Default: in-cluster DNS `{ufmFullname}-plugin-{name}.{namespace}.svc.cluster.local`. | No |
| `rdma` | Per-plugin RDMA override: `{ resourceName, resourceCount }`. | No |
| `resources` | `requests`/`limits` for this plugin; overrides `plugins.defaultResources`. | No |
| `startupProbe` | Full startup probe spec. | No |
| `livenessProbe` | Full liveness probe spec. Overrides the chart default (httpGet or tcpSocket). | No |
| `disableLivenessProbe` | Set to `true` to omit the liveness probe entirely. | No |
| `readinessProbe` | Full readiness probe spec. No default. | No |
| `mountHealthScripts` | Set to `true` to mount the chart's health-check script at `/health-scripts`. | No (default: false) |
| `extraCapabilities` | Additional Linux capabilities (e.g. `["SYS_PTRACE"]`). | No |
| `env` | Extra environment variables for the main container. | No |
| `volumes` | Extra volumes for the pod. | No |
| `volumeMounts` | Extra volumeMounts for the main container. | No |
| `runInitContainer` | When `false`, the init container is omitted. Default `true`. | No |
| `strategy` | Deployment strategy: `Recreate` (default) or `RollingUpdate`. `Recreate` terminates the old pod before starting the new one — safer for single-replica plugins that share a PVC or lock resources. Set to `RollingUpdate` if you need zero-downtime upgrades. | No (default: Recreate) |
| `watchdog` | Per-plugin watchdog override: `{ enabled, restartThreshold, timeWindowSeconds }`. | No |

## Incremental upgrades

The map-based `plugins.entries` model lets you upgrade a single plugin without restating every other plugin.

### How it works

Helm merges maps by key. When you run `helm upgrade --reuse-values -f single-plugin.yaml`, Helm:

1. Loads the stored values from the previous release (all plugins).
2. Deep-merges the new file on top — only the plugin key you specified is updated.
3. Re-renders templates — only the changed plugin's Deployment spec differs, so only that pod restarts.

### Recommended workflow

**Per-plugin files** — keep one values file per plugin (e.g. `plugins/log-streamer.yaml`, `plugins/telemetry.yaml`) plus a shared `base.yaml` with `ufmFullname` and global settings.

**Initial install** (all plugins):

```bash
helm install ufm-plugins ./ufm-plugin-helm-template -f base.yaml -f plugins/log-streamer.yaml -f plugins/telemetry.yaml -n ufm-enterprise
```

**Upgrade one plugin** (only that plugin restarts):

```bash
helm upgrade ufm-plugins ./ufm-plugin-helm-template --reuse-values -f plugins/log-streamer.yaml -n ufm-enterprise
```

**Disable one plugin**:

```bash
helm upgrade ufm-plugins ./ufm-plugin-helm-template --reuse-values --set plugins.entries.log_streamer.enabled=false -n ufm-enterprise
```

**Full reconcile** (set exact desired state, e.g. after chart version upgrade):

```bash
helm upgrade ufm-plugins ./ufm-plugin-helm-template --reset-values -f base.yaml -f plugins/log-streamer.yaml -f plugins/telemetry.yaml -n ufm-enterprise
```

### When to use `--reuse-values` vs `--reset-values`

| Scenario | Flag | Why |
|----------|------|-----|
| Upgrade one plugin's image/config | `--reuse-values` | Keeps all other plugins as-is |
| Add a new plugin to an existing release | `--reuse-values` | Merges the new entry into existing |
| Disable a single plugin | `--reuse-values` | Only changes that plugin's `enabled` flag |
| Upgrade the chart version itself | `--reset-values` | Ensures new chart defaults apply cleanly |
| Full reconcile of all plugins | `--reset-values` | Sets the authoritative desired state |

## Watchdog integration

The chart supports the UFM watchdog operator. When `watchdog.enabled` is `true` (default), each plugin pod gets:

- Label `ufm.nvidia.com/watchdog-scope: plugin` for discovery.
- Annotations for restart threshold and time window.
- Node-exclusion rule to avoid nodes marked unhealthy for that specific plugin.

Per-plugin overrides:

```yaml
plugins:
  entries:
    log_streamer:
      image: my-image
      tag: "1.0.0"
      watchdog:
        enabled: true
        restartThreshold: 5
        timeWindowSeconds: 180
```

To disable watchdog for all plugins: `watchdog.enabled: false`. For a single plugin: set `watchdog: { enabled: false }` on that entry.

## What the chart generates
- **ClusterIP Service per plugin** (when `port` and/or `ports` is set): name `{ufmFullname}-plugin-{k8s-name}`, selector matches the Deployment, ports align with container ports so in-cluster DNS matches `plugins.yaml` defaults.
- **Deployment per plugin**: One Deployment per entry in `plugins.items`, with:
  - Init container that runs `/init.sh -ufm_version ${UFM_VERSION}`; `UFM_VERSION` is read from the ConfigMap `{ufmFullname}-config` (see Prerequisites). Mounts plugin config/log dirs from the shared PVC.
  - Main container with the same mounts, optional `PLUGIN_PORT` and `HEALTH_ENDPOINT`/`HEALTH_PORT` (for the default liveness script), and RDMA resources when configured.
  - Optional placement control via `affinity`, `nodeSelector`, and `tolerations` (no default affinity; set `affinity` if you want e.g. same node as UFM).
  - **Liveness**: default is **native Kubernetes**—**httpGet** when `healthEndpoint` is set, **tcpSocket** when `port` is set; otherwise no default. Override with `livenessProbe`.
  - **Readiness**: no default; set `readinessProbe` if you want a readiness probe.
- **ConfigMap `plugins.yaml`**: One ConfigMap (name from `configMapName` / default `{ufmFullname}-plugins`) containing a `plugins.yaml` consumed by UFM (list of name, host, port, tag). Default host per plugin is the in-cluster DNS name; a matching **Service** is created when ports are defined. Override `host` per plugin if needed (e.g. Ingress).
- **Health scripts ConfigMap** (optional): Emitted only when at least one plugin has `mountHealthScripts: true`. Contains `health-check.sh`; when mounted, it is at `/health-scripts`. Default liveness uses httpGet/tcpSocket and does not mount this; set `mountHealthScripts: true` only if you use a custom `livenessProbe` with `exec` and that script.

- **Deployment per plugin**: One Deployment per enabled entry in `plugins.entries` (sorted alphabetically for stable output). Each Deployment uses `Recreate` strategy by default (old pod is terminated before new pod starts), which is safer for single-replica plugins sharing a PVC. Override per plugin with `strategy: RollingUpdate` if you need zero-downtime.
- **ConfigMap `plugins.yaml`**: One ConfigMap listing all enabled plugins for UFM (name, host, port, tag).
- **Health scripts ConfigMap** (optional): Emitted only when at least one plugin has `mountHealthScripts: true`. Pods that mount it get a `checksum/health-scripts` annotation so they automatically restart when the script changes during a chart upgrade.

## Plugin image expectations

Your plugin image should:

- Provide **`/init.sh`** that accepts `-ufm_version <version>` and initializes config under `/config` and logs under `/log`.
- Default liveness uses native Kubernetes httpGet (when `healthEndpoint` is set) or tcpSocket (when `port` is set). Override with `livenessProbe` or set `disableLivenessProbe: true`.

## RDMA / InfiniBand

Default `rdma.resourceCount` is `"0"`. Set to `"1"` when your plugin uses InfiniBand. Override per plugin with `rdma: { resourceName, resourceCount }`.

## Input validation (values.schema.json)

The chart includes a values schema so `helm install/upgrade/template/lint` validate your values. Required: `ufmFullname`, `plugins.entries`, and for each entry `image` and `tag`.

## Examples

- **`examples/log-streamer-config.yaml`** — Single plugin deployment.
- **`examples/two-plugins.yaml`** — Two plugins deployed together.
- **`examples/upgrade-one-plugin.yaml`** — Upgrade only one plugin using `--reuse-values`.

```bash
# Deploy two plugins
helm install ufm-plugins ./ufm-plugin-helm-template -f examples/two-plugins.yaml -n ufm-enterprise

# Later, upgrade only log_streamer
helm upgrade ufm-plugins ./ufm-plugin-helm-template --reuse-values -f examples/upgrade-one-plugin.yaml -n ufm-enterprise
```

## Validation and CI

```bash
# Dry-run with your values
helm template my-ufm-plugin . -f my-values.yaml -n ufm-enterprise

# Lint the chart
helm lint . -f ci-values.yaml
```

CI runs `helm lint` and `helm template` with all `ci-values*.yaml` files and all example files.

## Packaging and distributing

```bash
helm package .
helm install ufm-plugins ufm-plugins-0.1.0.tgz -f my-plugins.yaml -n ufm-enterprise
helm upgrade ufm-plugins ufm-plugins-0.1.0.tgz --reuse-values -f upgrade-one.yaml -n ufm-enterprise
```

## Summary

1. **Create plugin definition files** (YAML) with `ufmFullname` and `plugins.entries` (each plugin keyed by name with `image`, `tag`; add `port`, `healthEndpoint`, `rdma`, probes as needed).
2. **Install** with `helm install ufm-plugins <chart> -f <your-files> -n <namespace>`.
3. **Upgrade one plugin** with `helm upgrade ufm-plugins <chart> --reuse-values -f <single-plugin-file> -n <namespace>`.
4. **Disable a plugin** with `enabled: false` and `--reuse-values`.
5. **Full reconcile** with `--reset-values` and all plugin files.
