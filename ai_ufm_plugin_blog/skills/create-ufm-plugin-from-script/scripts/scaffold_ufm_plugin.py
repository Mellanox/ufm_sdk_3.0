#!/usr/bin/env python3
"""Generate a conservative UFM plugin scaffold from a UFM SDK Python script."""

from __future__ import annotations

import argparse
import json
import re
import stat
import textwrap
from pathlib import Path


KNOWN_PORTS = {8901, 8910, 8980, 8981, 8982, 8983, 8984, 8989}


def sanitize_plugin_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    if not name:
        raise ValueError("plugin name is empty after sanitization")
    if name[0].isdigit():
        name = f"plugin_{name}"
    return name


def pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-\s]+", value) if part)


def title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("_"))


def detect_api_path(script_text: str) -> str:
    patterns = [
        r"[A-Z0-9_]*API_URL\s*=\s*['\"]([^'\"]+)['\"]",
        r"send_request\(\s*['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, script_text)
        if match:
            return match.group(1)
    return "resources/ports"


def detect_cli_params(script_text: str) -> list[str]:
    constants = dict(re.findall(r"([A-Z][A-Z0-9_]*)\s*=\s*['\"]([A-Za-z0-9_\-]+)['\"]", script_text))
    params = []
    for match in re.finditer(r'"name"\s*:\s*f[\'\"]--\{([A-Za-z0-9_]+)\}', script_text):
        params.append(constants.get(match.group(1), match.group(1)).replace("-", "_"))
    for match in re.finditer(r'"name"\s*:\s*[\'\"]--([A-Za-z0-9_\-]+)[\'\"]', script_text):
        params.append(match.group(1).replace("-", "_"))
    for match in re.finditer(r"add_argument\(\s*['\"]--([A-Za-z0-9_\-]+)['\"]", script_text):
        params.append(match.group(1).replace("-", "_"))
    cleaned = []
    for param in params:
        if param not in cleaned:
            cleaned.append(param)
    return cleaned or ["system", "active", "show_disabled"]


def pick_port(plugin_name: str, requested: int | None) -> int:
    if requested:
        return requested
    seed = sum(ord(ch) for ch in plugin_name)
    port = 8920 + seed % 60
    while port in KNOWN_PORTS:
        port += 1
    return port


def write_file(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def render_logic(plugin_name: str, source_label: str, api_path: str, query_params: list[str]) -> str:
    params_repr = json.dumps(query_params, indent=4).replace("\n", "\n        ")
    return f'''
        import os
        from typing import Any, Dict, Iterable
        from urllib.parse import urljoin

        import requests


        SOURCE_SCRIPT = "{source_label}"
        API_PATH = "{api_path}"
        QUERY_PARAMS = {params_repr}


        def _env_bool(name: str, default: bool) -> bool:
            value = os.environ.get(name)
            if value is None:
                return default
            return value.lower() in ("1", "true", "yes", "on")


        def _ufm_base_url() -> str:
            protocol = os.environ.get("UFM_PROTOCOL", "https")
            host = os.environ.get("UFM_HOST", "127.0.0.1")
            prefix = os.environ.get("UFM_REST_PREFIX", "/ufmRest")
            return f"{{protocol}}://{{host}}{{prefix.strip()}}/"


        def _auth_kwargs() -> Dict[str, Any]:
            token = os.environ.get("UFM_ACCESS_TOKEN")
            if token:
                return {{"headers": {{"Authorization": f"Bearer {{token}}"}}}}
            username = os.environ.get("UFM_USERNAME")
            password = os.environ.get("UFM_PASSWORD")
            if username and password:
                return {{"auth": (username, password)}}
            return {{}}


        def _coerce_bool(value: str | None, default: bool | None = None) -> str | None:
            if value is None or value == "":
                if default is None:
                    return None
                return "true" if default else "false"
            return "true" if str(value).lower() in ("1", "true", "yes", "on") else "false"


        def _filtered_params(args: Dict[str, str]) -> Dict[str, str]:
            params: Dict[str, str] = {{}}
            for name in QUERY_PARAMS:
                value = args.get(name)
                if name in ("active", "show_disabled"):
                    value = _coerce_bool(value, True if name == "active" else False)
                if value not in (None, ""):
                    params[name] = value
            return params


        def _limited(items: Any, limit_value: str | None) -> Any:
            if not limit_value:
                return items
            try:
                limit = int(limit_value)
            except ValueError:
                return items
            if isinstance(items, list) and limit >= 0:
                return items[:limit]
            return items


        def collect(args: Dict[str, str]) -> Dict[str, Any]:
            url = urljoin(_ufm_base_url(), API_PATH)
            params = _filtered_params(args)
            verify = _env_bool("UFM_VERIFY_TLS", False)
            timeout = float(os.environ.get("UFM_REQUEST_TIMEOUT", "30"))
            request_kwargs = _auth_kwargs()
            response = requests.get(url, params=params, verify=verify, timeout=timeout, **request_kwargs)
            response.raise_for_status()
            payload = _limited(response.json(), args.get("limit"))
            return {{
                "plugin": "{plugin_name}",
                "source_script": SOURCE_SCRIPT,
                "api_path": API_PATH,
                "query": params,
                "items": payload,
            }}


        def _iter_items(payload: Any) -> Iterable[Dict[str, Any]]:
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(payload, dict):
                for key in ("items", "ports", "data", "results"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                yield item


        def summarize(collection: Dict[str, Any]) -> Dict[str, Any]:
            items = list(_iter_items(collection.get("items")))
            active = 0
            disabled = 0
            states: Dict[str, int] = {{}}
            for item in items:
                active_value = item.get("active")
                if active_value in (True, "true", "True", 1, "1"):
                    active += 1
                state = str(item.get("state") or item.get("physical_state") or item.get("logical_state") or "unknown")
                states[state] = states.get(state, 0) + 1
                if item.get("enabled") in (False, "false", "False", 0, "0"):
                    disabled += 1
            return {{
                "plugin": collection["plugin"],
                "source_script": collection["source_script"],
                "api_path": collection["api_path"],
                "total_items": len(items),
                "active_items": active,
                "disabled_items": disabled,
                "states": states,
                "sample": items[:5],
            }}
    '''


def render_app(plugin_name: str, class_prefix: str, with_ui: bool) -> str:
    send_import = ", send_from_directory" if with_ui else ""
    content = f'''
        import configparser
        from pathlib import Path

        from flask import Flask, jsonify, request{send_import}

        from logic import collect, summarize


        PLUGIN_NAME = "{plugin_name}"
        DEFAULT_PORT = 8925


        def get_plugin_port() -> int:
            conf_path = Path(f"/config/{{PLUGIN_NAME}}_httpd_proxy.conf")
            if not conf_path.exists():
                return DEFAULT_PORT
            parser = configparser.ConfigParser()
            parser.read_string("[plugin]\\n" + conf_path.read_text(encoding="utf-8"))
            return parser.getint("plugin", "port", fallback=DEFAULT_PORT)


        app = Flask(__name__)


        @app.route("/", methods=["GET"])
        def index():
            return jsonify({{"plugin": PLUGIN_NAME, "endpoints": ["/healthz", "/run", "/summary"]}})


        @app.route("/healthz", methods=["GET"])
        def healthz():
            return jsonify({{"status": "ok", "plugin": PLUGIN_NAME}})


        @app.route("/run", methods=["GET"])
        def run():
            return jsonify(collect(request.args.to_dict()))


        @app.route("/summary", methods=["GET"])
        def summary():
            return jsonify(summarize(collect(request.args.to_dict())))
    '''
    if with_ui:
        content += f'''


        @app.route("/files/<path:file_name>", methods=["GET"])
        def files(file_name):
            data_dir = Path("/data/{plugin_name}_ui")
            bundled_dir = Path(f"/opt/ufm/ufm_plugin_{{PLUGIN_NAME}}/{{PLUGIN_NAME}}_plugin/ui_dist")
            static_dir = data_dir if (data_dir / file_name).exists() else bundled_dir
            return send_from_directory(static_dir, file_name)
        '''
    content += '''


        if __name__ == "__main__":
            app.run(host="127.0.0.1", port=get_plugin_port())
    '''
    return content


def render_init(plugin_name: str, with_ui: bool) -> str:
    ui_copy = ""
    ui_conf = ""
    if with_ui:
        ui_conf = f" $SRC_DIR_PATH/conf/{plugin_name}_ui_conf.json"
        ui_copy = f'''
            rm -rf /data/{plugin_name}_ui
            cp -r "$SRC_DIR_PATH/ui_dist" "/data/{plugin_name}_ui"
        '''
    return f'''
        #!/bin/bash
        set -eE

        PLUGIN_NAME={plugin_name}
        SRC_DIR_PATH=/opt/ufm/ufm_plugin_${{PLUGIN_NAME}}/${{PLUGIN_NAME}}_plugin
        CONFIG_PATH=/config

        mkdir -p "$CONFIG_PATH" /data /log
        cp "$SRC_DIR_PATH/conf/${{PLUGIN_NAME}}_httpd_proxy.conf"{ui_conf} "$CONFIG_PATH"
        {{
            echo "/opt/ufm/files/log/plugins/${{PLUGIN_NAME}}:/log"
            echo "/opt/ufm/ufm_plugins_data/${{PLUGIN_NAME}}:/data"
        }} > "$CONFIG_PATH/${{PLUGIN_NAME}}_shared_volumes.conf"
        {ui_copy}

        required_ufm_version=(6 12 0)
        if [ "${{1:-}}" = "-ufm_version" ]; then
            actual_ufm_version_string=${{2:-0.0.0}}
            actual_ufm_version=(${{actual_ufm_version_string//./ }})
            if [ "${{actual_ufm_version[0]:-0}}" -ge "${{required_ufm_version[0]}}" ] \\
            && [ "${{actual_ufm_version[1]:-0}}" -ge "${{required_ufm_version[1]}}" ]; then
                exit 0
            fi
            echo "UFM version $actual_ufm_version_string is older than required ${{required_ufm_version[*]}}"
            exit 1
        fi

        exit 0
    '''


def render_deinit(plugin_name: str, with_ui: bool) -> str:
    ui_cleanup = f"rm -rf /data/{plugin_name}_ui" if with_ui else ":"
    return f'''
        #!/bin/bash
        set -eE
        {ui_cleanup}
        exit 0
    '''


def render_upgrade() -> str:
    return '''
        #!/bin/bash
        set -eE
        echo "No data migration is required for this plugin scaffold."
        exit 0
    '''


def render_supervisord(plugin_name: str) -> str:
    return f'''
        [supervisord]
        nodaemon=true

        [program:{plugin_name}]
        command=python3 /opt/ufm/ufm_plugin_{plugin_name}/{plugin_name}_plugin/src/app.py
        autostart=true
        autorestart=true
        stdout_logfile=/log/{plugin_name}.log
        stderr_logfile=/log/{plugin_name}.err
        environment=PYTHONUNBUFFERED="1"
    '''


def render_dockerfile(plugin_name: str, with_ui: bool) -> str:
    if with_ui:
        ui_builder = f'''
        FROM node:16-bullseye-slim AS ui_builder

        WORKDIR /ui
        COPY ui/package.json ./
        RUN npm install
        COPY ui/ ./
        RUN npm run build

        '''
        ui_copy = f"COPY --from=ui_builder /ui/dist/{plugin_name}_ui/ ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/ui_dist/"
    else:
        ui_builder = ""
        ui_copy = ""

    return f'''
        {ui_builder}FROM ubuntu:20.04

        ARG DEBIAN_FRONTEND=noninteractive
        ARG PLUGIN_NAME={plugin_name}
        ARG BASE_PATH=/opt/ufm/ufm_plugin_${{PLUGIN_NAME}}

        COPY conf/supervisord.conf /etc/supervisor/conf.d/{plugin_name}.conf
        COPY . ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/
        {ui_copy}
        COPY scripts/init.sh scripts/deinit.sh scripts/upgrade.sh /

        RUN apt-get update \\
            && apt-get install -y --no-install-recommends ca-certificates python3 python3-pip supervisor \\
            && python3 -m pip install --no-cache-dir -r ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/src/requirements.txt \\
            && mkdir -p /var/log/supervisor \\
            && chmod +x /init.sh /deinit.sh /upgrade.sh \\
            && rm -rf /var/lib/apt/lists/*

        CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
    '''


def render_simulator_dockerfile(plugin_name: str) -> str:
    return f'''
        FROM harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.24.2-3_ibmgtsim_master_ub22:ufm-6.24.2-3 AS ui_builder

        ARG DEBIAN_FRONTEND=noninteractive
        RUN apt-get update \\
            && apt-get install -y --no-install-recommends nodejs npm \\
            && rm -rf /var/lib/apt/lists/*

        WORKDIR /ui
        COPY ui/package.json ./
        RUN npm install --force
        COPY ui/ ./
        RUN npm run build

        FROM harbor.mellanox.com/ibtools/ufm-ibmgtsim/ufm_6.24.2-3_ibmgtsim_master_ub22:ufm-6.24.2-3

        ARG PLUGIN_NAME={plugin_name}
        ARG BASE_PATH=/opt/ufm/ufm_plugin_${{PLUGIN_NAME}}
        ARG SIM_UFM_USERNAME=admin
        ARG SIM_UFM_PASSWORD

        ENTRYPOINT []
        ENV UFM_PROTOCOL=https \\
            UFM_HOST=127.0.0.1 \\
            UFM_USERNAME=${{SIM_UFM_USERNAME}} \\
            UFM_PASSWORD=${{SIM_UFM_PASSWORD}} \\
            UFM_VERIFY_TLS=false \\
            PYTHONUNBUFFERED=1

        COPY conf/supervisord.conf /etc/supervisor/conf.d/{plugin_name}.conf
        COPY . ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/
        COPY --from=ui_builder /ui/dist/{plugin_name}_ui/ ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/ui_dist/
        COPY scripts/init.sh scripts/deinit.sh scripts/upgrade.sh /

        RUN python3 -m pip install --no-cache-dir -r ${{BASE_PATH}}/${{PLUGIN_NAME}}_plugin/src/requirements.txt \\
            && mkdir -p /var/log/supervisor \\
            && chmod +x /init.sh /deinit.sh /upgrade.sh

        CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
    '''


def render_dockerignore() -> str:
    return '''
        build/*.img
        build/*.img.gz
        build/*.tar
        build/*.tgz
        ui/node_modules
        ui/dist
        **/__pycache__
        *.pyc
    '''


def render_build_script(plugin_name: str) -> str:
    return f'''
        #!/bin/bash
        set -euo pipefail

        PLUGIN_NAME={plugin_name}
        IMAGE_NAME=ufm-plugin-${{PLUGIN_NAME}}:latest
        OUTPUT=build/ufm-plugin-${{PLUGIN_NAME}}_latest-docker.img.gz

        docker build --build-arg PLUGIN_NAME="${{PLUGIN_NAME}}" -t "${{IMAGE_NAME}}" -f build/Dockerfile .
        docker save "${{IMAGE_NAME}}" | gzip > "${{OUTPUT}}"
        echo "Created $OUTPUT"
    '''


def render_ui_conf(plugin_name: str, label: str) -> str:
    return json.dumps(
        [
            {
                "mfEntry": f"{plugin_name}/files/remoteEntry.js",
                "name": f"{plugin_name}_ui",
                "exposedModule": "PortsSnapshotModule",
                "ngModuleName": "PortsSnapshotModule",
                "hookInfo": {
                    "type": "leftMenu",
                    "label": label,
                    "key": plugin_name,
                    "route": plugin_name.replace("_", "-"),
                    "pluginRoute": "overview",
                    "icon": "fa fa-plug",
                    "order": 8,
                },
            }
        ],
        indent=2,
    ) + "\n"


def write_ui(plugin_dir: Path, plugin_name: str, label: str) -> None:
    ui_dir = plugin_dir / "ui"
    class_name = "PortsSnapshot"
    write_file(
        ui_dir / "package.json",
        f'''
        {{
          "name": "{plugin_name}_ui",
          "version": "0.0.0",
          "private": true,
          "scripts": {{
            "ng": "ng",
            "build": "ng build --configuration production"
          }},
          "dependencies": {{
            "@angular-architects/module-federation": "^14.3.12",
            "@angular/animations": "~13.3.0",
            "@angular/common": "~13.3.0",
            "@angular/compiler": "~13.3.0",
            "@angular/core": "~13.3.0",
            "@angular/forms": "~13.3.0",
            "@angular/platform-browser": "~13.3.0",
            "@angular/platform-browser-dynamic": "~13.3.0",
            "@angular/router": "~13.3.0",
            "rxjs": "~7.5.0",
            "tslib": "^2.3.0",
            "zone.js": "~0.11.4"
          }},
          "devDependencies": {{
            "@angular-devkit/build-angular": "~13.3.9",
            "@angular/cli": "~13.3.9",
            "@angular/compiler-cli": "~13.3.0",
            "@types/node": "^12.11.1",
            "ngx-build-plus": "~13.0.1",
            "typescript": "~4.6.2"
          }}
        }}
        ''',
    )
    write_file(
        ui_dir / "webpack.config.js",
        f'''
        const {{ shareAll, withModuleFederationPlugin }} = require('@angular-architects/module-federation/webpack');

        module.exports = withModuleFederationPlugin({{
          name: '{plugin_name}_ui',
          exposes: {{
            'PortsSnapshotModule': './src/app/ports-snapshot/ports-snapshot.module.ts'
          }},
          shared: {{
            ...shareAll({{ singleton: true, strictVersion: true, requiredVersion: 'auto' }}),
          }},
        }});
        ''',
    )
    write_file(ui_dir / "webpack.prod.config.js", "module.exports = require('./webpack.config');\n")
    write_file(
        ui_dir / "angular.json",
        f'''
        {{
          "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
          "version": 1,
          "projects": {{
            "{plugin_name}_ui": {{
              "projectType": "application",
              "root": "",
              "sourceRoot": "src",
              "architect": {{
                "build": {{
                  "builder": "ngx-build-plus:browser",
                  "options": {{
                    "outputPath": "dist/{plugin_name}_ui",
                    "index": "src/index.html",
                    "main": "src/main.ts",
                    "polyfills": "src/polyfills.ts",
                    "tsConfig": "tsconfig.app.json",
                    "inlineStyleLanguage": "scss",
                    "styles": ["src/styles.scss"],
                    "scripts": [],
                    "extraWebpackConfig": "webpack.config.js",
                    "commonChunk": false
                  }},
                  "configurations": {{
                    "production": {{
                      "optimization": true,
                      "outputHashing": "all",
                      "extraWebpackConfig": "webpack.prod.config.js"
                    }},
                    "development": {{
                      "buildOptimizer": false,
                      "optimization": false,
                      "vendorChunk": true,
                      "extractLicenses": false,
                      "sourceMap": true,
                      "namedChunks": true
                    }}
                  }},
                  "defaultConfiguration": "production"
                }}
              }}
            }}
          }},
          "defaultProject": "{plugin_name}_ui"
        }}
        ''',
    )
    write_file(
        ui_dir / "tsconfig.json",
        '''
        {
          "compileOnSave": false,
          "compilerOptions": {
            "baseUrl": "./",
            "outDir": "./dist/out-tsc",
            "forceConsistentCasingInFileNames": true,
            "strict": true,
            "noImplicitOverride": true,
            "noPropertyAccessFromIndexSignature": false,
            "noImplicitReturns": true,
            "noFallthroughCasesInSwitch": true,
            "sourceMap": true,
            "declaration": false,
            "downlevelIteration": true,
            "experimentalDecorators": true,
            "moduleResolution": "node",
            "importHelpers": true,
            "target": "es2020",
            "module": "es2020",
            "lib": ["es2020", "dom"]
          },
          "angularCompilerOptions": {
            "enableI18nLegacyMessageIdFormat": false,
            "strictInjectionParameters": true,
            "strictInputAccessModifiers": true,
            "strictTemplates": true
          }
        }
        ''',
    )
    write_file(
        ui_dir / "tsconfig.app.json",
        '''
        {
          "extends": "./tsconfig.json",
          "compilerOptions": {
            "outDir": "./out-tsc/app",
            "types": []
          },
          "files": ["src/main.ts", "src/polyfills.ts"],
          "include": ["src/**/*.d.ts", "src/**/*.ts"]
        }
        ''',
    )
    write_file(ui_dir / "src/index.html", "<app-root></app-root>\n")
    write_file(ui_dir / "src/main.ts", "import('./bootstrap').catch(err => console.error(err));\n")
    write_file(ui_dir / "src/polyfills.ts", "import 'zone.js';\n")
    write_file(ui_dir / "src/styles.scss", "body { margin: 0; font-family: Arial, sans-serif; }\n")
    write_file(
        ui_dir / "src/bootstrap.ts",
        '''
        import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
        import { PortsSnapshotModule } from './app/ports-snapshot/ports-snapshot.module';

        platformBrowserDynamic().bootstrapModule(PortsSnapshotModule).catch(err => console.error(err));
        ''',
    )
    write_file(
        ui_dir / "src/app/ports-snapshot/ports-snapshot.module.ts",
        f'''
        import {{ CommonModule }} from '@angular/common';
        import {{ HttpClientModule }} from '@angular/common/http';
        import {{ NgModule }} from '@angular/core';
        import {{ RouterModule }} from '@angular/router';
        import {{ {class_name}Component }} from './ports-snapshot.component';

        @NgModule({{
          declarations: [{class_name}Component],
          imports: [
            CommonModule,
            HttpClientModule,
            RouterModule.forChild([
              {{ path: 'overview', component: {class_name}Component }},
              {{ path: '', redirectTo: 'overview', pathMatch: 'full' }},
              {{ path: '**', redirectTo: 'overview' }}
            ])
          ],
          exports: [{class_name}Component]
        }})
        export class PortsSnapshotModule {{}}
        ''',
    )
    write_file(
        ui_dir / "src/app/ports-snapshot/ports-snapshot.service.ts",
        f'''
        import {{ HttpClient }} from '@angular/common/http';
        import {{ Injectable }} from '@angular/core';
        import {{ Observable }} from 'rxjs';

        export interface PortsSummary {{
          total_items: number;
          active_items: number;
          disabled_items: number;
          states: Record<string, number>;
          sample: Array<Record<string, unknown>>;
        }}

        @Injectable({{ providedIn: 'root' }})
        export class PortsSnapshotService {{
          constructor(private http: HttpClient) {{}}

          getSummary(): Observable<PortsSummary> {{
            return this.http.get<PortsSummary>('/ufmRest/plugin/{plugin_name}/summary');
          }}
        }}
        ''',
    )
    write_file(
        ui_dir / "src/app/ports-snapshot/ports-snapshot.component.ts",
        f'''
        import {{ Component, OnInit }} from '@angular/core';
        import {{ PortsSnapshotService, PortsSummary }} from './ports-snapshot.service';

        @Component({{
          selector: 'ufm-ports-snapshot',
          templateUrl: './ports-snapshot.component.html',
          styleUrls: ['./ports-snapshot.component.scss']
        }})
        export class {class_name}Component implements OnInit {{
          loading = true;
          error = '';
          summary?: PortsSummary;

          constructor(private service: PortsSnapshotService) {{}}

          ngOnInit(): void {{
            this.refresh();
          }}

          refresh(): void {{
            this.loading = true;
            this.error = '';
            this.service.getSummary().subscribe({{
              next: value => {{
                this.summary = value;
                this.loading = false;
              }},
              error: err => {{
                this.error = err?.message || 'Failed to load ports summary';
                this.loading = false;
              }}
            }});
          }}
        }}
        ''',
    )
    write_file(
        ui_dir / "src/app/ports-snapshot/ports-snapshot.component.html",
        f'''
        <section class="ports-panel">
          <header>
            <h2>{label}</h2>
            <button type="button" (click)="refresh()" [disabled]="loading">Refresh</button>
          </header>

          <div class="status" *ngIf="loading">Loading...</div>
          <div class="error" *ngIf="error">{{{{ error }}}}</div>

          <div class="metrics" *ngIf="summary && !loading">
            <div>
              <span>Total</span>
              <strong>{{{{ summary.total_items }}}}</strong>
            </div>
            <div>
              <span>Active</span>
              <strong>{{{{ summary.active_items }}}}</strong>
            </div>
            <div>
              <span>Disabled</span>
              <strong>{{{{ summary.disabled_items }}}}</strong>
            </div>
          </div>

          <table *ngIf="summary?.sample?.length">
            <thead>
              <tr>
                <th>Node</th>
                <th>Port</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let item of summary?.sample">
                <td>{{{{ item['system_name'] || item['node_name'] || item['system'] || '-' }}}}</td>
                <td>{{{{ item['port'] || item['port_number'] || item['name'] || '-' }}}}</td>
                <td>{{{{ item['state'] || item['physical_state'] || item['logical_state'] || 'unknown' }}}}</td>
              </tr>
            </tbody>
          </table>
        </section>
        ''',
    )
    write_file(
        ui_dir / "src/app/ports-snapshot/ports-snapshot.component.scss",
        '''
        .ports-panel {
          color: #1f2933;
          padding: 24px;
        }

        header {
          align-items: center;
          display: flex;
          justify-content: space-between;
          margin-bottom: 20px;
        }

        h2 {
          font-size: 22px;
          font-weight: 600;
          margin: 0;
        }

        button {
          background: #76b900;
          border: 0;
          color: #ffffff;
          cursor: pointer;
          font-weight: 600;
          padding: 8px 14px;
        }

        button:disabled {
          cursor: default;
          opacity: 0.55;
        }

        .metrics {
          display: grid;
          gap: 12px;
          grid-template-columns: repeat(3, minmax(120px, 1fr));
          margin-bottom: 20px;
        }

        .metrics div {
          border: 1px solid #d9e2ec;
          padding: 14px;
        }

        .metrics span {
          color: #52606d;
          display: block;
          font-size: 12px;
          margin-bottom: 6px;
          text-transform: uppercase;
        }

        .metrics strong {
          font-size: 24px;
        }

        table {
          border-collapse: collapse;
          width: 100%;
        }

        th,
        td {
          border-bottom: 1px solid #d9e2ec;
          padding: 10px;
          text-align: left;
        }

        .error {
          color: #b42318;
        }
        ''',
    )


def render_readme(plugin_name: str, source_label: str, with_ui: bool) -> str:
    ui_text = "This variant includes a UFM left-menu UI extension." if with_ui else "This variant is backend-only and does not include UI."
    return f'''
        # {title_case(plugin_name)} UFM Plugin

        Generated from `{source_label}`.

        {ui_text}

        ## Build

        ```bash
        bash build/docker_build.sh
        docker load -i build/ufm-plugin-{plugin_name}_latest-docker.img.gz
        ```

        Manage the loaded plugin from UFM Settings > Plugins Management or with UFM plugin management APIs/scripts.

        ## Endpoints

        - `/ufmRest/plugin/{plugin_name}/healthz`
        - `/ufmRest/plugin/{plugin_name}/run`
        - `/ufmRest/plugin/{plugin_name}/summary`

        Set `UFM_HOST`, `UFM_PROTOCOL`, and either `UFM_ACCESS_TOKEN` or `UFM_USERNAME` plus `UFM_PASSWORD` for outbound UFM REST calls.
    '''


def scaffold(args: argparse.Namespace) -> Path:
    script_path = Path(args.script).expanduser().resolve()
    script_text = script_path.read_text(encoding="utf-8")
    try:
        source_label = script_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        source_label = script_path.as_posix()
    plugin_name = sanitize_plugin_name(args.plugin_name or script_path.stem)
    class_prefix = pascal_case(plugin_name)
    label = args.ui_label or title_case(plugin_name)
    api_path = args.api_path or detect_api_path(script_text)
    query_params = detect_cli_params(script_text)
    port = pick_port(plugin_name, args.port)
    plugin_dir = Path(args.output_dir).expanduser().resolve() / f"{plugin_name}_plugin"

    write_file(plugin_dir / "src/logic.py", render_logic(plugin_name, source_label, api_path, query_params))
    write_file(plugin_dir / "src/app.py", render_app(plugin_name, class_prefix, args.with_ui))
    write_file(plugin_dir / "src/requirements.txt", "flask==3.0.3\nrequests==2.32.3\n")
    write_file(plugin_dir / "conf" / f"{plugin_name}_httpd_proxy.conf", f"port={port}\n")
    write_file(plugin_dir / "conf/supervisord.conf", render_supervisord(plugin_name))
    write_file(plugin_dir / "scripts/init.sh", render_init(plugin_name, args.with_ui), executable=True)
    write_file(plugin_dir / "scripts/deinit.sh", render_deinit(plugin_name, args.with_ui), executable=True)
    write_file(plugin_dir / "scripts/upgrade.sh", render_upgrade(), executable=True)
    write_file(plugin_dir / "build/Dockerfile", render_dockerfile(plugin_name, args.with_ui))
    write_file(plugin_dir / "build/docker_build.sh", render_build_script(plugin_name), executable=True)
    write_file(plugin_dir / "README.generated.md", render_readme(plugin_name, source_label, args.with_ui))

    if args.with_ui:
        write_file(plugin_dir / "conf" / f"{plugin_name}_ui_conf.json", render_ui_conf(plugin_name, label))
        write_file(plugin_dir / "build/Dockerfile.simulator", render_simulator_dockerfile(plugin_name))
        write_file(plugin_dir / ".dockerignore", render_dockerignore())
        write_ui(plugin_dir, plugin_name, label)

    return plugin_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a UFM plugin scaffold from a UFM SDK Python script.")
    parser.add_argument("script", help="Path to the UFM SDK Python script")
    parser.add_argument("--plugin-name", help="Plugin name. Defaults to the script file stem.")
    parser.add_argument("--output-dir", required=True, help="Directory where the plugin folder will be created")
    parser.add_argument("--port", type=int, help="Plugin HTTP port. Defaults to a deterministic 8900-8999 value.")
    parser.add_argument("--api-path", help="UFM REST API path to call, for example resources/ports")
    parser.add_argument("--with-ui", action="store_true", help="Generate a UFM UI extension scaffold")
    parser.add_argument("--ui-label", help="Visible label for the generated UFM UI entry")
    args = parser.parse_args()

    plugin_dir = scaffold(args)
    print(plugin_dir)


if __name__ == "__main__":
    main()
