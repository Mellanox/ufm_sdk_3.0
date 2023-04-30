#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (C) 2023 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
import os
import logging
import subprocess
import time
import json
from datetime import datetime
import csv
import pandas as pd
from topo_diff.topo_diff import parse_ndt_port, PortType, parse_ibdiagnet_dump


DEFAULT_IBDIAGNET_OUTPUT_PATH = "/var/tmp/ibdiagnet2"
DEFAULT_IBDIAGNET_NET_DUMP_PATH = "/var/tmp/ibdiagnet2/ibdiagnet2.net_dump"
IBDIAGNET_TARBALL_LOCATION_PATH = "/tmp/ibdiagnet"
IBDIAGNET_TARBALL_FILE_PREFIX = "ibdignet_output"
TOPOCONFIG_DIRECTORY = "/config/topoconfig"
IBDIAGNET_OUT_DIRECTORY = "/tmp/ndt_plugin"
IBDIAGNET_LOG_FILE = "%s/%s" % (IBDIAGNET_OUT_DIRECTORY, "ibdiagnet2.log")
IBDIAGNET_COMMAND = "ibdiagnet -o %s --enable_switch_dup_guid --skip dup_node_desc,lids,sm,nodes_info,pkey,pm,temp_sensing,virt" % IBDIAGNET_OUT_DIRECTORY
IBDIAGNET_PORT_VERIFICATION_COMMAND = "ibdiagnet -o %s --discovery_only" % IBDIAGNET_OUT_DIRECTORY
CHECK_DUPLICATED_GUIDS_COMMAND = "cat %s | grep \"Node GUID = .* is duplicated at\"" % (IBDIAGNET_LOG_FILE)
IBDIAGNET_OUT_NET_DUMP_FILE_PATH = "%s/ibdiagnet2.net_dump" % IBDIAGNET_OUT_DIRECTORY
IBDIAGNET_OUT_DB_CSV_FILE_PATH = "%s/ibdiagnet2.db_csv" % IBDIAGNET_OUT_DIRECTORY
EMPTY_RESPOND_MESSAGE = "Empty respond message"
IBDIAGNET_COMPLETION_MESSAGE = "ibdiagnet execution completed"
IBDIAGNET_EXCEED_NUMBER_OF_TASKS = "Maximum number of task exceeded, please remove a task before adding a new one"
IBDIAGNET_TASK_ALREDY_EXIST = "Task with same name already exists"
IBDIAGNET_RERROR_RESPONDS = (IBDIAGNET_EXCEED_NUMBER_OF_TASKS, IBDIAGNET_TASK_ALREDY_EXIST)
DEFAULT_IBDIAGNET_RESPONSE_DIR = '/tmp/ibdiagnet'  # temporarry - should be received as parameter
IBDIAGNET_AGE_INTERVAL_DEFAULT = 3600
MERGER_OPEN_SM_CONFIG_FILE = "%s/%s" % (TOPOCONFIG_DIRECTORY, "topoconfig")
LAST_DEPLOYED_NDT_FILE_INFO = "%s/%s" % (TOPOCONFIG_DIRECTORY, "deployed_ndt")
PORT_CONFIG_CSV_FILE = "%s/%s" % (TOPOCONFIG_DIRECTORY, "port_discovery_data.csv")
SWITCH_GUID = "Switch_GUID" 
PORT_NUM = "Port_Num" 
NEIGHBOR_GUID = "Neighbor_GUID" 
NEIGHBOR_PORT_NUM = "Neighbor_Port_Num" 
NEIGHBOR_TYPE = "Neighbor_Type"
PORT_STATE = "Port_State"
BOUNDARY_PORT_STATE_NO_DISCOVER = "No-discover"
BOUNDARY_PORT_STATE_DISABLED = "Disabled"
BOUNDARY_PORT_STATE_ACTIVE = "Active"
BOUNDARY_PORTS_STATES = [BOUNDARY_PORT_STATE_NO_DISCOVER,
                         BOUNDARY_PORT_STATE_DISABLED,
                         BOUNDARY_PORT_STATE_ACTIVE]
