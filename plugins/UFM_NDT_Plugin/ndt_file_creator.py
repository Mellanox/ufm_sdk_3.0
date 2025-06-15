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
import pandas as pd
import io
import sys


IBDIAGNET_OUT_DIR = "/tmp/ibdiagnet_out"
NETDUMP_FILE_NAME = "ibdiagnet2.net_dump"
DB_CSV_FILE_NAME = "ibdiagnet2.db_csv"
IBDIAGNET_COMMAND = "ibdiagnet -o %s --discovery_only --enable_output net_dump" % IBDIAGNET_OUT_DIR
IBDIAGNET_NET_DUMP_FILE = "%s/%s" % (IBDIAGNET_OUT_DIR, NETDUMP_FILE_NAME)
IBDIAGNET_DB_CSV_FILE = "%s/%s" % (IBDIAGNET_OUT_DIR, DB_CSV_FILE_NAME)
OUTPUT_NDT_FILE_NAME = "%s/generated_ndt.csv" % IBDIAGNET_OUT_DIR
REQUEST_ARGS = ["input_path", "brief_structure"]
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
    request.add_argument("-b", "--brief_structure", default=False, action="store_true",
                         help="Flag if NDT file should be created with mandatory NDT columns only (For NDT Merger).")
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

def extract_section(content, section_name):
    """
    Extract a section from the db_csv file content
    """
    pattern = rf"START_{section_name}\n(.*?)END_{section_name}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def parse_ibdiagnet_dump(db_csv_file_path):
    """
    Create a structure based on ibdiagnet2.db_csv file - links information
    """
    with open(db_csv_file_path, 'r') as f:
        content = f.read()

    links_txt = extract_section(content, "LINKS")
    port_hierarchy_txt = extract_section(content, "PORT_HIERARCHY_INFO")
    nodes_txt = extract_section(content, "NODES")

    links_df = pd.read_csv(io.StringIO(links_txt), sep=',')
    port_df = pd.read_csv(io.StringIO(port_hierarchy_txt), sep=',')
    nodes_df = pd.read_csv(io.StringIO(nodes_txt), sep=',')

    # Clean up whitespace
    nodes_df['NodeDesc'] = nodes_df['NodeDesc'].astype(str).str.strip()
    nodes_df['NodeGUID'] = nodes_df['NodeGUID'].astype(str).str.strip()
    nodes_df['NodeType'] = nodes_df['NodeType'].astype(str).str.strip()
    port_df['NodeGUID'] = port_df['NodeGUID'].astype(str).str.strip()
    port_df['PortNum'] = port_df['PortNum'].astype(str).str.strip()
    port_df['ExtendedLabel'] = port_df['ExtendedLabel'].astype(str).str.strip()
    links_df['NodeGuid1'] = links_df['NodeGuid1'].astype(str).str.strip()
    links_df['PortNum1'] = links_df['PortNum1'].astype(str).str.strip()
    links_df['NodeGuid2'] = links_df['NodeGuid2'].astype(str).str.strip()
    links_df['PortNum2'] = links_df['PortNum2'].astype(str).str.strip()

    # Build lookups
    node_guid_to_desc = nodes_df.set_index('NodeGUID')['NodeDesc'].to_dict()
    node_guid_to_type = nodes_df.set_index('NodeGUID')['NodeType'].to_dict()
    port_label_map = port_df.set_index(['NodeGUID', 'PortNum'])['ExtendedLabel'].to_dict()

    ibdiagnet_links = set()
    for _, row in links_df.iterrows():
        src_guid = row['NodeGuid1']
        src_port = row['PortNum1']
        dst_guid = row['NodeGuid2']
        dst_port = row['PortNum2']

        src_node_desc = node_guid_to_desc.get(src_guid, '')
        dst_node_desc = node_guid_to_desc.get(dst_guid, '')
        src_node_type = node_guid_to_type.get(src_guid, '')
        dst_node_type = node_guid_to_type.get(dst_guid, '')

        # Exclude any link where either node description contains "Mellanox Technologies Aggregation Node"
        if 'Mellanox Technologies Aggregation Node' in src_node_desc or 'Mellanox Technologies Aggregation Node' in dst_node_desc:
            continue

        # Host to host: skip
        if src_node_type == '1' and dst_node_type == '1':
            continue

        src_port_label = port_label_map.get((src_guid, src_port), src_port)
        dst_port_label = port_label_map.get((dst_guid, dst_port), dst_port)

        # Switch to switch: add both directions
        if src_node_type == '2' and dst_node_type == '2':
            # Original direction
            ibdiagnet_links.add(Link(src_node_desc, src_port_label, dst_node_desc, dst_port_label))
            # Reverse direction
            ibdiagnet_links.add(Link(dst_node_desc, dst_port_label, src_node_desc, src_port_label))
            continue

        # Host to switch: swap to switch to host
        if src_node_type == '1' and dst_node_type == '2':
            ibdiagnet_links.add(Link(dst_node_desc, dst_port_label, src_node_desc, src_port_label))
            continue

        # Switch to host: keep as is
        if src_node_type == '2' and dst_node_type == '1':
            ibdiagnet_links.add(Link(src_node_desc, src_port_label, dst_node_desc, dst_port_label))
            continue

    return ibdiagnet_links

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
        ibdiag_db_csv_file = IBDIAGNET_DB_CSV_FILE
        if not run_ibdiagnet():
            print("Filed to run ibdiagnet command: %s" % IBDIAGNET_COMMAND)
            exit(1)
    else:
        # use ibdiagnet dump
        ibdiag_db_csv_file = os.path.join(input_path, DB_CSV_FILE_NAME)
    # check if net dump file exist
    if not check_file_exist(ibdiag_db_csv_file):
        print("ibdiagnet output file %s not exist" % ibdiag_db_csv_file)
        exit(1)
    brief_structure = request_arguments['brief_structure']
    ibdiagnet_links = parse_ibdiagnet_dump(ibdiag_db_csv_file)
    #rack #,U height,#Fields:StartDevice,StartPort,StartDeviceLocation,EndDevice,EndPort,EndDeviceLocation,U height_1,LinkType,Speed,_2,Cable Length,_3,_4,_5,_6,_7,State,Domain
    #,,SwitchX -  Mellanox Technologies,Port 26,,r-ufm64 mlx5_0,Port 1,,,,,,,,,,,,Active,In-Scope
    if brief_structure:
        header = HEADER_BRIEF
        link_line = LINE_BRIEF
    else:
        header = HEADER_FULL
        link_line = LINE_FULL
    # output file name - based on input path
    with open(OUTPUT_NDT_FILE_NAME, 'w') as ndt_file:
        ndt_file.write(header)
        for link in ibdiagnet_links:
            line = link_line % (
                   link.start_dev, link.start_port, link.end_dev, link.end_port)
            ndt_file.write(line)

    print("NDT file generation completed. Generated file can be found at %s" % OUTPUT_NDT_FILE_NAME)

if __name__ == '__main__':
    main()
