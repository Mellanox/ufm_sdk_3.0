---
name: run-ufm-simulator
description: Start, validate, and use the NVIDIA UFM simulator container for plugin development and demos. Use when the user asks to run UFM in simulator mode, prepare a UFM simulator host, validate UFM Web UI or REST on a simulator, or deploy and test a UFM plugin on the simulator.
---

# Run UFM Simulator

## Overview

This is a Markdown-only playbook for running UFM in simulator mode. It intentionally has no helper scripts or bundled code. Use it to prepare a simulator host, start the all-in-one UFM simulator container, verify UFM Web UI and REST, and provide a safe target for UFM plugin or UFM APIs validation.

Prefer the simulator for blog demos, AI-generated plugin validation, and repeatable development workflows where a physical fabric is not required.

## Trigger Prompts

Use this skill for prompts like:

- `Run UFM on simulator`
- `Start UFM simulator on <host>`
- `Deploy latest UFM GA in simulator mode`
- `Validate UFM Web UI on simulator`
- `Deploy plugin on UFM simulator`
- `Use default topology` or `Use topology <topology_file>`

## Workflow

1. Resolve the simulator target.
   - Identify the host, SSH user, simulator image, and topology file.
   - Use the verified Jenkins `.db_csv` topology when the user does not provide one: `/auto/mswg/release/ufm/topologies/xdr_msft_extended_x2/ibdiagnet2.db_csv`.
   - Resolve the simulator image using the image lookup rules below.
   - Do not store user passwords or tokens in generated files.

2. Prepare the simulator workspace on the target host.
   - Use `/tmp/ufm-docker-conf` as the verified automation workspace. Use `/opt/ufm-ibmgtsim` only when reproducing the older blog/manual setup or when the user requests that path.
   - Create the workspace directory.
   - Copy or download the topology file into the workspace.
   - If the topology is a `.db_csv` file, copy it to `ibdiagnet2.db_csv` in the workspace regardless of its original name. UFM Fabric Analysis inside the simulator expects `/mnt/air/ibdiagnet2.db_csv`.
   - If the topology is a `.topo` file, keep the topology file name unchanged.
   - Write `ibmgtsim.conf` into the workspace.

3. Configure `ibmgtsim.conf`.
   - Set `IBMGTSIM_TOPOLOGY` to the topology path as seen inside the container.
   - For `.db_csv`, always use `IBMGTSIM_TOPOLOGY=/mnt/air/ibdiagnet2.db_csv`.
   - For `.topo`, use the copied file name, for example `/mnt/air/IS1-16.topo` or `/mnt/air/BM.2.topo`.
   - Set `IBMGTSIM_SERVER=<hostname>:6000`.
   - Set `TELEMETRY_ENDPOINTS=telemetry` unless the user explicitly requests `endpoints`.
   - Changing `TELEMETRY_ENDPOINTS` after startup requires a full simulator stop and start, not only editing `ibmgtsim.conf`.

4. Start or replace the simulator container.
   - Stop the host UFM service before starting the simulator. On HA hosts use `/etc/init.d/ufmha stop`; on standalone hosts use `systemctl stop ufm-enterprise` and `/etc/init.d/ufmd stop` when present.
   - If the host may be serving a real fabric and the user did not explicitly approve simulator takeover, explain that host UFM must stop and ask before proceeding.
   - Use the verified default container name `ibmgtsim`. If an existing environment already uses `ufm-ibmgtsim`, keep that name only when the user asks to reuse or reproduce it.
   - Stop an existing simulator container only when it is clearly the target of the user's request.
   - When stopping an existing simulator, gracefully stop UFM inside the container before `docker rm -f`, then kill stale `ModelMain`, `opensm`, and `ibdiagnet` processes to avoid port 8000 conflicts on the next start.
   - Run the simulator with host networking, privileged mode, the UFM simulator environment variables, and the workspace mounted as `/mnt/air`.
   - Include `PATH=/opt/ufm/opensm/sbin/:/opt/ufm/opensm/bin/:$PATH` in the container environment so OpenSM and IB tools are available.
   - Use a pinned simulator image tag; do not silently use an unqualified `latest` tag.