TOPOCONFIG_FIELD_NAMES = ["port_guid", "port_num", "peer_port_guid", "peer_port_num", "host_type", "port_state"]
NDT_FILE_STATE_NEW = "New"
NDT_FILE_STATE_VERIFY_FILED = "Verification Failed"
NDT_FILE_STATE_VERIFIED = "Verified"
NDT_FILE_CAPABILITY_VERIFY = "Verify"
NDT_FILE_CAPABILITY_VERIFY_DEPLOY_UPDATE = "Verify,Deploy,Update"
NDT_FILE_CAPABILITY_DEPLOY_UPDATE = "Deploy,Update"
NDT_FILE_STATE_DEPLOYED = "Deployed"
NDT_FILE_STATE_UPDATED = "Updated"
NDT_FILE_STATE_UPDATED_DISABLED = "Updated, Boundary ports disabled"
NDT_FILE_STATE_UPDATED_NO_DISCOVER = "Updated, Boundary ports No_discover"
NDT_FILE_STATE_DEPLOYED_DISABLED = "Deployed, ready for extension"
NDT_FILE_STATE_DEPLOYED_NO_DISCOVER = "Deployed, ready for verification"
NDT_FILE_STATE_DEPLOYED_COMPLETED = "Deployed, not active"

#port state mapping
IB_PORT_PHYS_STATE_NO_CHANGE = 0
IB_PORT_PHYS_STATE_SLEEP = 1
IB_PORT_PHYS_STATE_POLLING = 2
IB_PORT_PHYS_STATE_DISABLED = 3
IB_PORT_PHYS_STATE_PORTCONFTRAIN = 4
IB_PORT_PHYS_STATE_LINKUP = 5
IB_PORT_PHYS_STATE_LINKERRRECOVER = 6
IB_PORT_PHYS_STATE_PHYTEST = 7
ib_port_state = {
    IB_PORT_PHYS_STATE_DISABLED: BOUNDARY_PORT_STATE_DISABLED,
    IB_PORT_PHYS_STATE_POLLING: BOUNDARY_PORT_STATE_DISABLED, # for old switches if disabled physical state could be polling (???)
    IB_PORT_PHYS_STATE_LINKUP: BOUNDARY_PORT_STATE_NO_DISCOVER,
    }

def get_timestamp_str():
    return str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

def run_command_line_cmd(command):
    cmd = command.split()
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def execute_generic_command_interactive(command):
    logging.info("Server:Executing Command %s" % command)
    try:
        return run_command_line_cmd(command)
    except Exception as e:
        logging.error("Got exception when executing command")
        logging.error(e)
        return "Error on command %s execution %s command: %s" % (command,e)

def execute_generic_command(command):
    logging.info("Executing Command %s" % command)
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
        output, error = process.communicate()
        logging.debug("Command Errors: %s" % error)
        retcode = process.returncode
        if retcode != 0:
            logging.error(
                "Executing command failed: %s, status %s" % (
                    command, retcode))
            return False, "Failed to execute command %s command: %s" % (command,
                                                                         retcode)
    except Exception as e:
        logging.error("Got exception when executing command")
        logging.error(e)
        return False,"Error on command %s execution : %s" % (command,e)
    ret_msg = EMPTY_RESPOND_MESSAGE if not output else output
    return True, ret_msg

def check_file_exist(file_name):
    '''
    check if file exist
    :param file_name:
    '''
    if not os.path.isfile(file_name):
        return False
    return True

def get_file_last_update_time(file_name):
    '''
    get file update time
    :param file_name:
    '''
    try:
        last_modified_time = os.path.getmtime(file_name)
    except Exception as e:
        logging.error("Failed to get last update time for file %s (%s)" % (
                     file_name, e))
        return None
    return last_modified_time

