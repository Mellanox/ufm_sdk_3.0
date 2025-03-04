import time
import logging
import os
import shutil
import subprocess
import json
import requests
import signal
from typing import Tuple,List,Dict

from ufm_sdk_tools.src.general_utils import general_utils


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
    log_filename = "/log/tfs.log" # Log file location

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
            simulation_paths (list, optional): names of the simulation. Defaults to [].

        Returns:
            bool: iff successful return true
        """
        if self.simulation_process is not None:
            return False
        if simulation_paths is None:
            simulation_paths = ["/csv/metrics"]
        self.simulation_paths = simulation_paths
        current_directory = os.path.dirname(os.path.abspath(__file__))
        try:
            command = ["python","telemetry_simulation.py","--rows",rows,"--max_changing",max_changing,
                       "--update_interval",interval,"--paths"]+simulation_paths
            self.simulation_process = subprocess.Popen(command, cwd=current_directory,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            time.sleep(2)
            print(f"running simulation on pid {self.simulation_process.pid}")
            return True
        except FileNotFoundError as e:
            print(f"could not run this process due to {e}")
            print(self.simulation_process.stderr.readlines())
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
        base_directory = current_script_path_abs
        for _ in range(3):
            base_directory = os.path.dirname(base_directory)
        try:
            self.server_process = subprocess.Popen(command,cwd=base_directory, text=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Started a server with PID: {self.server_process.pid}")
            time.sleep(2)
            return self.server_process.pid
        except FileNotFoundError as error:
            print(f"Failed to find app.py {error}, cwd {base_directory}")
            return -1
        except subprocess.SubprocessError as error:
            print(f"An unspecified error occurred while trying to run server {error}")
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
        config_folder = "/config"
        os.makedirs(config_folder, exist_ok=True)
        os.makedirs("/log", exist_ok=True)

        config_folder_src = os.path.basename(os.path.basename(__file__))+"/conf/"
        if os.path.exists(config_folder_src):
            for file_name in os.listdir(config_folder_src):
                source_file = os.path.join(config_folder_src, file_name)
                destination_filename = os.path.join(config_folder,file_name)
                shutil.copy(source_file, destination_filename)


    def prepare_fluentd(self, protocol="forward", bind='0.0.0.0') -> None:
        """
        pull the fluend image and create the configuration for the fluent
        """
        self.stop_fluentd()
        os.makedirs("/tmp/fluentd",exist_ok=True)
        conf = f"""<source>
  @type {protocol}
  bind {str(bind)}
  port {self.fluent_port}
</source>
<match **>
  @type stdout
</match>"""
        general_utils.write_to_file('fluentd.conf', conf, "localhost", "/config/fluentd.conf")

    def run_fluentd(self)->None:
        """
        Start the fluent container with the configuration and put the output in log.
        Remove the previous fluent log and create new empty one.
        """
        docker_image = "fluent/fluent:edge"
        config_folder = "/config"
        try:
            if os.path.exists(self.log_filename):
                os.remove(self.log_filename) # remove previous log
            open(self.log_filename,'a',encoding='utf-8').close() # create new log_file

            subprocess.run((f"docker run -i --rm --network host -v {config_folder}:/fluentd/etc "+
                            f"{docker_image} -c /fluentd/etc/fluentd.conf").split(),
                            stdout=open(self.log_filename,"a",encoding="utf-8"),
                            stderr=subprocess.STDOUT,check=False)
            time.sleep(5)
            print("fluentd container is running")
        except subprocess.CalledProcessError as error:
            print(f"Error occurred while running fluentd docker container: {error}")

    def stop_fluentd(self) -> None:
        """
        stop and remove the fluentd container
        """
        try:
            subprocess.run("docker rm -f fluentd".split(),stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,check=False)
        except subprocess.CalledProcessError as error:
            print(f"Error occurred while stopping fluentd docker container: {error}")

    def set_conf_from_json(self,body:dict,extension:str="") -> Tuple[Dict,int]:
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
                    headers={"Content-Type": "application/json"},timeout=20)
        return response.text, response.status_code

    def set_conf(self, compressed_streaming=False, c_fluent_streamer=True, meta=False) -> Tuple[Dict,int]:
        """
        modify the server configuration from the basic configuration.
        compressed_streaming True for using HTTP protocol / False for using Forward protocol
        c_fluent_streamer True for using C library / False for using python library
        """
        body = BaseTestTfs.configure_body_conf(self.tele_host, self.tele_url, self.tele_port,
                    self.fluent_host, self.fluent_port, self.interval,
                    self.bulk_streaming, self.stream_only_new_samples, compressed_streaming,
                    c_fluent_streamer, self.enabled, meta, endpoints_array=self.endpoints)
        return self.set_conf_from_json(body)

    def get_conf(self,extension:str="") -> Tuple[Dict,int]:
        """
        get the configuration from the server
        """
        url = f'http://localhost:{self.port}/conf{extension}'
        response = requests.get(url, headers={"Content-Type": "application/json"},timeout=20)
        return response.json(), response.status_code

    @staticmethod
    def configure_body_conf(tele_host="127.0.0.1", tele_url="csv/xcset/ib_basic_debug", tele_port="9007",
                           fluent_host="localhost", fluent_port="24225", interval="120",
                           bulk_streaming=True, stream_only_new_samples=False, compressed_streaming=False, c_fluent_streamer=True, enabled=True,
                           meta=False, tag_msg="UFM_Telemetry_Streaming",
                           endpoints_array=None) -> Dict:
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
                "host": tele_host,
                "url": tele_url,
                "interval": int(interval),
                "port": int(tele_port),
                "message_tag_name": tag_msg,
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
                "enable_cached_stream_on_telemetry_fail": True,
                "enabled": enabled,
                "telemetry_request_timeout": 60,
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

    def read_data(self):
        with open(self.log_filename,'r',encoding='utf-8') as log_file:
            lines = log_file.read().splitlines()
            last_line = lines[-1]
        return last_line
    
    def extract_data_from_line(self,last_line):
        all_data = last_line.split('"values":')[1][:-1] # take the values and remove the } at the end.
        return json.load(all_data)

    def verify_streaming(self, stream=False, bulk=False, meta=False, constants=False,
                         info_labels=False, tag_msg="UFM_Telemetry_Streaming") -> Tuple[bool,str]:
        """
        Verify the tfs telemetry streaming using the args.

        Args:
            stream (bool, optional): Is checking the stream data. Defaults to False.
            bulk (bool, optional): Is the data bulk. Defaults to False.
            meta (bool, optional): what the meta data that we check. Defaults to False.
            constants (bool, optional): what the constants data that we check. Defaults to False.
            info_labels (bool, optional): Is checking the info_labels data. Defaults to False.
            tag_msg (str, optional): what the tag msg we checking on. Defaults to "UFM_Telemetry_Streaming".

        Returns:
            Tuple[bool,str]: tuple of is Successful, error message
        """
        stdout_before = self.read_data()
        time.sleep(10)
        stdout = self.read_data()
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
            if not meta:
                return stdout_before != stdout and tag_msg in stdout, "Streaming is not working"
            return meta in stdout and constants in stdout, "Streaming with meta is not working"
        lines = stdout.splitlines()
        tele_lines = []
        for line in lines:
            if tag_msg in line:
                tele_lines.append(line)
        bulky_msg = len(tele_lines) > 10
        # check that if the bulk message is requested we get bulk message,
        # if it is not a bulk message is expecting to to have 10 lines
        return bulky_msg == bulk, f"Streaming Bulk check {bulk} is not working as expected {bulky_msg}"
