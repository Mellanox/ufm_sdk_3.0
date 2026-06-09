---
name: create-ufm-plugin-from-script
description: Create NVIDIA UFM plugins from scripts, containers, or behavior prompts. Use when the user asks "Create UFM plugin from script ...", "Create UFM plugin from container ...", asks to add UI or API to a UFM plugin, or asks to deploy a generated plugin on UFM or the UFM simulator.
---

# Create UFM Plugin

## Overview

This is a Markdown-only playbook for creating UFM plugins with an AI agent. It intentionally has no helper scripts, templates, or generated code bundled inside the skill. When this skill is used, create or update the plugin files directly in the target repository by following the workflow below.

Start with the smallest backend-only plugin that proves the requested behavior. Add API, UI, packaging, and deployment steps only when the user asks for them or when they are required to validate the plugin.

## Trigger Prompts

Use this skill for prompts like:

- `Create UFM plugin from script <script_path>`
- `Create UFM plugin from container <image_or_dockerfile>`
- `Create UFM plugin that will scrape UFM events and stream them to fluentd destination <destination> every <T> interval`
- `Add UI <optional_ui_template>`
- `Add API to plugin <api_description>`
- `Deploy plugin on server <ufm_host>`

## Workflow

1. Resolve the user intent.
   - Identify whether the input is a UFM SDK script, an existing container, an existing plugin directory, or a new behavior description.
   - Find the exact source file, image, plugin directory, host, or destination mentioned by the user.
   - Ask a short follow-up only if a required target is missing and cannot be inferred.

2. Classify safety before generating behavior.
   - Read-only reporting is safe to expose as a GET-style endpoint.
   - Configuration updates must use explicit inputs, validation, and a dry-run mode.
   - Reboot, isolation, firmware update, delete, or disruptive fabric actions must be disabled by default and require explicit user confirmation before enablement.

3. Create the backend plugin first.
   - Extract the smallest useful logic from the script, container, or behavior prompt.
   - Keep UFM access, parsing, and summarization in a logic module.
   - Add a thin HTTP API wrapper with health and domain endpoints.
   - Preserve the original CLI or container behavior as closely as possible while making inputs explicit through HTTP parameters or request body fields.

4. Package it as a UFM plugin.
   - Use a Docker image named `ufm-plugin-<plugin_name>` with a clear tag.
   - Include lifecycle hooks for add, remove, and upgrade.
   - Include UFM plugin configuration under `conf/`.
   - Use a plugin HTTP port in the UFM plugin range `8900-8999`; avoid common sample ports such as `8901`, `8910`, `8980`, `8981`, `8982-8984`, and `8989`.
   - Expose authenticated REST calls through `/ufmRest/plugin/<plugin_name>/<endpoint>`.

5. Add APIs only after the base plugin works.
   - Add one endpoint per clear user workflow.
   - Keep request and response schemas compact.
   - Return operational status, validation errors, and enough data for troubleshooting.
   - Avoid hiding destructive actions behind simple one-click endpoints.

6. Add UI only when requested.
   - Prefer a simple UFM left-menu page for first demos.
   - Use settings or device hooks only when the plugin is naturally scoped to settings or selected devices.
   - Serve the UI bundle from the plugin backend and register it with UFM UI configuration.
   - The UI should call the plugin through `/ufmRest/plugin/<plugin_name>/...`.

7. Validate before claiming success.
   - Run syntax checks for every generated language and shell file.
   - Validate JSON configuration files.
   - Build the plugin image when Docker is available and the user requested an artifact.
   - Do not claim deploy testing unless the plugin was actually deployed and exercised on UFM or the UFM simulator.

8. Deploy when requested.
   - Build and save the plugin image.
   - Copy or load it on the target UFM host.
   - Use UFM plugin manager to deploy, add, enable, and inspect status.
   - Validate REST endpoints through UFM's plugin proxy.
   - If UI was added, open UFM Web UI and verify the plugin entry renders real data.

## Expected Plugin Shape

For a script-derived backend plugin, generate a directory with:

- `src/logic.py` for script-derived logic.
- `src/app.py` or the repository's existing web framework wrapper.
- `src/requirements.txt` when Python dependencies are needed.
- `conf/<plugin_name>_httpd_proxy.conf` for the plugin port.
- Optional `conf/<plugin_name>_ui_conf.json` when UI is requested.
- `scripts/init.sh`, `scripts/deinit.sh`, and `scripts/upgrade.sh` for lifecycle.
- `build/Dockerfile` and `build/docker_build.sh` for packaging.
- `README.generated.md` with endpoints, build steps, deployment steps, and validation notes.

For a container-derived plugin, wrap the existing image or Dockerfile with UFM lifecycle and configuration files instead of rewriting the workload. Preserve the original process contract and document required environment variables, volumes, ports, and health checks.

For a behavior prompt, choose the simplest runtime that matches the task. For example, an event streaming plugin can poll UFM events on an interval, transform them into compact records, and send them to the requested Fluentd destination.

## UFM UI Notes

UFM UI extensions use a frontend bundle plus a UI configuration file copied to UFM plugin config. For a first UI:

- Use a left-menu hook.
- Give the page a clear domain label such as `Ports Snapshot`.
- Show live status from the backend rather than static placeholder content.
- Include loading, empty, success, and error states.
- Keep the first UI compact: summary cards, one small table, and a refresh action are enough.

## UFM Simulator Notes

For demo and development, prefer deploying first on the UFM simulator when it is available. The simulator gives a realistic UFM REST and Web UI surface without requiring a physical fabric. When the user asks to deploy on a simulator host:

- Confirm the simulator container is running.
- Confirm UFM Web UI and REST are reachable.
- Deploy with UFM plugin manager.
- Validate plugin status, health endpoint, domain endpoint, and UI entry if present.

## Response Contract

When the task is complete, report:

- The source input used: script, container, plugin directory, or behavior prompt.
- The plugin directory created or updated.
- The backend endpoints.
- Whether API or UI was added.
- The UFM UI hook type when UI exists.
- Validation performed and results.
- Deployment target and plugin manager status when deployed.
- Any manual follow-up needed before production use.
