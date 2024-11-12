class UFMTelemetryConstants:
    """UFMTelemetryConstants Class"""

    PLUGIN_NAME = "UFM_Telemetry_Streaming"

    args_list = [
        {
            "name": '--ufm_telemetry_host',
            "help": "Host or IP of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_port',
            "help": "Port of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_url',
            "help": "URL of UFM Telemetry endpoint"
        },{
            "name": '--ufm_telemetry_xdr_mode',
            "help": "Telemetry XDR mode flag, "
                    "i.e., if True, the enabled ports types in `xdr_ports_types` "
                    "will be collected from the telemetry and streamed to fluentd"
        },{
            "name": '--ufm_telemetry_xdr_ports_types',
            "help": "Telemetry XDR ports types, "
                    "i.e., List of XDR ports types that should be collected and streamed, "
                    "separated by `;`. For example legacy;aggregated;plane"
        },{
            "name": '--streaming_interval',
            "help": "Interval for telemetry streaming in seconds"
        },{
            "name": '--bulk_streaming',
            "help": "Bulk streaming flag, i.e. if True all telemetry rows will be streamed in one message; "
                    "otherwise, each row will be streamed in a separated message"
        },{
            "name": '--compressed_streaming',
            "help": "Compressed streaming flag, i.e. if True the streamed data will be sent gzipped json; "
                    "otherwise, will be sent plain text as json"
        },{
            "name": '--c_fluent_streamer',
            "help": "C Fluent Streamer flag, i.e. if True the C fluent streamer will be used; "
                    "otherwise, the native python streamer will be used"
        },{
            "name": '--enable_streaming',
            "help": "If true, the streaming will be started once the required configurations have been set"
        },{
            "name": '--stream_only_new_samples',
            "help": "If True, the data will be streamed only in case new samples were pulled from the telemetry"
        },{
            "name": '--fluentd_host',
            "help": "Host name or IP of fluentd endpoint"
        },{
            "name": '--fluentd_port',
            "help": "Port of fluentd endpoint"
        },{
            "name": '--fluentd_timeout',
            "help": "Fluentd timeout in seconds"
        },{
            "name": '--fluentd_message_tag_name',
            "help": "Tag name of fluentd endpoint message"
        }
    ]

    CSV_LINE_SEPARATOR = "\n"
    CSV_ROW_ATTRS_SEPARATOR = ","
