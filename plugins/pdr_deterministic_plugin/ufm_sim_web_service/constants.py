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
    BER_MATRIX = "/config/Field_BER_Thresholds.csv"
    FEC_LOOKUP = "/config/fec_mode_lookup.json"
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
    
    GET_SESSION_DATA_REST = "/monitoring/session/0/data"
    POST_EVENT_REST = "/app/events/external_event"
    ISOLATION_REST = "/app/unhealthy_ports"
    GET_ISOLATED_PORTS = "/resources/isolated_ports"
    GET_PORTS_REST = "/resources/ports"
    GET_ACTIVE_PORTS_REST = "/resources/ports?active=true"
    API_HEALTHY_PORTS = "healthy_ports"
    API_ISOLATED_PORTS = "isolated_ports"

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
    
    PHY_RAW_ERROR_LANE0 = "phy_raw_errors_lane0"
    PHY_RAW_ERROR_LANE1 = "phy_raw_errors_lane1"
    PHY_RAW_ERROR_LANE2 = "phy_raw_errors_lane2"
    PHY_RAW_ERROR_LANE3 = "phy_raw_errors_lane3"
    PHY_EFF_ERROR = "phy_effective_errors"
    PHY_SYMBOL_ERROR = "phy_symbol_errors"
    
    SYMBOL_BER = "symbol_ber"
    EFF_BER = "eff_ber"
    RAW_BER = "raw_ber"
    ACTIVE_SPEED = "active_speed"
    ASIC = "asic"
    HW_TECHNOLOGY = "hw_technology"
    WIDTH = "active_width"
    FEC_MODE = "fec_mode_active"
    PORT_NAME = "name"
    
    ISSUE_PDR = "pdr"
    ISSUE_BER = "ber"
    ISSUE_PDR_BER = "pdr&ber"
    ISSUE_OONOC = "oonoc"
    ISSUE_INIT = "init"

    STATE_NORMAL = "normal"
    STATE_ISOLATED = "isolated"
    STATE_TREATED = "treated"

    CSV_FEC_OPCODE = "FEC OPCODE"
    CSV_ASIC = "ASIC"
    CSV_RAW_BER_ISOLATE = "Pre-FEC BER Error"
    CSV_EFF_BER_ISOLATE = "Post-FEC BER Error"
    CSV_SYMBOL_BER_ISOLATE = "Symbol BER Error"
    CSV_RAW_BER_DEISOLATE = "Pre-FEC BER Normal"
    CSV_EFF_BER_DEISOLATE = "Post-FEC BER Normal"
    CSV_SYMBOL_BER_DEISOLATE = "Symbol BER Normal"