def run_ibdiagnet():
    '''
    Run ibdiagnet command
    '''
    status , cmd_output = execute_generic_command(IBDIAGNET_COMMAND)
    return status

def run_ibdiagnet_verification_command():
    '''
    Run ibdiagnet command for port status verification
    '''
    status, cmd_output = execute_generic_command(IBDIAGNET_PORT_VERIFICATION_COMMAND)
    return status


def get_mapping_port_labels2port_numbers():
    '''
    Return map with mapping between node_guid and port_lable to port number
    to be used for topoconfig creation
    '''
    port_guid_lable_to_port_num = dict()
    with open(IBDIAGNET_OUT_DB_CSV_FILE_PATH, 'r', encoding="utf-8") as db_csv_file:
        # just read file until START_PORTS, then take all the lined until not END_PORTS
        hierarchy_section_started = False
        port_line_number = 0
        while line := db_csv_file.readline():
            if "START_PORT_HIERARCHY_INFO" in line:
                hierarchy_section_started = True
                port_line_number += 1
            elif hierarchy_section_started:
                if "END_PORT_HIERARCHY_INFO" in line:
                    break
                else:
                    if port_line_number >= 2:
                        port_hierarchy_info = line.strip().split(",")
                        port_key = "%s___%s" % (port_hierarchy_info[0], port_hierarchy_info[4].strip("\""))
                        port_guid_lable_to_port_num[port_key] = int(port_hierarchy_info[3])
                    port_line_number += 1
            else:
                continue
    return port_guid_lable_to_port_num

def get_boundary_ports_with_state(boundary_ports, global_verify_state=None):
    '''
    Get current port state for boundary ports
    :param boundary_ports_list: list of boundary ports
    IB_PORT_PHYS_STATE_NO_CHANGE 0
    IB_PORT_PHYS_STATE_SLEEP 1
    IB_PORT_PHYS_STATE_POLLING 2
    IB_PORT_PHYS_STATE_DISABLED 3
    IB_PORT_PHYS_STATE_PORTCONFTRAIN 4
    IB_PORT_PHYS_STATE_LINKUP 5
    IB_PORT_PHYS_STATE_LINKERRRECOVER 6
    IB_PORT_PHYS_STATE_PHYTEST 7
    
    Disabled -> IB_PORT_PHYS_STATE_DISABLED  ---> 3
    No-discover -> IB_PORT_PHYS_STATE_LINKUP ---> 5
    No-discover -> IB_PORT_PHYS_STATE_POLLING---> 2
    '''
    boundary_port_info_list = list()
    ports_lines = list()
    with open(IBDIAGNET_OUT_DB_CSV_FILE_PATH, 'r', encoding="utf-8") as db_csv_file:
        # just read file until START_PORTS, then take all the lined until not END_PORTS
        port_section_started = False
        while line := db_csv_file.readline():
            if "START_PORTS" in line:
                port_section_started = True
            elif port_section_started:
                if "END_PORTS" in line:
                    break
                else:
                    ports_lines.append(line.strip().split(","))
            else:
                continue
    # create struct for boundary ports
    if not ports_lines:
        logging.error("Failed to get ports info from file %s" % IBDIAGNET_OUT_DB_CSV_FILE_PATH)
        return []
    header = ports_lines[0]
    data = ports_lines[1:]
    data = pd.DataFrame(data, columns=header)
    data.to_csv(PORT_CONFIG_CSV_FILE, index=False)
    with open(PORT_CONFIG_CSV_FILE, 'r') as csvfile:
        dictreader = csv.DictReader(csvfile)
        try:
            _ = iter(dictreader)
        except TypeError as te:
            error_message = "{} is empty or cannot be parsed: {}".format(PORT_CONFIG_CSV_FILE, te)
            logging.error(error_message)
            return boundary_port_info_list
        for index, port_data in enumerate(dictreader):
            boundary_port_entry = "%s___%s" % (port_data["PortGuid"], port_data["PortNum"])
            if boundary_port_entry in boundary_ports:
                current_port_state = ib_port_state.get(int(port_data["PortPhyState"]), "None")
                verify_state = boundary_ports.get(boundary_port_entry, 0)
                if current_port_state != verify_state:
                    boundary_port_info_list.append(boundary_port_entry)
    return boundary_port_info_list

