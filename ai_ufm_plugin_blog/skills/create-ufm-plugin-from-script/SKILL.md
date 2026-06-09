---
name: create-ufm-plugin-from-script
description: Create NVIDIA UFM plugins from UFM SDK Python scripts. Use when the user asks "Create UFM plugin from script ...", wants to convert a Mellanox/NVIDIA UFM SDK script into a backend plugin, add an optional UFM UI extension, package Docker/plugin lifecycle files, or generate a reusable UFM plugin scaffold.
---

# Create UFM Plugin From Script

## Overview

Use this skill to turn a UFM SDK Python script into a UFM plugin package. Start with a backend-only REST plugin, then add a UFM UI extension only when the user asks for UI or the workflow benefits from a visual panel.

For UFM plugin mechanics, read `references/ufm-plugin-mechanics.md` before making packaging or UI decisions.

## Quick Start

When the request is `Create UFM plugin from script XXX`:

1. Resolve `XXX` to a local file path or to a script in `Mellanox/ufm_sdk_3.0`.
2. Inspect the script and identify the smallest useful behavior to expose as a plugin endpoint.
3. Reject or gate destructive operations. For scripts that reboot, isolate, update, delete, or write fabric state, create a dry-run endpoint first and require explicit user approval before enabling the action endpoint.
4. Run the scaffold helper:

```bash
python3 <skill-dir>/scripts/scaffold_ufm_plugin.py <script-path> --plugin-name <plugin_name> --output-dir <target-dir>
```

Add `--with-ui` when the plugin should extend UFM Web UI:

```bash
python3 <skill-dir>/scripts/scaffold_ufm_plugin.py <script-path> --plugin-name <plugin_name> --output-dir <target-dir> --with-ui
```

5. Replace any generated generic logic with the exact script-specific behavior.
6. Validate generated Python, JSON, and shell syntax before handing off.

## Backend Conversion

Prefer this structure for the first pass:

- `src/logic.py`: pure script-derived logic. Keep UFM REST calls, parsing, and summarization here.
- `src/app.py`: Flask API wrapper with `/healthz`, `/run`, and one domain endpoint such as `/summary`.
- `conf/<plugin>_httpd_proxy.conf`: plugin HTTP port in the UFM plugin range.
- `scripts/init.sh`, `scripts/deinit.sh`, `scripts/upgrade.sh`: lifecycle hooks copied to container root.
- `build/Dockerfile` and `build/docker_build.sh`: image build and `docker save` flow.

For read-only REST scripts, expose query parameters from the original CLI as HTTP query parameters. For example, a script with `--system`, `--active`, and `--show_disabled` should produce an endpoint such as:

```text
/ufmRest/plugin/<plugin>/summary?system=<guid>&active=true&show_disabled=false
```

Do not import the original script directly if it performs CLI parsing, writes local result files, or exits from `__main__`. Extract the useful function into plugin logic instead.

## UI Extension

Add UI only after the backend plugin is stable. Use the advanced UFM SDK plugin pattern:

- Add `conf/<plugin>_ui_conf.json`.
- Serve compiled Angular/module-federation files from `/files/<path>` in the plugin backend.
- Copy the UI bundle into `/data/<plugin>_ui` from `init.sh`.
- Configure the remote entry path as `<plugin>/files/remoteEntry.js`.

Use a left-menu hook for a simple standalone panel. Use a settings or device tab only if the script is naturally scoped to settings or a selected device.

## Validation

Run the checks that match the generated files:

```bash
python3 -m py_compile <plugin-dir>/src/*.py
python3 -m json.tool <plugin-dir>/conf/<plugin>_ui_conf.json
bash -n <plugin-dir>/scripts/init.sh <plugin-dir>/scripts/deinit.sh <plugin-dir>/scripts/upgrade.sh <plugin-dir>/build/docker_build.sh
```

If Docker is available and the user wants a build artifact, run:

```bash
cd <plugin-dir>
bash build/docker_build.sh
```

Do not claim the plugin is deploy-tested unless it has actually been loaded into UFM and exercised through UFM plugin management.

## Output

Return:

- The selected source script and why it was chosen.
- The generated plugin directory.
- The backend endpoints.
- Whether UI was added, and which UFM hook type it uses.
- Validation commands run and results.
- Any manual follow-up needed before production deployment.
