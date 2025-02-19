import time
import logging
import os
import shutil
import subprocess
import json
import requests
import yaml
import signal

from ufm_sdk_tools.src.general_utils import general_utils, utils_constants
import pytest


class BaseTestTfs:
    tele_host = "127.0.0.1"
    tele_url = "csv/metrics"
    tele_port = "9001"
    fluent_host = "10.209.38.160"
    fluent_port = "24225"
    interval = "10"
    bulk_streaming = False
    compressed_streaming = False
    stream_only_new_samples = False
    c_fluent_streamer = True
    enabled = True
    endpoints = None
    bind = '0.0.0.0'

    def __init__(self):
        self.ufm_server = None
        self.simulation_process = None
        self.server_process = None
        self.tag_msg = None
        self.port=8981

    def run_simulation(self, simulation_paths):
        if self.simulation_process is not None:
            return -1
        current_directory = os.path.dirname(os.path.abspath(__file__))
        try:
            command = ["python","telemetry_simulation.py","--paths"]+simulation_paths
            self.simulation_process = subprocess.Popen(command, cwd=current_directory,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            print(f"running simulation on pid {self.simulation_process.pid}")
        except FileNotFoundError as e:
            print(f"could not run this process due to {e}")
            print(self.simulation_process.stderr.readlines())

    def run_server(self):
        if self.server_process is not None:
            return -1
        command = ["python","plugins/fluentd_telemetry_plugin/src/app.py"]
        current_script_path_abs = os.path.abspath(__file__)
        base_directory = current_script_path_abs
        for _ in range(3):
            base_directory = os.path.dirname(base_directory)
        try:
            self.server_process = subprocess.Popen(command,cwd=base_directory, text=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Started a server with PID: {self.server_process.pid}")
            return self.server_process.pid
        except FileNotFoundError as error:
            print(f"Failed to find app.py {error}, cwd {base_directory}")
            return -1
        except subprocess.SubprocessError as error:
            print(f"An unspecified error occurred while trying to run server {error}")
            return -1

    def stop_simulation(self):
        if self.simulation_process:
            os.kill(self.simulation_process.pid,signal.SIGKILL)

    def stop_server(self):
        if self.server_process:
            os.kill(self.server_process.pid,signal.SIGKILL)

    def prepare_environment(self):
        config_folder = "/config"
        os.makedirs(config_folder, exist_ok=True)
        os.makedirs("/log", exist_ok=True)
        self.prepare_fluentd()

        config_folder_src = os.path.basename(os.path.basename(__file__))+"/conf/"
        if os.path.exists(config_folder_src):
            for file_name in os.listdir(config_folder_src):
                source_file = os.path.join(config_folder_src, file_name)
                destination_filename = os.path.join(config_folder,file_name)
                shutil.copy(source_file, destination_filename)

        self.run_fluentd()

    def prepare_fluentd(self, protocol="forward", bind='0.0.0.0'):
        general_utils.run_command_status("docker stop $(docker ps -q)", self.fluent_host)
        os.makedirs("/tmp/fluentd",exist_ok=True)
        general_utils.run_command_status("docker pull fluent/fluentd:edge", self.fluent_host)
        conf = f"""<source>
  @type {protocol}
  bind {str(bind)}
  port {self.fluent_port}
</source>
<match **>
  @type stdout
</match>"""
        general_utils.write_to_file('fluentd.conf', conf, "localhost", "/config/fluentd.conf")

    def run_fluentd(self):
        log_file = os.path.abspath("/log/tfs.log")  # Log file location
        docker_image = "fluent/fluent:edge"
        config_folder = "/config"

        try:
            if not os.path.exists(log_file):
                open(log_file,'a',encoding='utf-8').close() # touch log_file

            subprocess.run((f"docker run -i --rm --network host -v {config_folder}:/fluentd/etc "+
                            f"{docker_image} -c /fluentd/etc/fluentd.conf").split(),
                            stdout=open(log_file,"a",encoding="utf-8"),stderr=subprocess.STDOUT,check=False)

            print("fluentd container is running")
        except subprocess.CalledProcessError as error:
            print(f"Error occurred while running fluentd docker container: {error}")

    def stop_fluentd(self):
        try:
            subprocess.run("docker rm -f fluentd".split(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        except subprocess.CalledProcessError as error:
            print(f"Error occurred while stopping fluentd docker container: {error}")

    def set_conf_from_json(self,body):
        url = f'http://localhost:{self.port}/conf'
        response = requests.post(url, body=json.dumps(body), headers={"Content-Type": "application/json"},timeout=20)
        return response.text, response.status_code

    def set_conf(self, compressed_streaming=False, c_fluent_streamer=True, meta=False):
        # compressed_streaming True for using HTTP protocol / False for using Forward protocol
        # c_fluent_streamer True for using C library / False for using python library
        body = BaseTestTfs.configure_body_conf(self.tele_host, self.tele_url, self.tele_port,
                                               self.fluent_host, self.fluent_port, self.interval,
                                               self.bulk_streaming, self.stream_only_new_samples, compressed_streaming,
                                               c_fluent_streamer, self.enabled, meta, endpoints_array=self.endpoints)
        return self.set_conf_from_json(body)

    def get_conf(self):
        url = f'http://localhost:{self.port}/conf'
        response = requests.get(url, headers={"Content-Type": "application/json"},timeout=20)
        return response.json(), response.status_code

    @staticmethod
    def configure_body_conf(tele_host, tele_url, tele_port,
                           fluent_host, fluent_port, interval,
                           bulk_streaming, stream_only_new_samples, compressed_streaming, c_fluent_streamer, enabled,
                           meta=False,
                           endpoints_array=None):
        if not endpoints_array:
            endpoints = [{
                "host": tele_host,
                "url": tele_url,
                "interval": int(interval),
                "port": int(tele_port),
                "message_tag_name": "UFM_Telemetry_Streaming"
            }]
        else:
            endpoints = endpoints_array
        basic_config = {
            "ufm-telemetry-endpoint": endpoints,
            "fluentd-endpoint": {
                "host": fluent_host,
                "port": int(fluent_port)
            },
            "streaming": {
                "bulk_streaming": bulk_streaming,
                "compressed_streaming": compressed_streaming,
                "stream_only_new_samples": stream_only_new_samples,
                "c_fluent_streamer": c_fluent_streamer,
                "enabled": enabled
            }
        }
        if meta:
            basic_config["meta-field"] = meta
        return basic_config


    @staticmethod
    def validate_rest_body(self, msg, expected_ms):
        logging.info("Comparing %s ?= %s" % (msg, expected_ms))
        if msg == expected_ms:
            logging.info("Message is Expected")
        else:
            self.handleError("Message is not Expected")

    def verify_streaming(self, stream=False, bulk=False, not_bulk=False, meta=False, constants=False,info_labels=False):
        if not self.tag_msg:
            self.tag_msg = "UFM_Telemetry_Streaming"
        rc, stdout_before, stderr = general_utils.run_command_status("cat /tmp/tfs.log", self.fluent_host)
        logging.info(stdout_before)
        self.sleep(90)
        rc, stdout, stderr = general_utils.run_command_status("cat /tmp/tfs.log", self.fluent_host)
        logging.info(stdout)
        if info_labels:
            for msg in stdout.splitlines():
                if not self.tag_msg:
                    self.tag_msg = "UFM_Telemetry_Streaming"
                if self.tag_msg in msg:
                    for info_label in ["node_guid", "port_guid", "port_num", "node_description"]:
                        assert info_label in msg, f"Label {info_label} not found in {msg}"
            return True
        if stream:
            if not meta:
                assert stdout_before != stdout and self.tag_msg in stdout, "Streaming is not working"
            else:
                assert meta in stdout and constants in stdout, "Streaming with meta is not working"
        else:
            lines = stdout.splitlines()
            tele_lines = []
            for line in lines:
                if self.tag_msg in line:
                    tele_lines.append(line)
            condition = False
            if bulk:
                condition = len(tele_lines) <= 10
            if not_bulk:
                condition = len(tele_lines) > 10
            assert condition, "Streaming Bulk is not working as expected"

    def get_ipv6(self, ip):
        __, text, __ = general_utils.run_command_status("ip -6 addr | grep global", ip)
        return text.split("/")[0].split()[1]

    def sleep(self, second_to_sleep: float):
        time.sleep(second_to_sleep)

    def enable_ipv6_prometheus(self):
        general_utils.run_command_status("sed -i 's#http://0.0.0.0:9001#http://0:0:0:0:0:0:0:0:9001#g'"
                                       " /opt/ufm/files/conf/telemetry/launch_ibdiagnet_config.ini",
                                       self.ufm_server)
        self.sleep(90)

    def verify_streaming_with_conf(self, ip_protocol="ipv4", using_http_streamer=True, using_c_fluent_streamer=False):
        """
        Verify streaming with http protocol, or with forward python/c protocol using {ip_protocol}
        """
        self.set_conf(compressed_streaming=using_http_streamer, c_fluent_streamer=using_c_fluent_streamer)  
        # Forward protocol using Python forward library
        self.sleep(10)
        if ip_protocol == "ipv6":
            self.bind = "::"
        self.prepare_fluentd("forward", self.bind)
        self.run_fluentd()
        self.verify_streaming(stream=True)
