# AI UFM Plugin Blog Package

This package supports a technical blog and podcast segment about using an AI agent to create an NVIDIA UFM plugin from a UFM SDK script.

## Contents

- `blog/create-ufm-plugin-with-ai.md`: technical blog draft.
- `examples/no_ui/ports_snapshot_plugin`: backend-only UFM plugin generated from `scripts/ufm_ports/load_ports.py`.
- `examples/with_ui/ports_snapshot_plugin`: the same plugin with a UFM left-menu UI extension.
- `skills/create-ufm-plugin-from-script`: reusable agent skill for the prompt `Create UFM plugin from script XXX`.

## Selected SDK Script

The demo uses the public UFM SDK script:

```text
Mellanox/ufm_sdk_3.0/scripts/ufm_ports/load_ports.py
```

It is a good first AI-agent demo because it is read-only, maps cleanly to UFM REST API `resources/ports`, and has CLI arguments that naturally become plugin query parameters.

## Validation Run

Validated locally:

```bash
python3 -m py_compile ai_ufm_plugin_blog/skills/create-ufm-plugin-from-script/scripts/scaffold_ufm_plugin.py
python3 -m py_compile ai_ufm_plugin_blog/examples/no_ui/ports_snapshot_plugin/src/*.py ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/src/*.py
python3 -m json.tool ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/conf/ports_snapshot_ui_conf.json
bash -n ai_ufm_plugin_blog/examples/no_ui/ports_snapshot_plugin/scripts/init.sh ai_ufm_plugin_blog/examples/no_ui/ports_snapshot_plugin/scripts/deinit.sh ai_ufm_plugin_blog/examples/no_ui/ports_snapshot_plugin/scripts/upgrade.sh ai_ufm_plugin_blog/examples/no_ui/ports_snapshot_plugin/build/docker_build.sh
bash -n ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/scripts/init.sh ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/scripts/deinit.sh ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/scripts/upgrade.sh ai_ufm_plugin_blog/examples/with_ui/ports_snapshot_plugin/build/docker_build.sh
```

The skill was also validated with `quick_validate.py` from the Codex `skill-creator` skill using a temporary `/tmp` venv containing PyYAML.
