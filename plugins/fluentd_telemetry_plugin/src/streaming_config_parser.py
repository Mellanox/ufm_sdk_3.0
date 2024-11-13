# pylint: disable=no-name-in-module,import-error
import logging
from utils.config_parser import ConfigParser

class UFMTelemetryStreamingConfigParser(ConfigParser):
    """
    UFMTelemetryStreamingConfigParser class to manage
    the TFS configurations
    """

    # for debugging
    # config_file = "../conf/fluentd_telemetry_plugin.cfg"

    config_file = "/config/fluentd_telemetry_plugin.cfg" # this path on the docker

    UFM_TELEMETRY_ENDPOINT_SECTION = "ufm-telemetry-endpoint"
    UFM_TELEMETRY_ENDPOINT_SECTION_HOST = "host"
    UFM_TELEMETRY_ENDPOINT_SECTION_PORT = "port"
    UFM_TELEMETRY_ENDPOINT_SECTION_URL = "url"
    UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL = "interval"
    UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME = "message_tag_name"
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE = "xdr_mode"
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE = "xdr_ports_types"
    UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE_SPLITTER = ";"

    FLUENTD_ENDPOINT_SECTION = "fluentd-endpoint"
    FLUENTD_ENDPOINT_SECTION_HOST = "host"
    FLUENTD_ENDPOINT_SECTION_PORT = "port"
    FLUENTD_ENDPOINT_SECTION_TIMEOUT = "timeout"

    STREAMING_SECTION = "streaming"
    STREAMING_SECTION_COMPRESSED_STREAMING = "compressed_streaming"
    STREAMING_SECTION_C_FLUENT__STREAMER = "c_fluent_streamer"
    STREAMING_SECTION_BULK_STREAMING = "bulk_streaming"
    STREAMING_SECTION_STREAM_ONLY_NEW_SAMPLES = "stream_only_new_samples"
    STREAMING_SECTION_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL = "enable_cached_stream_on_telemetry_fail"
    STREAMING_SECTION_ENABLED = "enabled"

    META_FIELDS_SECTION = "meta-fields"

    def __init__(self, args=None):
        super().__init__(args, False)
        self.sdk_config.read(self.config_file)

    def get_telemetry_host(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_HOST)

    def get_telemetry_port(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_PORT,
                                     '9001')

    def get_telemetry_url(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_URL,
                                     "csv/metrics")

    def get_ufm_telemetry_xdr_mode_flag(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_MODE,
                                     "False")

    def get_ufm_telemetry_xdr_ports_types(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_XDR_PORTS_TYPE,
                                     "legacy;aggregated;plane")

    def get_streaming_interval(self):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_INTERVAL,
                                     '10')

    def get_bulk_streaming_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_BULK_STREAMING,
                                  True)

    def get_compressed_streaming_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_COMPRESSED_STREAMING,
                                  True)

    def get_c_fluent_streamer_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_C_FLUENT__STREAMER,
                                  True)

    def get_stream_only_new_samples_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_STREAM_ONLY_NEW_SAMPLES,
                                  True)

    def get_enable_cached_stream_on_telemetry_fail(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLE_CACHED_STREAM_ON_TELEMETRY_FAIL,
                                  True)

    def get_enable_streaming_flag(self):
        return self.safe_get_bool(None,
                                  self.STREAMING_SECTION,
                                  self.STREAMING_SECTION_ENABLED,
                                  False)

    def get_fluentd_host(self):
        return self.get_config_value(None,
                                     self.FLUENTD_ENDPOINT_SECTION,
                                     self.FLUENTD_ENDPOINT_SECTION_HOST)

    def get_fluentd_port(self):
        return self.safe_get_int(None,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_PORT)

    def get_fluentd_timeout(self):
        return self.safe_get_int(None,
                                 self.FLUENTD_ENDPOINT_SECTION,
                                 self.FLUENTD_ENDPOINT_SECTION_TIMEOUT,
                                 120)

    def get_fluentd_msg_tag(self, default=''):
        return self.get_config_value(None,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION,
                                     self.UFM_TELEMETRY_ENDPOINT_SECTION_MSG_TAG_NAME,
                                     default)

    def get_meta_fields(self):
        meta_fields_list = self.get_section_items(self.META_FIELDS_SECTION)
        aliases = []
        custom = []
        for meta_field,value in meta_fields_list:
            meta_fields_parts = meta_field.split("_")
            meta_field_type = meta_fields_parts[0]
            meta_field_key = "_".join(meta_fields_parts[1:])
            if meta_field_type == "alias":
                aliases.append({
                    "key": meta_field_key,
                    "value": value
                })
            elif meta_field_type == "add":
                custom.append({
                    "key": meta_field_key,
                    "value": value
                })
            else:
                logging.warning("The meta field type : %s is not from the supported types list [alias, add]",
                                meta_field_type)
        return aliases, custom
