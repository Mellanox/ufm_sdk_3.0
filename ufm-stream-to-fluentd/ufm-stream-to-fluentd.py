#
# Copyright (C) Mellanox Technologies Ltd. 2021.  ALL RIGHTS RESERVED.
#
# See file LICENSE for terms.

import logging
import os
import time
import datetime
import sys
from fluent import asyncsender as asycsender
try:
    from utils.utils import Utils
    from utils.ufm_rest_client import UfmRestClient, HTTPMethods, UfmProtocols
    from utils.args_parser import ArgsParser
    from utils.config_parser import ConfigParser, SDK_CONFIG_UFM_REMOTE_SECTION,SDK_CONFIG_UFM_REMOTE_SECTION_WS_PROTOCOL
    from utils.logger import Logger, LOG_LEVELS
    from utils.exception_handler import ExceptionHandler
except ModuleNotFoundError as e:
    print("Error occurred while importing python modules, "
          "Please make sure that you exported your repository to PYTHONPATH by running: "
          f'export PYTHONPATH="${{PYTHONPATH}}:{os.path.dirname(os.getcwd())}"')




global logs_file_name
global logs_level
global fluentd_metadata
global fluentd_host
global fluentd_port
global fluentd_timeout
global fluentd_message_tag_name
global ufm_host
global ufm_protocol
global ufm_username
global ufm_password
global args
global streaming_interval
global local_streaming
global streaming
global enabled_streaming_systems
global enabled_streaming_ports
global enabled_streaming_links
global enabled_streaming_alarms

stored_versioning_api = ''
stored_systems_api = []
stored_ports_api = []
stored_links_api = []
stored_alarms_api = []



def stream_to_fluentd():
    global fluentd_metadata
    try:
        current_time = int(time.time())
        message_id = fluentd_metadata.message_id + 1
        logging.info(f'Streaming to Fluentd IP: {fluentd_host} port: {fluentd_port} timeout: {fluentd_timeout}')
        fluent_sender = asycsender.FluentSender(UfmStreamingToFluentdConstants.PLUGIN_NAME,
                                                fluentd_host,
                                                fluentd_port,timeout=fluentd_timeout)
        fluentd_message = {
            "id": message_id,
            "timestamp": datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
            "type": "full"
        }
        if enabled_streaming_systems:
            fluentd_message["systems"] = {
                "systems_list": stored_systems_api
            }
        if enabled_streaming_ports:
            fluentd_message["ports"] = {
                "ports_list": stored_ports_api
            }
        if enabled_streaming_links:
            fluentd_message["links"] = {
                "links_list": stored_links_api
            }
        if enabled_streaming_alarms:
            fluentd_message["alarms"] = {
                "alarms_list": stored_alarms_api
            }
        fluent_sender.emit(fluentd_message_tag_name,fluentd_message)
        fluent_sender.close()
        fluentd_metadata.message_id = message_id
        fluentd_metadata.message_timestamp = current_time
        Utils.write_json_to_file(UfmStreamingToFluentdConstants.FLUENTD_METADATA_FILE, fluentd_metadata.__dict__)
        Logger.log_message(f'Finished Streaming to Fluentd Host: {fluentd_host} port: {fluentd_port}')
    except Exception as e:
        Logger.log_message(e, LOG_LEVELS.ERROR)


def load_fluentd_metadata_json():
    global fluentd_metadata
    logging.info(f'Call load_fluentd_metadata_json')
    if os.path.exists(UfmStreamingToFluentdConstants.FLUENTD_METADATA_FILE):
        fluentd_metadata_result = Utils.read_json_from_file(UfmStreamingToFluentdConstants.FLUENTD_METADATA_FILE)
        fluentd_metadata = FluentdMessageMetadata(fluentd_metadata_result['message_id'],
                                                  fluentd_metadata_result['message_timestamp'])
    else:
        fluentd_metadata = FluentdMessageMetadata()


def load_memory_with_jsons():
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api
    global stored_alarms_api

    try:
        logging.info(f'Call load_memory_with_jsons')

        if os.path.exists(UfmStreamingToFluentdConstants.UFM_API_VERSIONING_RESULT):
            stored_versioning_api = Utils.read_json_from_file(UfmStreamingToFluentdConstants.UFM_API_VERSIONING_RESULT)

        if os.path.exists(UfmStreamingToFluentdConstants.UFM_API_SYSTEMS_RESULT) and enabled_streaming_systems:
            stored_systems_api = Utils.read_json_from_file(UfmStreamingToFluentdConstants.UFM_API_SYSTEMS_RESULT)

        if os.path.exists(UfmStreamingToFluentdConstants.UFM_API_PORTS_RESULT) and enabled_streaming_ports:
            stored_ports_api = Utils.read_json_from_file(UfmStreamingToFluentdConstants.UFM_API_PORTS_RESULT)

        if os.path.exists(UfmStreamingToFluentdConstants.UFM_API_LINKS_RESULT) and enabled_streaming_links:
            stored_links_api = Utils.read_json_from_file(UfmStreamingToFluentdConstants.UFM_API_LINKS_RESULT)

        if os.path.exists(UfmStreamingToFluentdConstants.UFM_API_ALARMS_RESULT) and enabled_streaming_alarms:
            stored_alarms_api = Utils.read_json_from_file(UfmStreamingToFluentdConstants.UFM_API_ALARMS_RESULT)

    except Exception as e:
        Logger.log_message(e, LOG_LEVELS.ERROR)


