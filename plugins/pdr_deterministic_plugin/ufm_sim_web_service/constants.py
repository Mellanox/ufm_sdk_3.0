#
# Copyright © 2013-2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

import logging

class PDRConstants(object):

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
    AUTOMATIC_DEISOLATE = "AUTOMATIC_DEISOLATE"
    DO_DEISOLATION = "DO_DEISOLATION"
    TIMESTAMP = "timestamp"
    LAST_TIMESTAMP = "last_timestamp"
    CONFIGURED_TEMP_CHECK = "CONFIGURED_TEMP_CHECK"
    NO_DOWN_COUNT = "NO_DOWN_COUNT"
    ACCESS_ISOLATION = "ACCESS_ISOLATION"
    TEST_MODE = "TEST_MODE"
    TEST_MODE_PORT = 9090
    DYNAMIC_UNRESPONSIVE_LIMIT = "DYNAMIC_UNRESPONSIVE_LIMIT"
    
    GET_SESSION_DATA_REST = "/monitoring/session/0/data"
    POST_EVENT_REST = "/app/events/external_event"
    ISOLATION_REST = "/app/unhealthy_ports"
    GET_ISOLATED_PORTS = "/resources/isolated_ports"
    GET_PORTS_REST = "/resources/ports"
    GET_ACTIVE_PORTS_REST = "/resources/ports?active=true"
    API_HEALTHY_PORTS = "healthy_ports"
    API_ISOLATED_PORTS = "isolated_ports"
    DYNAMIC_SESSION_REST = "/app/telemetry/instances/%s"
    STATUS_DYNAMIC_SESSION_REST = "/app/telemetry/instances/status"

    EXTERNAL_EVENT_ERROR = 554
    EXTERNAL_EVENT_ALERT = 553
    EXTERNAL_EVENT_NOTICE = 552
    
    POST_METHOD = "POST"
    PUT_METHOD = "PUT"
    GET_METHOD = "GET"
    DELETE_METHOD = "DELETE"
    
    CONF_INTERNAL_PORT= "ufm_internal_port"
    UFM_HTTP_PORT = 8000
    CONF_USERNAME = 'admin'
    CONF_PASSWORD = 'password'

    TEMP_COUNTER = "CableInfo.Temperature"
    ERRORS_COUNTER = "errors"
    RCV_PACKETS_COUNTER = "PortRcvPktsExtended"
    RCV_ERRORS_COUNTER = "PortRcvErrorsExtended"
    RCV_REMOTE_PHY_ERROR_COUNTER = "PortRcvRemotePhysicalErrorsExtended"
    LNK_DOWNED_COUNTER = "LinkDownedCounterExtended"
    
    PHY_RAW_ERROR_LANE0 = "phy_raw_errors_lane0"
    PHY_RAW_ERROR_LANE1 = "phy_raw_errors_lane1"
    PHY_RAW_ERROR_LANE2 = "phy_raw_errors_lane2"
    PHY_RAW_ERROR_LANE3 = "phy_raw_errors_lane3"
    PHY_SYMBOL_ERROR = "phy_symbol_errors"
    
    SYMBOL_BER = "symbol_ber"
    ACTIVE_SPEED = "active_speed"
    WIDTH = "active_width"
    PORT_NAME = "name"
    DESCRIPTION = "description"
    EXTERNAL_NUMBER = "external_number"
    GUID = "guid"
    SYSTEM_ID = "systemID"
    PORT_NUM = "port_num"
    PEER = "peer"
    NODE_TYPE = "node_type"
    NODE_TYPE_COMPUTER = "computer"
    NODE_TYPE_OTHER = "other"
    BER_TELEMETRY = "ber_telemetry"

    ISSUE_PDR = "pdr"
    ISSUE_BER = "ber"
    ISSUE_PDR_BER = "pdr&ber"
    ISSUE_OONOC = "oonoc"
    ISSUE_INIT = "init"
    ISSUE_LINK_DOWN = "link_down"

    STATE_NORMAL = "normal"
    STATE_ISOLATED = "isolated"
    STATE_TREATED = "treated"

    PDR_DYNAMIC_NAME = "pdr_dynamic"
    # intervals in seconds for testing ber values and corresponding thresholds
    BER_THRESHOLDS_INTERVALS = [(125 * 60, 3), (12 * 60, 2.88)]