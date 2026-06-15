# ufm-state-mirror

The **StateMirror** sidecar makes UFM's runtime state durable in Redis/Valkey
when UFM runs on Kubernetes with ephemeral (`emptyDir`) pod storage. It is the
implementation of the Redis-backed storage mode described in the
`HLD_redis_sidecar_storage_mode` HLD (kept in the UFM repo).

This is a **standalone, consumer-agnostic** component: it ships only the
mirroring engine. The list of files to mirror (the *classifier*) is supplied at
runtime by each consumer (UFM, UFM HA) via a ConfigMap mounted at
`CLASSIFIER_PATH` — see `examples/classifier-example.yaml` for the schema. The
authoritative, file-set-reconciled classifier lives in the consumer repo.

The same image runs in two roles inside the UFM pod:

| Role | Command | When | Purpose |
|------|---------|------|---------|
| restore | `python -m state_mirror.restore` | init container | Materialize Redis → `emptyDir` **before** UFM starts; fails closed on incomplete state. |
| mirror | `python -m state_mirror.mirror` | native sidecar | Continuously mirror `emptyDir` → Redis as files change. |

## How it works

- **Classifier** (supplied by the consumer at `CLASSIFIER_PATH`; see
  `examples/classifier-example.yaml`): the single source of truth for which
  files are durable and how (handler, Redis key, change trigger, first-install
  baseline). Validated and fails closed at load.
- **Handlers**: `blob`, `atomic_blob`, `directory` (key-per-child fan-out), and
  `sqlite`. SQLite DBs are made durable with consistent online-backup snapshots
  (snapshot-only — the whole DB is shipped when it changes, no WAL-shipping),
  polled by a WAL-aware change fingerprint so live writes are detected whether
  the DB is in rollback-journal or WAL mode. The handler never changes a DB's
  journal mode; restore `PRAGMA integrity_check`s the DB, failing closed on
  corruption.
- **Wire format**: each file is two Redis keys — `<key>` (raw bytes) and
  `<key>:meta` (JSON: content hash, size, versions) — written in one
  transaction and verified on restore (hash/size/format), failing closed.
