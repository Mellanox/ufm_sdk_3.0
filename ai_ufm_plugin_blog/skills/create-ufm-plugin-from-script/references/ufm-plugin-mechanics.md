# UFM Plugin Mechanics

Use this reference when packaging a script as a UFM plugin.

## Source Patterns

The public `Mellanox/ufm_sdk_3.0` repository contains both script examples and plugin examples:

- `scripts/`: Python examples that collect data or operate devices through UFM REST API.
- `plugins/hello_world_plugin`: minimal backend plugin example.
- `plugins/advanced_hello_world_plugin`: backend plus Angular UI extension example.

For an AI-assisted demo, prefer read-only scripts from `scripts/` because they can be exposed safely as REST endpoints before any UI is added.

## Backend Packaging

A UFM plugin is packaged as a Docker image named `ufm-plugin-<plugin_name>` with a tag such as `latest`.

Expected lifecycle files in the image root:

- `/init.sh`: runs when UFM adds the plugin. Copy plugin configuration files into `/config`.
- `/deinit.sh`: runs when UFM removes the plugin. Return zero and clean plugin-owned data only.
- `/upgrade.sh`: runs during plugin upgrade. Return zero only after successful migration.

Common configuration files:

- `<plugin_name>_httpd_proxy.conf`: one line, `port=<port>`. UFM uses this to proxy authenticated REST calls to the plugin.
- `<plugin_name>_shared_volumes.conf`: optional host-to-container volume mappings.
- `<plugin_name>_runtime_args.conf`: optional resource limits.

Use the plugin port range `8900-8999`. Avoid known sample/plugin ports such as `8901`, `8910`, `8980`, `8981`, `8982-8984`, and `8989`.

UFM proxies plugin REST calls through:

```text
/ufmRest/plugin/<plugin_name>/<internal_plugin_url>
```

The local UFM implementation generates Apache proxy rules in `scripts/ufm_conf_creator.py` with this path shape.

## UI Extension

UFM UI extensions use an Angular module-federation remote plus a UI configuration file copied to `/config`:

```text
<plugin_name>_ui_conf.json
```

Typical fields:

- `mfEntry`: remote entry path, for example `<plugin_name>/files/remoteEntry.js`.
- `name`: module federation remote name.
- `exposedModule`: exposed Angular module key from webpack config.
- `ngModuleName`: exported Angular module class name.
- `hookInfo.type`: UFM extension point.

Supported hook types seen in the SDK docs include:

- `leftMenu`
- `dynamicLeftMenuItems`
- `deviceContextMenu`
- `settingsDetailsTabs`
- `deviceDetailsTabs`
- `devicesDataTable`
- `existingRoute`

For a first UI demo, use `leftMenu` and a simple panel that calls the plugin backend through `/ufmRest/plugin/<plugin_name>/...`.

## Safety Rules

Classify the source script before exposing it:

- Read-only collection or reporting: OK to expose as `GET`.
- Configuration update: require `POST`, input validation, and dry-run mode.
- Reboot, isolation, firmware update, delete, or other disruptive actions: require explicit user confirmation and add a disabled-by-default action endpoint.

Never convert a destructive CLI script into a one-click UI operation without confirmation, status reporting, and audit-friendly logging.