5. Validate the simulator.
   - Use the ordered readiness checklist below. Do not report "ready" immediately after `docker ps`; large fabrics can take minutes to initialize.
   - Confirm UFM Web UI is reachable.
   - Default throwaway simulator credentials are `admin` / `123456`. If the target uses different credentials, ask the user or use credentials they explicitly provided for this test session without writing them to the repo.

6. Use the simulator for plugin validation when requested.
   - Build or load the plugin image on the simulator host.
   - Deploy through UFM plugin manager.
   - Validate plugin status, health endpoint, domain endpoint, and UI route when the plugin has UI.
   - Prefer validating through UFM's plugin proxy: `/ufmRest/plugin/<plugin_name>/...`.

## Simulator Image Lookup

Resolve the simulator image in this order:

1. If the user gives an explicit simulator image, use that exact pinned image.
2. If a simulator is already running on the target host, inspect `ibmgtsim` first, then known existing names such as `ufm-ibmgtsim`, and reuse or report its image unless the user asked to upgrade or replace it.
3. If the user asks for `latest GA`, look up the current GA simulator image from the corporate release source or registry first, then pin the chosen tag in the command and response. Do not guess from memory.
4. If no image is provided and no running simulator exists, use the image/tag from the current project or user-provided simulator instructions.
5. If no image is available, stop and ask for the simulator image instead of guessing.

Verified Jenkins Harbor example:

```text
harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.26.0-2_ibmgtsim_release.v2.26.0_ub22:ufm-6.26.0-2
```

Older blog/simulator setup example:

```text
harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.24.2-3_ibmgtsim_master_ub22:ufm-6.24.2-3
```

Use a Harbor image only when it matches the requested version or when the user asks to reproduce a specific Jenkins/blog setup. Treat these as pinned examples, not as generic `latest GA` aliases.

## Command Pattern

Adapt this pattern to the target host, image, and topology:

```bash
set -euo pipefail

WORKDIR=/tmp/ufm-docker-conf
CONTAINER_NAME=${CONTAINER_NAME:-ibmgtsim}
TOPOLOGY_SOURCE=${TOPOLOGY_SOURCE:-/auto/mswg/release/ufm/topologies/xdr_msft_extended_x2/ibdiagnet2.db_csv}
: "${SIMULATOR_IMAGE:?Set SIMULATOR_IMAGE to the pinned UFM simulator image}"

mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

# Stop host UFM before binding simulator services on the same host.
if [ -x /etc/init.d/ufmha ]; then
  /etc/init.d/ufmha stop || true
fi
systemctl stop ufm-enterprise 2>/dev/null || true
if [ -x /etc/init.d/ufmd ]; then
  /etc/init.d/ufmd stop || true
fi

# Stop a previous simulator cleanly before replacing it.
if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  docker exec "${CONTAINER_NAME}" /etc/init.d/ufmd stop || true
  docker exec "${CONTAINER_NAME}" pkill -9 -f ModelMain || true
  docker exec "${CONTAINER_NAME}" pkill -9 -f opensm || true
  docker exec "${CONTAINER_NAME}" pkill -9 -f ibdiagnet || true
  docker rm -f "${CONTAINER_NAME}"
fi

# Copy or download a topology into the workspace.
# .db_csv topologies must be renamed to ibdiagnet2.db_csv for Fabric Analysis.
case "${TOPOLOGY_SOURCE}" in
  *.db_csv)
    TOPOLOGY_TARGET=ibdiagnet2.db_csv
    ;;
  *)
    TOPOLOGY_TARGET=$(basename "${TOPOLOGY_SOURCE}")
    ;;
esac

cp "${TOPOLOGY_SOURCE}" "${WORKDIR}/${TOPOLOGY_TARGET}"

cat > "${WORKDIR}/ibmgtsim.conf" <<EOF
IBMGTSIM_TOPOLOGY=/mnt/air/${TOPOLOGY_TARGET}
IBMGTSIM_SERVER=$(hostname):6000
TELEMETRY_ENDPOINTS=telemetry
EOF

docker run --rm -d --name="${CONTAINER_NAME}" \
  --network=host \
  --shm-size=256m \
  --tmpfs /run \
  --tmpfs /run/lock \
  --volume /lib/modules:/lib/modules:ro \
  --env UFM_FILES_PATH=/opt/ufm/files \
  --env TZ=$(timedatectl | grep 'Time zone' | awk '{print $3}') \
  --env container=docker \
  --env UFM_CONTEXT=ufm-enterprise \
  --env PATH="/opt/ufm/opensm/sbin/:/opt/ufm/opensm/bin/:$PATH" \
  --env LD_PRELOAD="/opt/ibmgtsim/build/lib/libibumad.2ibmgtsim.so" \
  --env IBMGTSIM_CONFIG_FOLDER="/mnt/air/" \
  --privileged \
  --volume "${WORKDIR}:/mnt/air" \
  "${SIMULATOR_IMAGE}"
```

