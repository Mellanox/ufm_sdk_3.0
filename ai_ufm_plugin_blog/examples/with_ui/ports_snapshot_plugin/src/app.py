import configparser
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from logic import collect, summarize


PLUGIN_NAME = "ports_snapshot"
DEFAULT_PORT = 8925


def get_plugin_port() -> int:
    conf_path = Path(f"/config/{PLUGIN_NAME}_httpd_proxy.conf")
    if not conf_path.exists():
        return DEFAULT_PORT
    parser = configparser.ConfigParser()
    parser.read_string("[plugin]\n" + conf_path.read_text(encoding="utf-8"))
    return parser.getint("plugin", "port", fallback=DEFAULT_PORT)


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({"plugin": PLUGIN_NAME, "endpoints": ["/healthz", "/run", "/summary"]})


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok", "plugin": PLUGIN_NAME})


@app.route("/run", methods=["GET"])
def run():
    return jsonify(collect(request.args.to_dict()))


@app.route("/summary", methods=["GET"])
def summary():
    return jsonify(summarize(collect(request.args.to_dict())))



@app.route("/files/<path:file_name>", methods=["GET"])
def files(file_name):
    data_dir = Path("/data/ports_snapshot_ui")
    bundled_dir = Path(f"/opt/ufm/ufm_plugin_{PLUGIN_NAME}/{PLUGIN_NAME}_plugin/ui_dist")
    static_dir = data_dir if (data_dir / file_name).exists() else bundled_dir
    return send_from_directory(static_dir, file_name)



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=get_plugin_port())