def check_duplicated_guids():
    '''
    Check ibdiagnet log file for duplicated guids error messages
    '''
    status , cmd_output = execute_generic_command(CHECK_DUPLICATED_GUIDS_COMMAND)
    return status, cmd_output

def check_boundary_port_state(sleep_interval=5, number_of_attempts=5,
                              ndt_file=None, expected_state=None):
    '''
    Check boundary ports state - if they according to topoconfig definition
    :param expected_state: state that we are expecting ports should be after topoconfig deploy
    '''
    # read boundary ports
    # run ibdiagnet
    # for boundary ports get their state
    # compare with expected
    # return true or false - depends on verification status
    topoconfig_file = MERGER_OPEN_SM_CONFIG_FILE if not ndt_file else get_topoconfig_file_name(ndt_file)
    if not check_file_exist(topoconfig_file):
        error_message = "Topoconfig file {} not found".format(topoconfig_file)
        logging.error(error_message)
        return False
    boundary_ports_info = dict()
    with open(topoconfig_file, 'r', encoding="utf-8") as topoconf_csv_file:
        dictreader = csv.DictReader(topoconf_csv_file,
                                    fieldnames=TOPOCONFIG_FIELD_NAMES)
        try:
            _ = iter(dictreader)
        except TypeError as te:
            error_message = "{} is empty or cannot be parsed: {}".format(topoconfig_file, te)
            logging.error(error_message)
            return False
        for index, row in enumerate(dictreader):
            logging.debug("Check topoconfig file: {}".format(row))
            try:
                if row["peer_port_guid"] == "-": # boundary port
                    port_guid_len = len(row["port_guid"])
                    if port_guid_len < 18: # in case and we have guid that is short - need to add zero
                        port_guid = "".join(["0x", "%s"%("0"*(18-port_guid_len)), row["port_guid"][2:]])
                    else:
                        port_guid = row["port_guid"]
                    boundary_port_entry = "%s___%s" % (port_guid, row["port_num"])
                    boundary_ports_info[boundary_port_entry] = row["port_state"]
            except Exception as e:
                error_message = "{}: failed to read boundary ports info: {}".format(topoconfig_file, te)
                logging.error(error_message)
                return False
        if boundary_ports_info:
            number_of_check_attempts = number_of_attempts
            while number_of_check_attempts > 0:
                # run ibdiagnet and get state for boundary ports
                if run_ibdiagnet_verification_command():
                    # check for ibdiagnet2.db_csv file
                    if not check_file_exist(topoconfig_file):
                        error_message = "Get boundary port state failure: ile {} not exists".format(topoconfig_file)
                        logging.error(error_message)
                        return False
                    # in loop pol for boundary ports state
                    boundary_ports_current_state = get_boundary_ports_with_state(boundary_ports_info, expected_state)
                    if not boundary_ports_current_state: # it meand there are boundary ports that have incorrect state - need to wait a bit more
                        break
                else:
                    error_message = "Failed to run ibdiagnet command for boundary ports state verification"
                    logging.error(error_message)
                    return False
                number_of_check_attempts -= 1
                time.sleep(sleep_interval)
            if not boundary_ports_current_state:
                return True
            else:
                error_message = "Boundary ports state not matching expected. SM topoconfig reload failed"
                logging.error(error_message)
                return False
        else:
            error_message = "{}: No boundary ports info found".format(topoconfig_file)
            logging.error(error_message)
            return False