An example of the simulator image is:

```bash
harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.26.0-2_ibmgtsim_release.v2.26.0_ub22:ufm-6.26.0-2
```

## Validation Checklist

Use an ordered readiness poll with a realistic timeout. The verified automation uses roughly 40 minutes total with 60-second polling.

```bash
SIM_READY_DEADLINE=$((SECONDS + 2400))

wait_for() {
  name=$1
  shift
  until "$@"; do
    if [ "${SECONDS}" -ge "${SIM_READY_DEADLINE}" ]; then
      echo "Timed out waiting for ${name}"
      return 1
    fi
    echo "Waiting for ${name}..."
    sleep 60
  done
}

CONTAINER_NAME=${CONTAINER_NAME:-ibmgtsim}

wait_for ibstat docker exec "${CONTAINER_NAME}" ibstat
wait_for ibhosts docker exec "${CONTAINER_NAME}" timeout 2400 ibhosts
wait_for ibswitches docker exec "${CONTAINER_NAME}" timeout 2400 ibswitches
wait_for opensm docker exec "${CONTAINER_NAME}" pgrep -f /opt/ufm/opensm/sbin/opensm
wait_for ModelMain docker exec "${CONTAINER_NAME}" pgrep -f ModelMain.pyc
wait_for UFM_REST_200 sh -c 'test "$(docker exec "${CONTAINER_NAME:-ibmgtsim}" curl -sk -u admin:123456 -o /dev/null -w "%{http_code}" https://localhost/ufmRest/app/ufm_version)" = "200"'
```

- `docker ps` shows the simulator container running, but this alone is not readiness.
- `ibstat`, `ibhosts`, and `ibswitches` succeed in order.
- OpenSM is running: `pgrep -f /opt/ufm/opensm/sbin/opensm`.
- ModelMain is running: `pgrep -f ModelMain.pyc`.
- UFM REST returns HTTP 200 from `https://localhost/ufmRest/app/ufm_version`.
- UFM Web UI responds at `https://<host>/ufm_web/`.
- The default topology appears in UFM views.
- Plugin manager can list, add, enable, and report status for test plugins.
- Plugin REST endpoints work through `/ufmRest/plugin/<plugin_name>/...`.
- Plugin UI renders real data in UFM Web UI when a UI extension is present.

## Stop Or Reconfigure The Simulator

Use this stop sequence before replacing the simulator image, changing the topology, changing `TELEMETRY_ENDPOINTS`, or cleaning up the host:

```bash
CONTAINER_NAME=${CONTAINER_NAME:-ibmgtsim}
docker exec "${CONTAINER_NAME}" /etc/init.d/ufmd stop || true
docker exec "${CONTAINER_NAME}" pkill -9 -f ModelMain || true
docker exec "${CONTAINER_NAME}" pkill -9 -f opensm || true
docker exec "${CONTAINER_NAME}" pkill -9 -f ibdiagnet || true
docker rm -f "${CONTAINER_NAME}"
```

Start a new container after changing `ibmgtsim.conf`; do not treat an in-place config edit as applied.

## Response Contract

When the task is complete, report:

- The simulator host and container name.
- The topology file used.
- The simulator image tag used.
- Ordered readiness results: `ibstat`, `ibhosts`, `ibswitches`, OpenSM, ModelMain, and REST 200.
- Web UI validation result.
- Plugin deployment and validation results when a plugin was deployed.
- Any remaining manual step, especially login credentials, browser access, or topology/image selection.
