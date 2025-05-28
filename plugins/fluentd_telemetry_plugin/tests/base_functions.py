import time
import logging
import os
import shutil
import subprocess
import json
import requests
import signal
from typing import Tuple,List,Dict

CONFIG_FOLDER = "/config"
LOG_FOLDER = "/log"
DEFAULT_TELEMETRY_HOST = "127.0.0.1"
DEFAULT_TELEMETRY_URL = "csv/xcset/ib_basic_debug"
DEFAULT_TELEMETRY_PORT = "9007"
DEFAULT_FLUENT_HOST = "localhost"
DEFAULT_FLUENT_PORT = "24225"
DEFAULT_INTERVAL = "120"
DEFAULT_BULK_STREAMING = True
DEFAULT_STREAM_ONLY_NEW_SAMPLES = False
DEFAULT_COMPRESS_STREAMING = False
DEFAULT_C_FLUENT_STREAMING = True
DEFAULT_STREAMING_ENABLED = True
DEFAULT_META = False
DEFAULT_TAG_MSG = "UFM_Telemetry_Streaming"
DEFAULT_TELEMETRY_REQUEST_TIMEOUT = 60
DEFAULT_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL = True
DEFAULT_STREAM_INTERVAL = 10
BULKY_MSG_COUNT = 10
TFS_HTTP_PORT_REQUEST_TIMEOUT = 20