def check_ibdiagnet_net_dump_file_exist():
    '''
    Check if ibdiagnet2.net_dump exist on standard location and could be taken as
    an option if the file is not too old. Let's say was created defined time
    interval (in hours) ago.
    '''
    if check_file_exist(DEFAULT_IBDIAGNET_NET_DUMP_PATH):
        # check date of file creation
        last_dump_file_update_time = get_file_last_update_time(
                                                DEFAULT_IBDIAGNET_NET_DUMP_PATH)
        current_time = datetime.now().timestamp()
        delta_seconds = current_time - last_dump_file_update_time
        logging.debug("%s file was updated %d seconds ago" % (
                                                DEFAULT_IBDIAGNET_NET_DUMP_PATH,
                                                int(delta_seconds)))
        # check if file was created less than 1 hour ago
        if delta_seconds <= IBDIAGNET_AGE_INTERVAL_DEFAULT:
            return True
        return False
    else:
        return False

def create_raw_topoconfig_file(ndt_file_path, boundary_port_state, patterns):
    '''
    Create topoconfig file upon request - not related to NDT file validation
    will include only links from ibdiagnet output and NDT.
    :param ndt_file_name:
    :param boundary_port_state:
    '''
    # create links_info_dictiionary based on ibdiagnet
    ndt_file_name = os.path.basename(ndt_file_path)
    if run_ibdiagnet():
        ibdiagnet_file_path = IBDIAGNET_OUT_NET_DUMP_FILE_PATH
    else:
        error_message = "Topoconfig file creation failed for {}. Failed to run ibdiagnet".format(ndt_file_name)
        logging.error(error_message)
        return False, error_message
    if not check_file_exist(ibdiagnet_file_path):
        error_message = "%s not exist" % IBDIAGNET_OUT_NET_DUMP_FILE_PATH
        logging.error(error_message)
        return False, error_message
    # will not check for duplicated GUIDs
    # get configuration from ibdiagnet
    ibdiagnet_links, ibdiagnet_links_reverse, links_info, error_message = \
                                   parse_ibdiagnet_dump(ibdiagnet_file_path)
    if error_message:
        logging.error(error_message)
        return False, error_message
    if links_info:
        creation_timestamp = get_timestamp_str()
        output_file_name = "%s_%s_%s_%s" % (MERGER_OPEN_SM_CONFIG_FILE, ndt_file_name,
                                         boundary_port_state, creation_timestamp)
        #this is the structure that contains names of the nodes and ports and GUIDs
        # on base of this struct should be created topconfig file
        create_status, error_message = create_topoconfig_file(links_info, ndt_file_path, patterns,
                                                      boundary_port_state,
                                                      output_file_name)
        if not create_status:
            logging.error(error_message)
            return False, error_message
        else:
            return True, "Topoconfig file %s based on %s created" % (output_file_name, ndt_file_name)
    else:
        error_message = "Failed to create topoconfig file - no links found"
        logging.error(error_message)
        return False, error_message

def get_topoconfig_file_name(ndt_file=None):
    '''
    Return combination of default topoconfig file name with ndt file name
    :param ndt_file_name:
    '''
    ndt_file_path = "%s_%s" % (MERGER_OPEN_SM_CONFIG_FILE, os.path.basename(ndt_file))
    return ndt_file_path

