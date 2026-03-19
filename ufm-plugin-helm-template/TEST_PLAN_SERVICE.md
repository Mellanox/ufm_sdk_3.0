# Test plan: plugin ClusterIP Service

Simple checklist for validating the chart’s **Service** objects (`templates/plugin-service.yaml`): stable DNS for UFM → plugin traffic after `hostNetwork` removal.

---

## 1. Scope

| In scope | Out of scope |
|----------|----------------|
| Service exists when `port` and/or `ports` is set | UFM application logic, Apache config inside UFM images |
| Name matches default `host` in `plugins.yaml` ConfigMap | Ingress / TLS / external LB (unless you add them later) |
| Selector matches plugin Deployment labels | Performance / load testing |

---

## 2. Prerequisites

- Helm 3.x
- For **cluster** sections: a namespace, `kubectl` access, and (for full checks) UFM + plugin chart installed or at least the plugin chart applied with valid PVC/ConfigMap refs—or a throwaway namespace with mocked resources if you only test Service wiring.

---

## 3. Base: static checks (no cluster)

**Goal:** Rendered YAML is consistent and valid.

| # | Step | Expected |
|---|------|------------|
| B1 | `helm lint . -f ci-values.yaml` | Exit 0 |
| B2 | `helm lint . -f ci-values-service.yaml` | Exit 0 |
| B3 | `helm template test . -f ci-values-service.yaml -n ufm-enterprise` | Output contains exactly one `kind: Service` |
| B4 | In that output, find `plugins.yaml` → `host:` line | Value is `{ufmFullname}-plugin-{k8s-name}.{namespace}.svc.cluster.local` (e.g. `ufm-ufm-enterprise-plugin-ci-test-plugin.ufm-enterprise.svc.cluster.local`) |
| B5 | Same render: Service `metadata.name` | Equals the **first segment** of that FQDN (before the first `.`) |
| B6 | Service `spec.selector.app` | Equals Deployment `spec.selector.matchLabels.app` for that plugin |

**Automation:** GitHub Actions (`.github/workflows/helm-template-ci.yml`) covers B3–B6 for `ci-values-service.yaml`.

---

## 4. Positive: cluster behavior

**Goal:** Kubernetes actually routes traffic to the plugin pod.

| # | Step | Expected |
|---|------|------------|
| P1 | `kubectl get svc -n <ns>` | Service `{ufmFullname}-plugin-<k8s-name>` exists, `CLUSTER-IP` assigned, `PORT(S)` list matches chart |
| P2 | `kubectl get endpoints -n <ns> <service-name>` | At least one ready endpoint when the pod is Running and Ready |
| P3 | Run a short-lived client pod in the **same** namespace | `curl -sS -o /dev/null -w '%{http_code}\n' --connect-timeout 5 http://<service-name>:<port>/` returns a defined HTTP code (e.g. 200/401/404—not connection refused) *if* the plugin listens on HTTP |
| P4 | `kubectl port-forward svc/<service-name> <local>:<port> -n <ns>` then `curl` to `127.0.0.1:<local>` | Same as P3 (proves Service + kube-proxy path) |

*If the plugin only speaks TCP and not HTTP, replace P3/P4 with `nc -zv <service-name> <port>` or a raw TCP check.*

---

## 5. Negative flows

**Goal:** Failures are understandable and match Kubernetes behavior (not necessarily “chart bugs”).

| # | Scenario | How to test | Expected |
|---|------------|-------------|----------|
| N1 | **No Service when no ports** | `helm template` with `ci-values-empty-plugins.yaml` or a plugin with **no** `port` / `ports` | No `kind: Service` for that plugin (nothing to expose) |
| N2 | **Wrong short DNS from another namespace** | From a pod in namespace `A`, `curl http://<svc>:<port>` while Service is in namespace `B` | Fails (name does not resolve or connects to wrong object). Fix: use FQDN `<svc>.<B>.svc.cluster.local` |
| N3 | **Pod not Ready** | Scale to broken image or break readiness so endpoints are empty | `kubectl get endpoints` shows no ready subsets; client gets connection refused or timeout |
| N4 | **Plugin listens on wrong interface** | App binds to `127.0.0.1` only inside the pod | Connection to Service IP fails even if pod is Running—**application must listen on `0.0.0.0` or pod IP** |
| N5 | **Custom `host` in values without matching Service** | Set `host: my-custom.example.com` in `plugins.yaml` via values but **no** external DNS/Ingress | UFM may try unreachable host; **operational** issue—document that custom `host` requires you to provide routing (Ingress/DNS) yourself |
| N6 | **Port mismatch** | Set `port: 8080` in values but container actually listens on 9090 | Probes/endpoints may fail; Service targets wrong `targetPort`—catch with failing readiness or manual `kubectl exec` |

---

## 6. Exit criteria (release / merge)

- [ ] B1–B6 pass locally or in CI.
- [ ] At least one cluster run of **P1 + P2** on a representative environment.
- [ ] If HTTP plugins are supported, **P3** or **P4** once per release on a smoke cluster.
- [ ] Team aware of **N4** (bind address) and **N2** (cross-namespace DNS) for support.

---

## 7. References

- Chart templates: `templates/plugin-service.yaml`, `templates/plugin-configmap.yaml`, `templates/plugin-deployment.yaml`
- CI values: `ci-values.yaml`, `ci-values-service.yaml`, `ci-values-empty-plugins.yaml`
