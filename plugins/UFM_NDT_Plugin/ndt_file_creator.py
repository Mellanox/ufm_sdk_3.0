#!/usr/bin/env python3
#
# Copyright (C) 2013-2025 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
import re
import subprocess
import os
import argparse

IBDIAGNET_OUT_DIR = "/tmp/ibdiagnet_out"
NETDUMP_FILE_NAME = "ibdiagnet2.net_dump"
IBDIAGNET_COMMAND = "ibdiagnet -o %s --discovery_only --enable_output net_dump" % IBDIAGNET_OUT_DIR
IBDIAGNET_NET_DUMP_FILE = "%s/%s" % (IBDIAGNET_OUT_DIR, NETDUMP_FILE_NAME)
OUTPUT_NDT_FILE_NAME = "%s/generated_ndt.csv" % IBDIAGNET_OUT_DIR
REQUEST_ARGS = ["input_path", "include_down_ports", "include_error_ports", "brief_structure"]
#rack #,U height,#Fields:StartDevice,StartPort,StartDeviceLocation,EndDevice,EndPort,EndDeviceLocation,U height_1,LinkType,Speed,_2,Cable Length,_3,_4,_5,_6,_7,State,Domain
#,,SwitchX -  Mellanox Technologies,Port 26,,r-ufm64 mlx5_0,Port 1,,,,,,,,,,,,Active,In-Scope
HEADER_FULL="rack #,U height,#Fields:StartDevice,StartPort,StartDeviceLocation,EndDevice,EndPort,EndDeviceLocation,U height_1,LinkType,Speed,_2,Cable Length,_3,_4,_5,_6,_7,State,Domain\n"
HEADER_BRIEF="StartDevice,StartPort,EndDevice,EndPort,State,Domain\n"
LINE_FULL = ",,%s,Port %s,,%s,Port %s,,,,,,,,,,,,Active,In-Scope\n"
LINE_BRIEF = "%s,Port %s,%s,Port %s,Active,In-Scope\n"
LINE_DISCONNECTED_FULL = "%s,Port %s,,,,,,,,,,,,Disabled,Disconnected\n"
LINE_ERROR_FULL = "%s,Port %s,,,,,,,,,,,,Disabled,Error\n"
LINE_DISCONNECTED_BRIEF = "%s,Port %s,,,Disabled,Disconnected\n"
LINE_ERROR_BRIEF = "%s,Port %s,,,Disabled,Error\n"

class Link:
    def __init__(self, start_dev, start_port, end_dev, end_port):
        self.start_dev = start_dev
        self.start_port = start_port
        self.end_dev = end_dev
        self.end_port = end_port
        # unique key in upper-case to compare links regardless the case
        self.unique_key = start_dev.upper() + start_port.upper() + end_dev.upper() + end_port.upper()

    def __str__(self):
        return "{}/{} - {}/{}".format(self.start_dev, self.start_port, self.end_dev, self.end_port)

    def __eq__(self, other):
        return self.unique_key == other.unique_key

    def __hash__(self):
        return self.unique_key.__hash__()