def create_topoconfig_file(links_info_dict, ndt_file_path, patterns,
                                                    boundary_port_state=None,
                                                    output_file_name=None):
    '''
    Create topoconfig file
    this is the structure that contains names of the nodes and ports and GUIDs
    on base of this struct should be created topconfig file
    :param links_list:
    :param ndt_file_path:
    
    '''
    # If boundery port described in NDT file it has no peer, so we can not get it's from
    # guid from ibdiagnet mapping as we do it now (?!) - possible to load all the ports from net_dump file
    # but may be it will be overload, so we will keep for device name mapping 
    # between device name and GUID of ports that have peer. We assuming that for the
    # switch for the device with the same name the guid will be the same,
    # and only port number will be different - and it is OK.
    # The issue is that boundary port will appear earlier than any other port of that device
    # OPEN ISSUE
    device_to_guid_map = dict()
    ndt_file = open(ndt_file_path, "r", encoding="utf-8")
    dictreader = csv.DictReader(ndt_file)
    host_type = "Any"
    file_creation_failed = False
    try:
        _ = iter(dictreader)
    except TypeError as te:
        error_message = "Topoconfig file creation failure: {} is empty or cannot be parsed: {}".format(ndt_file_path, te)
        logging.error(error_message)
        ndt_file.close()
        return False, error_message
    output_file = get_topoconfig_file_name(ndt_file_path) if not output_file_name else output_file_name
    # get mapping between node_guid and port lable to port number
    node_guid_lable2port_num = get_mapping_port_labels2port_numbers()
    with open(output_file, 'w') as topoconfig_file:
        for index, row in enumerate(dictreader):
            logging.debug("Parsing NDT link: {}".format(row))
            try:
                start_device, start_port, error_message = parse_ndt_port(
                                         os.path.basename(ndt_file_path), row, index,
                                         PortType.SOURCE, patterns, True)
                peer_device, peer_port, error_message = parse_ndt_port(
                                         os.path.basename(ndt_file_path), row, index,
                                         PortType.DESTINATION, patterns, True)

            except KeyError as ke:
                error_message = "No such column: {}, in line: {}".format(ke, index)
                report_error_message = "Topoconfig file creation failure: Error on NDT file {} parsing".format(os.path.basename(ndt_file_path))
                logging.error(error_message)
                file_creation_failed = True
                continue
            link_key = "%s___%s" % (start_device, start_port)
            # initially on verification boundary port state should be disabled
            # the question will it be the part of config file or UFM decision
            # port_state = row["State"]
            # After verification run completed the boundary port state will be Disabled
            # and than, if need, it will be changed to No-Discover
            port_state = row["State"]
            port_domain = row["Domain"]
            port_guid = links_info_dict.get(link_key)
            if not start_device in device_to_guid_map:
                device_to_guid_map[start_device] = port_guid
            if peer_device and peer_port:
                link_key_peer = "%s___%s" % (peer_device, peer_port)
                peer_port_guid = links_info_dict.get(link_key_peer)
                # in case peer port is not a number - get number from mapping
                if not peer_port.isnumeric():
                    port_key = "%s___%s" % (peer_port_guid, peer_port)
                    peer_port_num = node_guid_lable2port_num.get(port_key, None)
                    if peer_port_num:
                        peer_port = str(peer_port_num)
                    else:
                        error_message = "Failed to convert port label for GUID {}, Label {} to port number".format(peer_port_guid, peer_port)
                        report_error_message = "Topoconfig file creation failure: failed to convert port label to port number"
                        logging.error(error_message)
                        # TODO: AT what is the correct behavior in such case
                        file_creation_failed = True
            else:
                port_guid = device_to_guid_map.get(start_device)
                peer_port_guid = "-"
                peer_port = "-"
                port_state = BOUNDARY_PORT_STATE_DISABLED if not boundary_port_state else boundary_port_state
            if port_guid:
                topoconfig_file.write("%s,%s,%s,%s,%s,%s\n" % (port_guid, start_port,
                            peer_port_guid, peer_port,host_type,port_state))
    ndt_file.close()
    if file_creation_failed:
        if os.path.exists(output_file):
            os.remove(output_file)
        return False, report_error_message
    return True, "success"