def load_ufm_versioning_api():
    return ufm_rest_client.send_request(UfmStreamingToFluentdConstants.UFM_API_VERSIONING).json()


def update_ufm_apis(ufm_new_version):
    global stored_versioning_api
    global stored_systems_api
    global stored_ports_api
    global stored_links_api
    global stored_alarms_api

    try:
        logging.info(f'Call update_ufm_apis')

        # check if systems api is changed
        if enabled_streaming_systems and \
                (stored_versioning_api == '' or
                 ufm_new_version["switches_version"] != stored_versioning_api["switches_version"]):
            stored_systems_api = ufm_rest_client.send_request(UfmStreamingToFluentdConstants.UFM_API_SYSTEMS).json()
            Utils.write_json_to_file(UfmStreamingToFluentdConstants.UFM_API_SYSTEMS_RESULT, stored_systems_api)

        # check if ports api is changed
        if enabled_streaming_ports and \
                (stored_versioning_api == '' or
                 ufm_new_version["ports_version"] != stored_versioning_api["ports_version"]):
            stored_ports_api = ufm_rest_client.send_request(UfmStreamingToFluentdConstants.UFM_API_PORTS).json()
            Utils.write_json_to_file(UfmStreamingToFluentdConstants.UFM_API_PORTS_RESULT, stored_ports_api)

        # check if links api is changed
        if enabled_streaming_links and \
                (stored_versioning_api == '' or
                 ufm_new_version["links_version"] != stored_versioning_api["links_version"]):
            stored_links_api = ufm_rest_client.send_request(UfmStreamingToFluentdConstants.UFM_API_LINKS).json()
            Utils.write_json_to_file(UfmStreamingToFluentdConstants.UFM_API_LINKS_RESULT, stored_links_api)

        # check if alarms api is changed
        if enabled_streaming_alarms and \
                (stored_versioning_api == '' or
                 ufm_new_version["alarms_version"] != stored_versioning_api["alarms_version"]):
            stored_alarms_api = ufm_rest_client.send_request(UfmStreamingToFluentdConstants.UFM_API_ALARMS).json()
            Utils.write_json_to_file(UfmStreamingToFluentdConstants.UFM_API_ALARMS_RESULT, stored_alarms_api)

        stored_versioning_api = ufm_new_version
        Utils.write_json_to_file(UfmStreamingToFluentdConstants.UFM_API_VERSIONING_RESULT, stored_versioning_api)
    except Exception as e:
        Logger.log_message(e, LOG_LEVELS.ERROR)


class UfmStreamingToFluentdConstants:

    PLUGIN_NAME = "UFM_API_Streaming"
    CONFIG_FILE = 'ufm-stream-to-fluentd.cfg'
    FLUENTD_METADATA_FILE = 'fluentd_metadata.json'
    UFM_API_VERSIONING = 'app/versioning'
    UFM_API_VERSIONING_RESULT = 'api_results/versioning.json'
    UFM_API_SYSTEMS = 'resources/systems'
    UFM_API_SYSTEMS_RESULT = 'api_results/systems.json'
    UFM_API_PORTS = 'resources/ports'
    UFM_API_PORTS_RESULT = 'api_results/ports.json'
    UFM_API_LINKS = 'resources/links'
    UFM_API_LINKS_RESULT = 'api_results/links.json'
    UFM_API_ALARMS = 'app/alarms'
    UFM_API_ALARMS_RESULT = 'api_results/alarms.json'

    FLUENTD_HOST = "fluentd_host"
    FLUENTD_PORT = "fluentd_port"
    FLUENTD_TIMEOUT = "fluentd_timeout"
    FLUENTD_MESSAGE_TAG_NAME = "fluentd_message_tag_name"
    LOCAL_STREAMING = "local_streaming"
    STREAMING = "streaming"
    STREAMING_INTERVAL = 'streaming_interval'
    STREAMING_SYSTEMS = 'streaming_systems'
    STREAMING_PORTS = 'streaming_ports'
    STREAMING_ALARMS = 'streaming_alarms'
    STREAMING_LINKS = 'streaming_links'
    UFM_STREAMING_TO_FLUENTD = "ufm streaming to fluentd"

    args_list = [
        {
            "name": f'--{FLUENTD_HOST}',
            "help": "Host name or IP of fluentd endpoint",
        },
        {
            "name": f'--{FLUENTD_PORT}',
            "help": "Port of fluentd endpoint"
        },
        {
            "name": f'--{FLUENTD_TIMEOUT}',
            "help": "Fluentd timeout in seconds",
        },
        {
            "name": f'--{FLUENTD_MESSAGE_TAG_NAME}',
            "help": "Tag name of fluentd endpoint message"
        },
        {
            "name": f'--{LOCAL_STREAMING}',
            "help": "Enable/Disable local streaming [True|False]"
        },
        {
            "name": f'--{STREAMING}',
            "help": "Enable/Disable streaming [True|False]"
        },
        {
            "name": f'--{STREAMING_INTERVAL}',
            "help": "Streaming interval in minutes [Default is 5 minutes]",
        },
        {
            "name": f'--{STREAMING_SYSTEMS}',
            "help": "Enable/Disable streaming systems API [True|False]"
        },
        {
            "name": f'--{STREAMING_PORTS}',
            "help": "Enable/Disable streaming ports API [True|False]"
        },
        {
            "name": f'--{STREAMING_ALARMS}',
            "help": "Enable/Disable streaming alarms API [True|False]",
        },
        {
            "name": f'--{STREAMING_LINKS}',
            "help": "Enable/Disable streaming links API [True|False]"
        }
    ]