def create_base_parser():
    """
    Create an argument parser
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    return parser

def allocate_request_args(parser, release_version="1.0"):
    """
    Definition of arguments
    :param parser:
    """
    request = parser.add_argument_group('request')
    request.add_argument("-i", "--input_path", action="store",
                         required=None, default=None, choices=None,
                         help="Path to directory with ibdiagnet output. If not set - script will run ibdiagnet utility.")
    request.add_argument("-d", "--include_down_ports", default=False, action="store_true",
                         help="Flag if to include in NDT file currently disconnected Switch ports")
    request.add_argument("-b", "--brief_structure", default=False, action="store_true",
                         help="Flag if NDT file should be created with mandatory NDT columns only (For NDT Merger).")
    request.add_argument("-e", "--include_error_ports", default=False, action="store_true",
                         help="Flag if to include in NDT file Active Switch ports with link error")

    request.add_argument("-v", "--version", action="version", version = release_version)

def extract_request_args(arguments):
    """
    Extracting the connection arguments from the parsed arguments.
    """
    return dict([(arg, arguments.pop(arg))
                 for arg in REQUEST_ARGS])

def run_command_line_cmd(command):
    cmd = command.split()
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def execute_generic_command_interractive(command):
    print("Executing Command %s" % command)
    try:
        return run_command_line_cmd(command)
    except Exception as e:
        print("Got exception when executing command")
        return "Error on command %s execution %s command: %s" % (command,e)

def execute_generic_command(command):
    print("Executing Command %s" % command)
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE)
        output, error = process.communicate()
        retcode = process.returncode
        if retcode != 0:
            print(
                "Executing command failed: %s, status %s" % (
                    command, retcode))
            return False, "Failed to execute command %s command: %s" % (command,
                                                                         retcode)
    except Exception as e:
        print("Got exception when executing command")
        print(e)
        return False,"Error on command %s execution : %s" % (command,e)
    ret_msg = "" if not output else output
    return True, ret_msg

def check_file_exist(file_name):
    '''
    check if file exist
    :param file_name:
    '''
    if not os.path.isfile(file_name):
        return False
    return True

def run_ibdiagnet():
    '''
    Run ibdiagnet command
    '''
    status , cmd_output = execute_generic_command(IBDIAGNET_COMMAND)
    return status

def parse_ibdiagnet_dump(net_dump_file_path, include_down_ports=False,
                                                include_error_ports=False):
    """
    create a structure based on ibdiagnet2.net_dump file - links information
    
    # This database file was automatically generated by IBDIAG
    # Running version   : "IBDIAGNET 2.10.0.MLNX20220721.cd746c3","IBDIAG 2.1.1.cd746c3","IBDM 2.1.1.cd746c3","IBIS 7.0.0.c25850e"
    # Running command   : ibdiagnet --extended_speeds all --counter all --pm_per_lane --get_phy_info --get_cable_info --rail_validation -o /tmp/ibdiagnet2 
    # Running timestamp : 2022-08-25 17:45:38 UTC +0000
    # File created at   : 2022-08-25 17:46:20 UTC +0000
    
    
    # Switch label port numbering explanation:
    #   Quantum2 switch split mode: ASIC/Cage/Port/Split, e.g 1/1/1/1
    #   Quantum2 switch no split mode: ASIC/Cage/Port
    #   Quantum switch split mode: Port/Split
    #   Quantum switch no split mode: Port
    
    
    "MF0;DSM09-0101-0603-40IB1:MQM8700/U1", Mellanox, 0x1070fd03001adeb4, LID 24328
      #          : IB# : Sta  : PhysSta    : MTU : LWA     : LSA     : FEC mode            : Retran : Neighbor Guid      : N#         : NLID : Neighbor Description
      1          : 1   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300dbfb92  : 40         : 25697 : "MF0;dsm09-0101-0602-01ib0:MQM8700/U1"
      2          : 2   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300e6c032  : 40         : 22524 : "MF0;dsm09-0101-0602-02ib0:MQM8700/U1"
      3          : 3   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300e6c57a  : 40         : 24891 : "MF0;dsm09-0101-0602-03ib0:MQM8700/U1"
      4          : 4   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300e6c3fa  : 40         : 33719 : "MF0;dsm09-0101-0602-04ib0:MQM8700/U1"
      5          : 5   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300e6c51a  : 40         : 21711 : "MF0;dsm09-0101-0602-05ib0:MQM8700/U1"
      6          : 6   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300e6c112  : 40         : 21400 : "MF0;dsm09-0101-0604-01ib0:MQM8700/U1"
      7          : 7   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300fca4a6  : 40         : 22400 : "MF0;dsm09-0101-0604-02ib0:MQM8700/U1"
      8          : 8   : ACT  : LINK UP    : 5   : 4x      : 50      : MLNX_RS_271_257_PLR : NO-RTR : 0xc42a10300fcad46  : 40         : 23194 : "MF0;dsm09-0101-0604-03ib0:MQM8700/U1"
    
    """
    ibdiagnet_links = set()
#    For ports that are currently down
    links_list_disconnected = []
#    For ports that are Active but have problem with link - no destination defined
    links_list_errored = []
    with open(net_dump_file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if not line.strip():
                continue
            elif re.match(r'^#', line.strip()):
                continue
            elif re.match(r'^"', line):
                # beginning of the switch
                switch_info = line.split(",")
                continue
            else:
                # lines of switch
                # split by "\"" to get destination device name
                link_destination_host_info = line.split("\"")
                link_info_list = link_destination_host_info[0].split(":")
                if not link_info_list or len(link_info_list) == 1:
                    # empty string or failed to split info using ":"
                    continue
                link_state = link_info_list[2].strip().lower()
                link_info_dict = {}
                link_info_dict["node_name"] = switch_info[0].strip('"')
                link_info_dict["node_guid"] = switch_info[2].strip()
                link_info_dict["node_port_number"] = link_info_list[0].strip()
                # ports that are down - include if received flag to do so
                if link_state == "down":
                    if include_down_ports:
                        links_list_disconnected.append(link_info_dict)
                    continue
                # handle error when switch port is Active but does not have valid link
                # switch sisw007.s020.pci3 Port 1/16/1
                #  1/16/1:31:INI:LINK UP:5:4x:100:MLNX_RS_271_257_PLR:NO-RTR::::
                if len(link_destination_host_info) == 1:
                    if include_error_ports:
                        links_list_errored.append(link_info_dict)
                    continue
                peer_node_name = link_destination_host_info[-2].strip().strip('"')
                peer_node_guid = link_info_list[9].strip()
                peer_node_port_number = link_info_list[10].strip()
                valid_peer_params = True
                for parameter in (peer_node_name, peer_node_guid, peer_node_port_number):
                    if not parameter or parameter.isspace():
                        valid_peer_params = False
                        break
                #skip the line with problematic link
                if include_error_ports and not valid_peer_params:
                    links_list_errored.append(link_info_dict)
                    continue
                link_info_dict["peer_node_name"] = peer_node_name
                link_info_dict["peer_node_guid"] = peer_node_guid
                link_info_dict["peer_node_port_number"] = peer_node_port_number
                if "Aggregation Node" in link_info_dict["peer_node_name"]:
                    # sharp node - probably will not be a part of NDT file - skip
                    continue
                ibdiagnet_links.add(Link(link_info_dict["node_name"],
                                         link_info_dict["node_port_number"],
                                         link_info_dict["peer_node_name"],
                                         link_info_dict["peer_node_port_number"]))

    return ibdiagnet_links, links_list_disconnected, links_list_errored


def main():
    '''
    Main script function
    '''
        # arguments parser
    parser = create_base_parser()
    allocate_request_args(parser)
    arguments = vars(parser.parse_args())
    request_arguments = extract_request_args(arguments)
    input_path = request_arguments['input_path']

    if not input_path:
        # run ibdiagnet command to create output
        ibdiag_net_dump_file = IBDIAGNET_NET_DUMP_FILE
        if not run_ibdiagnet():
            print("Filed to run ibdiagnet command: %s" % IBDIAGNET_COMMAND)
            exit(1)
    else:
        # use ibdiagnet dump
        ibdiag_net_dump_file = os.path.join(input_path, NETDUMP_FILE_NAME)
    # check if net dump file exist
    if not check_file_exist(ibdiag_net_dump_file):
        print("ibdiagnet output file %s not exist" % ibdiag_net_dump_file)
        exit(1)
    include_down_ports = request_arguments['include_down_ports']
    include_error_ports = request_arguments['include_error_ports']
    brief_structure = request_arguments['brief_structure']
    ibdiagnet_links, links_list_disconnected , links_list_errored = \
                                    parse_ibdiagnet_dump( ibdiag_net_dump_file,
                                                             include_down_ports,
                                                             include_error_ports)
    #rack #,U height,#Fields:StartDevice,StartPort,StartDeviceLocation,EndDevice,EndPort,EndDeviceLocation,U height_1,LinkType,Speed,_2,Cable Length,_3,_4,_5,_6,_7,State,Domain
    #,,SwitchX -  Mellanox Technologies,Port 26,,r-ufm64 mlx5_0,Port 1,,,,,,,,,,,,Active,In-Scope
    if brief_structure:
        header = HEADER_BRIEF
        link_line = LINE_BRIEF
        error_line = LINE_ERROR_BRIEF
        disconnected_line = LINE_DISCONNECTED_BRIEF
    else:
        header = HEADER_FULL
        link_line = LINE_FULL
        error_line = LINE_ERROR_FULL
        disconnected_line = LINE_DISCONNECTED_FULL
    # output file name - based on input path
    with open(OUTPUT_NDT_FILE_NAME, 'w') as ndt_file:
        ndt_file.write(header)
        for link in ibdiagnet_links:
            line = link_line % (
                   link.start_dev, link.start_port, link.end_dev, link.end_port)
            ndt_file.write(line)
        for disconnected_port in links_list_disconnected:
            line = disconnected_line % (disconnected_port.get("node_name", ""),
                                        disconnected_port.get("node_port_number", ""))
            ndt_file.write(line)
        for error_port in links_list_errored:
            line = error_line % (error_port.get("node_name", ""),
                                 error_port.get("node_port_number", ""))
            ndt_file.write(line)


    print("NDT file generation completed. Generated file can be found at %s" % OUTPUT_NDT_FILE_NAME)

if __name__ == '__main__':
    main()