def update_boundary_port_state_in_topoconfig_file(boundary_port_state,
                                                  ndt_file=None):
    '''
    Update topoconfig file - change boundary file state to received
    this is the structure that contains names of the nodes and ports and GUIDs
    on base of this struct should be created topconfig file
    :param links_list:
    :param ndt_file_path:
    '''
    if boundary_port_state not in BOUNDARY_PORTS_STATES:
        # incorrect boundary port state
        error_message = "Unknown boundary port state received: {}".format(boundary_port_state)
        logging.error(error_message)
        return False
    topoconfig_file = MERGER_OPEN_SM_CONFIG_FILE if not ndt_file else get_topoconfig_file_name(ndt_file)
    if not check_file_exist(topoconfig_file):
        error_message = "Topoconfig file {} not found".format(topoconfig_file)
        logging.error(error_message)
        return False
    updated_topoconfig = list()
    with open(topoconfig_file, 'r', encoding="utf-8") as topoconfig_file_initial:
        dictreader = csv.DictReader(topoconfig_file_initial,
                                    fieldnames=TOPOCONFIG_FIELD_NAMES)
        try:
            _ = iter(dictreader)
        except TypeError as te:
            error_message = "{} is empty or cannot be parsed: {}".format(topoconfig_file, te)
            logging.error(error_message)
            return False
        for index, row in enumerate(dictreader):
            logging.debug("Update topoconfig file: {}".format(row))
            try:
                orig_peer_port_guid = row["peer_port_guid"]
                if not orig_peer_port_guid or orig_peer_port_guid.strip() == "-": # well lets assume that the port with no peer is a boundary
                    row["port_state"] = boundary_port_state
                updated_row = ','.join(row.values())
                updated_topoconfig.append(updated_row + "\n")
            except KeyError as ke:
                error_message = "No such column: {}, in line: {}".format(ke, index)
                logging.error(error_message)
                continue # ATB ??? what to do?
    with open(topoconfig_file, 'w+') as topoconfig_file:
        for line in updated_topoconfig:
            topoconfig_file.write(line)
    return True

def update_last_deployed_ndt(ndt_file_name):
    '''
    write last deployed ndt file name to the file for next time to know
    which file was deployed last time
    :param ndt_file_name:
    '''
    with open(LAST_DEPLOYED_NDT_FILE_INFO, 'w') as deployed_ndt_file:
        file_info = '{"last_deployed_file": "%s"}' % ndt_file_name
        deployed_ndt_file.write(file_info)

def get_last_deployed_ndt():
    '''
    returns last deployed ndt file name
    :param ndt_file_name:
    '''
    if check_file_exist(LAST_DEPLOYED_NDT_FILE_INFO):
        file_name = ""
        with open(LAST_DEPLOYED_NDT_FILE_INFO, 'r') as deployed_ndt_file:
            file_info = json.load(deployed_ndt_file)
            file_name = file_info.get("last_deployed_file", "")
        return file_name
    else:
        return ""

def verify_fix_json_list_file(json_file_to_check):
    '''
    Open file for reading and try to load json
    if failed - remove trailed ] (if exist 2 ... like "]]") - unclear bug may be in json dump
    :param json_file_to_check: file name
    '''
    try:
        with open(json_file_to_check, "r+") as file:
            # unhandled exception in case ndts file was changed manually
            data = json.load(file)
    except Exception as e:
        # probably file is corrupted and need to fix
        logging.error("Failed to load json file %s: %s" % (json_file_to_check, e))
        with open(json_file_to_check, "r+") as file:
            data = file.read().rstrip()
            if data.endswith("]]"):
                data = data[:-1]
            else:
                # double ] - was not a problem
                # try to select the text between two [] signs
                last_brace = data.find("]")
                if last_brace < 0: # not found ]
                    logging.error("Failed to load json file %s. Not a ]] problem. And no ] found." % json_file_to_check)
                    return False
                data = data[:(last_brace+1)]
            file.seek(0)
            file.truncate(0)
            file.write(data)
            file.flush()
        with open(json_file_to_check, "r") as file:
            try:
                data = json.load(file)
            except:
                # did not help ....
                logging.error("Failed to fix json file %s (]] issue)." % json_file_to_check)
                return False
    return True