class UfmStreamingToFluentdConfigParser(ConfigParser):
    config_file = "ufm-stream-to-fluentd.cfg"
    UFM_FLUENTD_CONFIG_SECTION = "fluentd-config"
    UFM_STREAMING_CONFIG_SECTION = "streaming-config"
    UFM_FLUENTD_CONFIG_SECTION_HOST = "host"
    UFM_FLUENTD_CONFIG_SECTION_PORT = "port"
    UFM_FLUENTD_CONFIG_SECTION_TIMEOUT = "timeout"
    UFM_FLUENTD_CONFIG_SECTION_TAG_NAME = "message_tag_name"
    UFM_STREAMING_CONFIG_SECTION_LOCAL_STREAMING = "local_streaming"
    UFM_STREAMING_CONFIG_SECTION_INTERVAL = "interval"
    UFM_STREAMING_CONFIG_SECTION_STREAMING = "streaming"
    UFM_STREAMING_CONFIG_SECTION_SYSTEMS = "systems"
    UFM_STREAMING_CONFIG_SECTION_LINKS = "links"
    UFM_STREAMING_CONFIG_SECTION_PORTS = "ports"
    UFM_STREAMING_CONFIG_SECTION_ALARMS = "alarms"


    def __init__(self,args):
        super().__init__(args)
        self.sdk_config.read(self.config_file)
        self.args_dict = self.args.__dict__

    def get_fluentd_host(self):
        return self.get_config_value(self.args_dict.get(UfmStreamingToFluentdConstants.FLUENTD_HOST),
                                     self.UFM_FLUENTD_CONFIG_SECTION, self.UFM_FLUENTD_CONFIG_SECTION_HOST, None)
    def get_fluentd_port(self):
        return self.safe_get_int(self.args_dict.get(UfmStreamingToFluentdConstants.FLUENTD_PORT),
                                     self.UFM_FLUENTD_CONFIG_SECTION, self.UFM_FLUENTD_CONFIG_SECTION_PORT, None)
    def get_fluentd_timeout(self):
        return self.safe_get_int(self.args_dict.get(UfmStreamingToFluentdConstants.FLUENTD_TIMEOUT),
                                     self.UFM_FLUENTD_CONFIG_SECTION, self.UFM_FLUENTD_CONFIG_SECTION_TIMEOUT, 120)

    def get_local_streaming(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.LOCAL_STREAMING),
                                  self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_LOCAL_STREAMING, 'True')

    def get_fluentd_message_tag_name(self):
        return self.get_config_value(self.args_dict.get(UfmStreamingToFluentdConstants.FLUENTD_MESSAGE_TAG_NAME),
                                  self.UFM_FLUENTD_CONFIG_SECTION, self.UFM_FLUENTD_CONFIG_SECTION_TAG_NAME, self.get_ufm_host())

    def get_streaming_interval(self):
        return self.safe_get_int(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING_INTERVAL),
                                     self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_INTERVAL, 5)
    def get_streaming(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING),
                                     self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_STREAMING, 'True')

    def get_enabled_streaming_systems(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING_SYSTEMS),
                                     self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_SYSTEMS, 'True')

    def get_enabled_streaming_ports(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING_PORTS),
                                      self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_PORTS, 'True')

    def get_enabled_streaming_links(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING_LINKS),
                                      self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_LINKS, 'True')

    def get_enabled_streaming_alarms(self):
        return self.safe_get_bool(self.args_dict.get(UfmStreamingToFluentdConstants.STREAMING_ALARMS),
                                   self.UFM_STREAMING_CONFIG_SECTION, self.UFM_STREAMING_CONFIG_SECTION_ALARMS, 'True')

    def get_ufm_protocol(self):
        return self.get_config_value(self.args.ufm_protocol,
                                     SDK_CONFIG_UFM_REMOTE_SECTION,
                                     SDK_CONFIG_UFM_REMOTE_SECTION_WS_PROTOCOL,
                                     UfmProtocols.http.value if local_streaming else UfmProtocols.https.value)