- **Change detection**: event-driven via [`watchdog`](https://pythonhosted.org/watchdog/);
  a periodic full scan reconciles anything events miss.
- **Redis discovery**: Sentinel-aware (`redis_client.master_for`) so writes
  follow failovers automatically.
- **Storage backends** (pluggable `Store`, install-wide — HLD 5.2.3): exactly
  one backend is selected at install time via the `STATE_MIRROR_BACKEND` env var
  and used for every entry — there is no per-file routing. `configmap` is the
  default; `redis` is the alternative. The same body+meta wire contract and
  fail-closed verification apply to both. The `configmap` backend stores each
  key as one Kubernetes ConfigMap (`binaryData` body + a `meta` field) and
  enforces the ~1 MiB etcd object cap fail-closed, so it requires the consumer
  to grant the pod's ServiceAccount ConfigMap RBAC in its namespace (HLD 8.7).
  Choose `redis` (BYO Redis/Valkey) when state exceeds the ConfigMap cap or is
  high-churn; a Redis install never loads the kubernetes client.

## Resilience model

- A Redis outage **degrades mirroring but never crashes the sidecar** — crashing
  would lose the `emptyDir`. Redis health is surfaced via metrics/alerts, not by
  failing the liveness probe.
- `restore` exits non-zero on any failure so UFM never boots on partial state.

## HTTP endpoints (port 9180)

| Path | Meaning |
|------|---------|
| `/ready` | 200 once restore/initial-scan done and the watcher is armed (gates UFM startup). |
| `/healthz` | Liveness of the mirror loop. Deliberately does **not** fail on Redis-unreachable. |
| `/metrics` | Prometheus text exposition (below). |

## Metrics

- `state_mirror_ready` — 1 when ready.
- `state_mirror_backend_reachable` — 1 if the storage backend was reachable on
  the last op.
- `state_mirror_watchdog_active` — 1 if the watchdog observer is running.
- `state_mirror_last_write_timestamp_seconds` — last successful store write.
- `state_mirror_dirty_queue_depth`, `state_mirror_pending_deletes` — backlog.
- `state_mirror_mirror_ops_total`, `state_mirror_full_scans_total`,
  `state_mirror_events_total` — counters.
- `state_mirror_dropped_events_total` — observed deletes dropped from the bounded
  queue under the D2 drop policy (oldest dropped first during a long outage).
  A dropped delete is **not** propagated: the file stays in the backend and is
  re-materialized on the next restore (the backend wins). A persistently rising
  value means delete durability is lagging (HLD 8.2).
- `state_mirror_unexpected_delete_total` — files gone from `emptyDir` but still
  present in the backend, detected at full scan **without** an observed delete
  (unobserved drift, HLD 5.3.7/5.3.9). The backend object is kept (it wins on
  ambiguity; the next restore re-materializes the file); this counter only makes
  the drift visible. Counted once per drift onset, not per scan.
- `state_mirror_snapshot_duration_seconds{db="..."}` — wall-clock of the last
  SQLite online-backup snapshot per DB (basename label), for snapshot-duration
  headroom under load (HLD 5.3.4 / Phase 5 / R2).
- `state_mirror_backend_errors_total{reason="..."}` — backend op errors by
  classified reason. The label set spans both backends: Redis reasons (`oom`,
  `noreplicas`, `noauth`, `noperm`, `misconf`, `readonly`, `loading`,
  `response`, `local_io`) and ConfigMap reasons (`forbidden`, `notfound`,
  `conflict`, `toolarge`, `invalid`, `server`), plus shared `conn`, `timeout`,
  `other`. This distinguishes "alive but can't mirror" causes — e.g. missing
  RBAC (`forbidden`) on ConfigMap, or an OOM that a Sentinel failover would
  **not** fix (HLD 8.6.2).

The Helm chart ships an optional `ServiceMonitor` + `PrometheusRule`
(`stateMirror.metrics.*`) that alert on these.

## Configuration (environment)

| Variable | Default | Meaning |
|----------|---------|---------|
| `CLASSIFIER_PATH` | `/etc/state_mirror/state_mirror.yaml` | Classifier file. |
| `UFM_VERSION` | `unknown` | Stamped into metadata. |
| `STATE_MIRROR_METRICS_PORT` | `9180` | HTTP port. |
| `STATE_MIRROR_MAX_QUEUE` | `100000` | Max observed-delete queue; drop-oldest on overflow (dropped deletes fall back to backend-wins, D2/HLD 8.2). |
| `STATE_MIRROR_BACKEND` | `configmap` | Install-wide storage backend: `configmap` (default, etcd-backed) or `redis` (BYO). Invalid values fail closed at startup. |
| `STATE_MIRROR_LOG_LEVEL` | `INFO` | Log level. |
| `STATE_MIRROR_LOG_TO_FILE` | `true` | Also log to `/opt/ufm/files/log/state_mirror.log`. |
| `STATE_MIRROR_LOG_DIR` | `/opt/ufm/files/log` | File log directory. |
| `REDIS_SENTINEL_HOSTS` | _(empty)_ | `host:port,...`; enables Sentinel discovery. |
| `REDIS_MASTER_NAME` | `ufm` | Sentinel master name. |
| `REDIS_HOST` / `REDIS_PORT` | `localhost` / `6379` | Direct (non-Sentinel) endpoint. |
| `REDIS_PASSWORD`, `REDIS_SENTINEL_PASSWORD` | _(none)_ | Auth. |
| `REDIS_USE_TLS`, `REDIS_CA_CERT` | `false` / _(none)_ | TLS. |

## Development

```bash
# from this component directory (ufm-state-mirror/):
pip install -r requirements.txt ruff pytest
python -m pytest -q
ruff format .
ruff check .
```

See `BUILD.md` for the image build and release flow.
