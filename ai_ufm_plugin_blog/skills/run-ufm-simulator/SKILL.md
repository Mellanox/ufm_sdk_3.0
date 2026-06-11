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
   - Use the default topology when the user does not provide one.
   - Resolve the simulator image using the image lookup rules below.
   - Do not store user passwords or tokens in generated files.

2. Prepare the simulator workspace on the target host.
   - Use `/opt/ufm-ibmgtsim` as the simulator workspace unless the user requests another path.
   - Create `/opt/ufm-ibmgtsim/air_data`.
   - Copy or download the topology file into `air_data`.
   - Write `ibmgtsim.conf` into `air_data`.

3. Configure `ibmgtsim.conf`.
   - Set `IBMGTSIM_TOPOLOGY` to the topology path as seen inside the container, for example `/mnt/air/IS1-16.topo` or `/mnt/air/BM.2.topo`.
   - Set `IBMGTSIM_SERVER=<hostname>:6000`.
   - Set `TELEMETRY_ENDPOINTS=telemetry` unless the user explicitly requests `endpoints`.

4. Start or replace the simulator container.
   - Stop an existing simulator container only when it is clearly the target of the user's request.
   - Run the simulator with host networking, privileged mode, the UFM simulator environment variables, and `./air_data:/mnt/air`.
   - Use a pinned simulator image tag; do not silently use an unqualified `latest` tag.

5. Validate the simulator.
   - Confirm the container is running.
   - Confirm UFM REST is reachable.
   - Confirm UFM Web UI is reachable.
   - If credentials are needed, ask the user or use credentials they explicitly provided for this test session without writing them to the repo.

6. Use the simulator for plugin validation when requested.
   - Build or load the plugin image on the simulator host.
   - Deploy through UFM plugin manager.
   - Validate plugin status, health endpoint, domain endpoint, and UI route when the plugin has UI.
   - Prefer validating through UFM's plugin proxy: `/ufmRest/plugin/<plugin_name>/...`.

## Simulator Image Lookup

Resolve the simulator image in this order:

1. If the user gives an explicit simulator image, use that exact pinned image.
2. If a simulator is already running on the target host, inspect `ufm-ibmgtsim` and reuse or report its image unless the user asked to upgrade or replace it.
3. If the user asks for `latest GA`, look up the current GA simulator image from the corporate release source or registry first, then pin the chosen tag in the command and response. Do not guess from memory.
4. If no image is provided and no running simulator exists, use the image/tag from the current project or user-provided simulator instructions.
5. If no image is available, stop and ask for the simulator image instead of guessing.

Known Harbor example from the current simulator workflow:

```text
harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.24.2-3_ibmgtsim_master_ub22:ufm-6.24.2-3
```

Use this Harbor image only when it matches the requested version or when the user asks to reproduce the current blog/simulator setup. Treat it as a pinned example, not as a generic `latest GA` alias.

## Command Pattern

Adapt this pattern to the target host, image, and topology:

```bash
mkdir -p /opt/ufm-ibmgtsim/air_data
cd /opt/ufm-ibmgtsim

# Optional: copy or download a topology into ./air_data.
# Additional internal topology files may be available from the corporate topo repository.

cat > /opt/ufm-ibmgtsim/air_data/ibmgtsim.conf <<EOF
IBMGTSIM_TOPOLOGY=/mnt/air/<topology-file>
IBMGTSIM_SERVER=$(hostname):6000
TELEMETRY_ENDPOINTS=telemetry
EOF

docker run --rm -d --name=ufm-ibmgtsim \
  --network=host \
  --shm-size=256m \
  --tmpfs /run \
  --tmpfs /run/lock \
  --volume /lib/modules:/lib/modules:ro \
  --env UFM_FILES_PATH=/opt/ufm/files \
  --env TZ=$(timedatectl | grep 'Time zone' | awk '{print $3}') \
  --env container=docker \
  --env UFM_CONTEXT=ufm-enterprise \
  --env LD_PRELOAD="/opt/ibmgtsim/build/lib/libibumad.2ibmgtsim.so" \
  --env IBMGTSIM_CONFIG_FOLDER="/mnt/air/" \
  --privileged \
  --volume ./air_data:/mnt/air \
  <ufm-simulator-image>:<tag>
```

An example of the simulator image is:

```bash
harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.24.2-3_ibmgtsim_master_ub22:ufm-6.24.2-3
```

## Validation Checklist

- `docker ps` shows `ufm-ibmgtsim` running.
- UFM Web UI responds at `https://<host>/ufm_web/`.
- UFM REST responds at `https://<host>/ufmRest/...`.
- The default topology appears in UFM views.
- Plugin manager can list, add, enable, and report status for test plugins.
- Plugin REST endpoints work through `/ufmRest/plugin/<plugin_name>/...`.
- Plugin UI renders real data in UFM Web UI when a UI extension is present.

## Response Contract

When the task is complete, report:

- The simulator host and container name.
- The topology file used.
- The simulator image tag used.
- Web UI and REST validation results.
- Plugin deployment and validation results when a plugin was deployed.
- Any remaining manual step, especially login credentials, browser access, or topology/image selection.
