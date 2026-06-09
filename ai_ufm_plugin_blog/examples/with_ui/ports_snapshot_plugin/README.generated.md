# Ports Snapshot UFM Plugin

Generated from `scripts/ufm_ports/load_ports.py`.

This variant includes a UFM left-menu UI extension.

## Build

```bash
bash build/docker_build.sh
docker load -i build/ufm-plugin-ports_snapshot_latest-docker.img.gz
```

Manage the loaded plugin from UFM Settings > Plugins Management or with UFM plugin management APIs/scripts.

The UI-enabled image builds the Angular module-federation remote during the Docker build and serves the compiled files through:

```text
/ufmRest/plugin/ports_snapshot/files/remoteEntry.js
```

## Endpoints

- `/ufmRest/plugin/ports_snapshot/healthz`
- `/ufmRest/plugin/ports_snapshot/run`
- `/ufmRest/plugin/ports_snapshot/summary`

Set `UFM_HOST`, `UFM_PROTOCOL`, and either `UFM_ACCESS_TOKEN` or `UFM_USERNAME` plus `UFM_PASSWORD` for outbound UFM REST calls.
