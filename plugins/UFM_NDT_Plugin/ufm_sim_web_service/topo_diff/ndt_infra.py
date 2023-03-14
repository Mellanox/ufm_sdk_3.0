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
from topo_diff.topo_diff import parse_ndt_port, PortType

DEFAULT_IBDIAGNET_OUTPUT_PATH = "/var/tmp/ibdiagnet2"
DEFAULT_IBDIAGNET_NET_DUMP_PATH = "/var/tmp/ibdiagnet2/ibdiagnet2.net_dump"
IBDIAGNET_TARBALL_LOCATION_PATH = "/tmp/ibdiagnet"
IBDIAGNET_TARBALL_FILE_PREFIX = "ibdignet_output"
TOPOCONFIG_DIRECTORY = "/config/topoconfig"
IBDIAGNET_OUT_DIRECTORY = "/tmp/ndt_plugin"
IBDIAGNET_LOG_FILE = "%s/%s" % (IBDIAGNET_OUT_DIRECTORY, "ibdiagnet2.log")
IBDIAGNET_COMMAND = "ibdiagnet -o %s --enable_switch_dup_guid --skip dup_node_desc,lids,sm,nodes_info,pkey,pm,temp_sensing,virt" % IBDIAGNET_OUT_DIRECTORY
CHECK_DUPLICATED_GUIDS_COMMAND = "cat %s | grep \"Node GUID = .* is duplicated at\"" % (IBDIAGNET_LOG_FILE)
IBDIAGNET_OUT_NET_DUMP_FILE_PATH = "%s/ibdiagnet2.net_dump" % IBDIAGNET_OUT_DIRECTORY
EMPTY_RESPOND_MESSAGE = "Empty respond message"
IBDIAGNET_COMPLETION_MESSAGE = "ibdiagnet execution completed"
IBDIAGNET_EXCEED_NUMBER_OF_TASKS = "Maximum number of task exceeded, please remove a task before adding a new one"
IBDIAGNET_TASK_ALREDY_EXIST = "Task with same name already exists"
IBDIAGNET_RERROR_RESPONDS = (IBDIAGNET_EXCEED_NUMBER_OF_TASKS, IBDIAGNET_TASK_ALREDY_EXIST)
DEFAULT_IBDIAGNET_RESPONSE_DIR = '/tmp/ibdiagnet'  # temporarry - should be received as parameter
IBDIAGNET_AGE_INTERVAL_DEFAULT = 3600
MERGER_OPEN_SM_CONFIG_FILE = "%s/%s" % (TOPOCONFIG_DIRECTORY, "topoconfig")
LAST_DEPLOYED_NDT_FILE_INFO = "%s/%s" % (TOPOCONFIG_DIRECTORY, "deployed_ndt")
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
NDT_FILE_STATE_NEW = "new"
NDT_FILE_STATE_VERIFIED = "verified"
NDT_FILE_STATE_DEPLOYED = "deployed"
NDT_FILE_STATE_UPDATED = "updated"
NDT_FILE_STATE_UPDATED_DISABLED = "updated_disabled"
NDT_FILE_STATE_UPDATED_NO_DISCOVER = "updated_no_discover"
NDT_FILE_STATE_DEPLOYED_DISABLED = "deployed_disabled"
NDT_FILE_STATE_DEPLOYED_NO_DISCOVER = "deployed_no_discover"

def run_command_line_cmd(command):
    cmd = command.split()
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def execute_generic_command_interractive(command):
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

def check_duplicated_guids():
    '''
    Check ibdiagnet log file for duplicated guids error messages
    '''
    status , cmd_output = execute_generic_command(CHECK_DUPLICATED_GUIDS_COMMAND)
    return status, cmd_output

def check_ibdiagnet_net_dump_file_exist():
    '''
    Check if ibdiagmet2.net_dump exist on standard location and could be taken as
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

def create_topoconfig_file(links_info_dict, ndt_file_path, patterns,
                                                    boundary_port_state=None):
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
    try:
        _ = iter(dictreader)
    except TypeError as te:
        error_message = "{} is empty or cannot be parsed: {}".format(ndt_file_path, te)
        logging.error(error_message)
        ndt_file.close()
        return
    with open(MERGER_OPEN_SM_CONFIG_FILE, 'w') as topoconfig_file:
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
                logging.error(error_message)
                continue # ATB ??? what to do?
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
            else:
                port_guid = device_to_guid_map.get(start_device)
                peer_port_guid = "-"
                peer_port = "-"
                port_state = BOUNDARY_PORT_STATE_DISABLED if not boundary_port_state else boundary_port_state
            if port_guid:
                topoconfig_file.write("%s,%s,%s,%s,%s,%s\n" % (port_guid, start_port,
                            peer_port_guid, peer_port,host_type,port_state))
    ndt_file.close()


def update_boundary_port_state_in_topoconfig_file(boundary_port_state,
                                                  topoconfig_file_path=None):
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
    topoconfig_file = MERGER_OPEN_SM_CONFIG_FILE if not topoconfig_file_path else topoconfig_file_path
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
                file.seek(0)
                file.truncate(0)
                file.write(data)
                file.flush()
            else:
                # double ] - was not a problem
                logging.error("Failed to load json file %s. Not a ]] problem." % json_file_to_check)
                return False
        with open(json_file_to_check, "r") as file:
            try:
                data = json.load(file)
            except:
                # did not help ....
                logging.error("Failed to fix json file %s (]] issue)." % json_file_to_check)
                return False
    return True