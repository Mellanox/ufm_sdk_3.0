import logging

class PDRConstants:
    CONF_FILE = "/config/pdr_deterministic.conf"
    LOG_FILE = '/log/pdr_deterministic_plugin.log'
    log_level = logging.INFO
    log_file_backup_count = 5
    log_file_max_size = 100 * 100 * 1024
    
    CONF_COMMON = "Common"
    T_ISOLATE = "T_ISOLATE"
    MAX_NUM_ISOLATE = "MAX_NUM_ISOLATE"
    TMAX = "TMAX"
    D_TMAX = "D_TMAX"
    MAX_PDR = "MAX_PDR"
    MAX_BER = "MAX_BER"
    CONFIGURED_BER_CHECK = "CONFIGURED_BER_CHECK"
    DRY_RUN = "DRY_RUN"
    DEISOLATE_CONSIDER_TIME = "DEISOLATE_CONSIDER_TIME"
    
    GET_SESSION_DATA_REST = "/monitoring/session/0/data"
    POST_EVENT_REST = "/app/events/external_event"
    ISOLATION_REST = "/app/unhealthy_ports"
    GET_ISOLATED_PORTS = "/resources/isolated_ports"

    POST_METHOD = "POST"
    PUT_METHOD = "PUT"
    GET_METHOD = "GET"
    
    CONF_INTERNAL_PORT= "ufm_internal_port"
    UFM_HTTP_PORT = 8000
    CONF_USERNAME = 'admin'
    CONF_PASSWORD = 'password'

    TEMP_COUNTER = "cable_temperature"
    ERRORS_COUNTER = "errors"
    RCV_PACKETS_COUNTER = "Infiniband_PckIn"
    RCV_ERRORS_COUNTER = "Infiniband_RcvErrors"
    RCV_REMOTE_PHY_ERROR_COUNTER = "Infiniband_RcvRemotePhysErrors"
    SYMBOL_BER = "symbol_ber"
    
    ISSUE_PDR = "pdr"
    ISSUE_BER = "ber"
    ISSUE_PDR_BER = "pdr&ber"
    ISSUE_OONOC = "oonoc"
    ISSUE_INIT = "init"

    STATE_NORMAL = "normal"
    STATE_ISOLATED = "isolated"
    STATE_TREATED = "treated"

    