class BaseTestTfs:
    tele_host = "127.0.0.1"
    tele_url = "csv/metrics"
    tele_port = "9001"
    fluent_host = "127.0.0.1"
    fluent_port = "24225"
    interval = "10"
    bulk_streaming = False
    compressed_streaming = False
    stream_only_new_samples = False
    c_fluent_streamer = True
    enabled = True
    endpoints = None
    bind = '0.0.0.0'
    log_filename = LOG_FOLDER + "/tfs.log" # Log file location
    log_stream = LOG_FOLDER + "/tfs_stream.log" # Log stream location

    def __init__(self):
        self.ufm_server = None
        self.simulation_process = None
        self.server_process = None
        self.simulation_paths = None
        self.port=8981
        self.prepare_environment()
    
    def get_simulation_url(self) -> List[str]:
        return [f"http://127.0.0.1:9007/{endpoint_url}" for endpoint_url in self.simulation_paths]

    def run_simulation(self, rows=10, simulation_paths=None, max_changing=0, interval=1.0) -> bool:
        """start the simulation with 10 rows and one telemetry

        Args:
            rows (int, optional): number of rows in the simulation. Defaults to 10.
            simulation_paths (list, optional): names of the simulation. Defaults to None.

        Returns:
            bool: if successful return true
        """
        if self.simulation_process is not None:
            return False
        if simulation_paths is None:
            simulation_paths = ["/csv/metrics"]
        self.simulation_paths = simulation_paths
        current_directory = os.path.dirname(os.path.abspath(__file__))
        try:
            command = ["python","telemetry_simulation.py","--rows", rows, "--max_changing", max_changing,
                       "--update_interval",interval,"--paths"] + simulation_paths
            self.simulation_process = subprocess.Popen(command, cwd=current_directory,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            time.sleep(2)
            logging.info(f"running simulation on pid {self.simulation_process.pid}")
            return True
        except FileNotFoundError as e:
            logging.error(f"could not run this process due to {e}")
            logging.error(self.simulation_process.stderr.readlines())
            return False

    def run_server(self) -> int:
        """start the tfs server and return the pid of it

        Returns:
            int: pid of the server service, -1 if unsuccessful
        """
        if self.server_process is not None:
            return -1
        command = ["python","plugins/fluentd_telemetry_plugin/src/app.py"]
        current_script_path_abs = os.path.abspath(__file__)
        # we run the server from plugins folder, but we need to do popen to run in that folder,
        # To reach the absolute path for plugin folder, I take the path of here and go back 3 folders.
        # e.g ufm_sdk_3/plugins/fluentd_telemetry_plugin/tests/base_functions -> ufm_sdk_3/plugins.
        base_directory = current_script_path_abs
        for _ in range(3):
            base_directory = os.path.dirname(base_directory)
        try:
            self.server_process = subprocess.Popen(command,cwd=base_directory, text=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"Started a server with PID: {self.server_process.pid}")
            time.sleep(2)
            return self.server_process.pid
        except FileNotFoundError as error:
            logging.error(f"Failed to find app.py {error}, cwd {base_directory}")
            return -1
        except subprocess.SubprocessError as error:
            logging.error(f"An unspecified error occurred while trying to run server {error}")
            return -1

    def stop_simulation(self) -> None:
        """
        stop simulation if there is one, using sigkill
        """
        if self.simulation_process:
            os.kill(self.simulation_process.pid,signal.SIGKILL)

    def stop_server(self) -> None:
        """
        stop the server if there is one, using sigkill
        """
        if self.server_process:
            os.kill(self.server_process.pid,signal.SIGKILL)

    def prepare_environment(self) -> None:
        """prepare the environment for the fluent and run the fluentd
        """
        os.makedirs(CONFIG_FOLDER, exist_ok=True)
        os.makedirs(LOG_FOLDER, exist_ok=True)

        config_folder_src = os.path.basename(os.path.basename(__file__))+"/conf/"
        if os.path.exists(config_folder_src):
            for file_name in os.listdir(config_folder_src):
                source_file = os.path.join(config_folder_src, file_name)
                destination_filename = os.path.join(CONFIG_FOLDER, file_name)
                shutil.copy(source_file, destination_filename)

    def prepare_fluentd(self, protocol="forward", bind='0.0.0.0') -> None:
        """
        pull the fluend image and create the configuration for the fluent
        """
        self.stop_fluentd()
        os.makedirs("/tmp/fluentd", exist_ok=True)
        conf = f"""<source>
  @type {protocol}
  bind {str(bind)}
  port {self.fluent_port}
</source>
<match **>
  @type stdout
</match>"""
        with open("/config/fluentd.conf", 'x', encoding='utf-8') as conf_file:
            conf_file.write(conf)

    def run_fluentd(self) -> None:
        """
        Start the fluent container with the configuration and put the output in log.
        Remove the previous fluent log and create new empty one.
        """
        docker_image = "fluent/fluent:edge"
        try:
            if os.path.exists(self.log_filename):
                os.rename(self.log_filename, self.log_filename + time.strftime("%Y%m%d_%H%M%S") +".old") # remove previous log
            open(self.log_filename, 'a', encoding='utf-8').close() # create new log_file

            subprocess.run((f"docker run -i --rm --network host -v {CONFIG_FOLDER}:/fluentd/etc "+
                            f"{docker_image} -c /fluentd/etc/fluentd.conf").split(),
                            stdout=open(self.log_stream, "a", encoding="utf-8"),
                            stderr=subprocess.STDOUT, check=False)
            time.sleep(5)
            logging.info("fluentd container is running")
        except subprocess.CalledProcessError as error:
            logging.error(f"Error occurred while running fluentd docker container: {error}")

    def stop_fluentd(self) -> None:
        """
        stop and remove the fluentd container
        """
        try:
            subprocess.run("docker rm -f fluentd".split(), stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False)
        except subprocess.CalledProcessError as error:
            logging.error(f"Error occurred while stopping fluentd docker container: {error}")

    def set_conf_from_json(self, body:dict, extension:str="") -> Tuple[Dict, int]:
        """
        send a port request to the local tfs server, with possibility to run attribute configuration as well

        Args:
            body (dict): full body of what we are going to send
            extension (str, optional): extension to the url, if we want to send attributes. Defaults to "".

        Returns:
            tuple: the text and the status code from the request.
        """
        url = f'http://localhost:{self.port}/conf{extension}'
        response = requests.post(url, body=json.dumps(body),
                    headers={"Content-Type": "application/json"}, timeout=TFS_HTTP_PORT_REQUEST_TIMEOUT)
        return response.text, response.status_code

    def set_conf(self, compressed_streaming=False, c_fluent_streamer=True, meta=False) -> Tuple[Dict, int]:
        """
        modify the server configuration from the basic configuration.
        compressed_streaming True for using HTTP protocol / False for using Forward protocol
        c_fluent_streamer True for using C library / False for using python library
        """
        body = self.configure_body_conf(self.tele_host, self.tele_url, self.tele_port,
                    self.fluent_host, self.fluent_port, self.interval,
                    self.bulk_streaming, self.stream_only_new_samples, compressed_streaming,
                    c_fluent_streamer, self.enabled, meta, endpoints_array=self.endpoints)
        return self.set_conf_from_json(body)

    def get_conf(self,extension:str="") -> Tuple[Dict, int]:
        """
        get the configuration from the server
        """
        url = f'http://localhost:{self.port}/conf{extension}'
        response = requests.get(url, headers={"Content-Type": "application/json"}, timeout=20)
        return response.json(), response.status_code

    def configure_body_conf(self, change_dict:Dict[str, any], endpoints_array:List[Dict]=None) -> Dict:
        """
        create a body configuration using all the configuration options

        Args:
            tele_host (str, optional): telemetry host ip. Defaults to "127.0.0.1".
            tele_url (str, optional): telemetry url. Defaults to "csv/xcset/ib_basic_debug".
            tele_port (str, optional): telemetry port. Defaults to "9007".
            fluent_host (str, optional): fluent host ip. Defaults to "localhost".
            fluent_port (str, optional): fluent port. Defaults to "24225".
            interval (str, optional): interval to get the data. Defaults to "120".
            bulk_streaming (bool, optional): bulk streaming option. Defaults to True.
            stream_only_new_samples (bool, optional): stream only new samples. Defaults to False.
            compressed_streaming (bool, optional): is compressed streaming. Defaults to False.
            c_fluent_streamer (bool, optional): is using c fluent streamer. Defaults to True.
            enabled (bool, optional): is the streaming enabled. Defaults to True.
            meta (bool, optional): what is the meta data. Defaults to False.
            tag_msg (str, optional): what is the message_tag_name . Defaults to "UFM_Telemetry_Streaming".
            endpoints_array (_type_, optional): endpoint array that is put in the configuration. Defaults to None.

        Returns:
            dict: dict that can be send to the post conf as a body
        """
        if not endpoints_array:
            endpoints = [{
                "host": change_dict.get("host", DEFAULT_TELEMETRY_HOST),
                "url": change_dict.get("url", DEFAULT_TELEMETRY_URL),
                "interval": int(change_dict.get("interval", DEFAULT_INTERVAL)),
                "port": int(change_dict.get("port", DEFAULT_TELEMETRY_PORT)),
                "message_tag_name": change_dict.get("message_tag_name", DEFAULT_TAG_MSG),
            }]
        else:
            endpoints = endpoints_array
        basic_config = {
            "ufm-telemetry-endpoint": endpoints,
            "fluentd-endpoint": {
                "host": change_dict.get("fluent_host", DEFAULT_FLUENT_HOST),
                "port": int(change_dict.get("fluent_port", DEFAULT_FLUENT_PORT))
            },
            "streaming": {
                "bulk_streaming": change_dict.get("bulk_streaming", DEFAULT_BULK_STREAMING)  ,
                "compressed_streaming": change_dict.get("compressed_streaming", DEFAULT_COMPRESS_STREAMING),
                "stream_only_new_samples": change_dict.get("stream_only_new_samples", DEFAULT_STREAM_ONLY_NEW_SAMPLES),
                "c_fluent_streamer": change_dict.get("c_fluent_streamer", DEFAULT_C_FLUENT_STREAMING),
                "enable_cached_stream_on_telemetry_fail": change_dict.get("enable_cached_stream_on_telemetry_fail", DEFAULT_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL),
                "enabled": change_dict.get("enabled", DEFAULT_STREAMING_ENABLED),
                "telemetry_request_timeout": change_dict.get("telemetry_request_timeout", DEFAULT_TELEMETRY_REQUEST_TIMEOUT),
            }
        }
        if "meta" in change_dict:
            basic_config["meta-field"] = change_dict["meta"]
        return basic_config

    def read_data(self, get_last_line:bool=True, timestamp:str=None) -> str:
        """
        return the last line from the log file.

        Returns:
            str: last line from the log file
        """
        with open(self.log_stream, 'r', encoding='utf-8') as log_file:
            lines = log_file.read().splitlines()
            if get_last_line:
                line_to_return = lines[-1]
            elif timestamp:
                for line in lines:
                    if timestamp in line["timestamp"]:
                        line_to_return = line
                        break
        return line_to_return
    
    def extract_data_from_line(self, last_line) -> Dict:
        """
        return only the values from str
        """
        all_data = last_line.split('"values":')[1][:-1] # take the values and remove the } at the end.
        return json.load(all_data)

    def verify_streaming(self, stream=False, bulk=False, meta="", constants=False,
                         info_labels=False, tag_msg="UFM_Telemetry_Streaming") -> Tuple[bool, str]:
        """
        Verify the tfs telemetry streaming using the args. return True if successful, False otherwise.
        if the stream is True, it will verify that the data is streaming correctly. with the meta data if it is provided.
        if the info_labels is True, it will verify that the info labels are streaming correctly,
          including the node_guid, port_guid, port_num, node_description.

        This verify streaming only checks the last line in the stream,
        if you want to check the stream with a specific timestamp or other uses, use different function.

        Args:
            stream (bool, optional): Whether to verify continuous data streaming. Defaults to False.
            bulk (bool, optional): Whether to verify bulk data transmission. Defaults to False.
            meta (list, optional): List of metadata to verify in the streaming output. Defaults to [].
            constants (bool, optional): Whether to verify constant values in the streaming output. Defaults to False.
            info_labels (bool, optional): Whether to verify presence of information labels in the output. Defaults to False.
            tag_msg (str, optional): The message tag to look for in the streaming output. Defaults to "UFM_Telemetry_Streaming".

        Returns:
            Tuple[bool,str]: tuple of is Successful, error message
        """
        stdout_before = self.read_data(get_last_line=True)
        time.sleep(DEFAULT_STREAM_INTERVAL)
        stdout = self.read_data(get_last_line=True)
        if info_labels:
            tag_name_included = False
            for msg in stdout.splitlines():
                if tag_msg in msg:
                    tag_name_included = True
                    for info_label in ["node_guid", "port_guid", "port_num", "node_description"]:
                        if info_label not in msg:
                            return False, f"Label {info_label} not found in {msg}"
            if not tag_name_included:
                return False, f"the tag_msg {tag_msg} is not found in the logs."
            return True, ""
        if stream:
            if len(meta) == 0:
                stream_check = stdout_before != stdout and tag_msg in stdout
                if stream_check:
                    return True, ""
                return False, "Streaming is not working"
            meta_check = meta in stdout and constants in stdout
            if meta_check:
                return True, ""
            return False, "Streaming with meta is not working, meta data is not in the stream"
        lines = stdout.splitlines()
        tele_lines = []
        for line in lines:
            if tag_msg in line:
                tele_lines.append(line)
        is_bulky_msg = len(tele_lines) > BULKY_MSG_COUNT
        # check that if the bulk message is requested we get bulk message,
        # if it is not a bulk message is expecting to to have BULKY_MSG_COUNT lines
        if bulk:
            if is_bulky_msg:
                return True, ""
            return False, f"Streaming Bulk check is not working as expected, expected to have more than {BULKY_MSG_COUNT} lines, but got {len(tele_lines)} lines"
        if is_bulky_msg:
            return False, f"Streaming Bulk check is not working as expected, expected to have less than {BULKY_MSG_COUNT} lines, but got {len(tele_lines)} lines"
        return True, ""