def init_app_params():
    global fluentd_host
    global fluentd_port
    global fluentd_timeout
    global fluentd_message_tag_name
    global ufm_host
    global ufm_protocol
    global ufm_username
    global ufm_password
    global local_streaming
    global streaming
    global streaming_interval
    global enabled_streaming_systems
    global enabled_streaming_ports
    global enabled_streaming_links
    global enabled_streaming_alarms
    try:
        fluentd_host = config_parser.get_fluentd_host()
        fluentd_port = config_parser.get_fluentd_port()
        fluentd_timeout = config_parser.get_fluentd_timeout()
        local_streaming = config_parser.get_local_streaming()
        ufm_host = config_parser.get_ufm_host()
        fluentd_message_tag_name = config_parser.get_fluentd_message_tag_name()
        ufm_protocol = config_parser.get_ufm_protocol()
        ufm_username = config_parser.get_ufm_username()
        ufm_password = config_parser.get_ufm_password()
        streaming_interval = config_parser.get_streaming_interval()
        streaming = config_parser.get_streaming()
        enabled_streaming_systems = config_parser.get_enabled_streaming_systems()
        enabled_streaming_ports =  config_parser.get_enabled_streaming_ports()
        enabled_streaming_links =  config_parser.get_enabled_streaming_links()
        enabled_streaming_alarms =  config_parser.get_enabled_streaming_alarms()
    except ValueError as e:
        ExceptionHandler.handel_arg_exception(UfmStreamingToFluentdConstants.UFM_STREAMING_TO_FLUENTD,
                                              UfmStreamingToFluentdConstants.FLUENTD_HOST,
                                              UfmStreamingToFluentdConstants.FLUENTD_PORT,
                                              supported_in_config=True)


class FluentdMessageMetadata:
    def __init__(self, message_id=0, message_timestamp=None):
        self.message_id = message_id
        self.message_timestamp = message_timestamp

    def get_message_id(self):
        return self.message_id

    def set_message_id(self, message_id):
        self.message_id = message_id

    def get_message_timestamp(self):
        return self.message_timestamp

    def set_message_timestamp(self, message_timestamp):
        self.message_timestamp = message_timestamp


def streaming_interval_is_valid():
    if fluentd_metadata and fluentd_metadata.message_timestamp:
        # The timestamp of the last message sent exists => check if it larger than the configurable streaming interval
        time_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(fluentd_metadata.message_timestamp)
        streaming_interval_in_seconds = streaming_interval * 60
        return time_delta.total_seconds() >= streaming_interval_in_seconds
    return True


# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        args = ArgsParser.parse_args('Streams UFM API to fluentD', UfmStreamingToFluentdConstants.args_list)

        # init app config parser & load config files
        config_parser = UfmStreamingToFluentdConfigParser(args)

        # init logs configs
        logs_file_name = config_parser.get_logs_file_name()
        logs_level = config_parser.get_logs_level()
        Logger.init_logs_config(logs_file_name, logs_level)

        # init app parameters
        init_app_params()

        # init ufm rest client
        ufm_rest_client = UfmRestClient(host=config_parser.get_ufm_host(),
                                        client_token=config_parser.get_ufm_access_token(),
                                        username=config_parser.get_ufm_username(),
                                        password=config_parser.get_ufm_password(),
                                        ws_protocol=config_parser.get_ufm_protocol())

        if not streaming:
            Logger.log_message("Streaming flag is disabled, please enable it from the configurations",LOG_LEVELS.WARNING)
            sys.exit()

        load_fluentd_metadata_json()
        if streaming_interval_is_valid():
            ufm_new_version = load_ufm_versioning_api()
            if ufm_new_version is None:
                sys.exit()
            load_memory_with_jsons()
            update_ufm_apis(ufm_new_version)
            stream_to_fluentd()
        else:
            Logger.log_message("Streaming interval isn't completed",LOG_LEVELS.ERROR)

    except Exception as global_ex:
        Logger.log_message(global_ex, LOG_LEVELS.ERROR)
