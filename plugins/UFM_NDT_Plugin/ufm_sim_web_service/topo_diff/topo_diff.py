import requests
import os
import csv
import logging
import json
import re
import pickle
from enum import Enum
import pandas as pd
import io

# ATB
from pprint import pprint

# Column name defines
NODE_DESC_COLUMN = 'NodeDesc'
NODE_GUID_COLUMN = 'NodeGUID'
NODE_TYPE_COLUMN = 'NodeType'
NODE_PORT_COLUMN = 'NodePort'
NODE_PORT_GUID_COLUMN = 'NodePortGUID'
NODE_PORT_NUM_COLUMN = 'NodePortNum'
NODE_LID_COLUMN = 'NodeLID'
PORT_NUM_COLUMN = 'PortNum'
EXTENDED_LABEL_COLUMN = 'ExtendedLabel'
LABEL_COLUMN = 'Label'
PORT_GUID_COLUMN = 'PortGUID'

SUCCESS_CODE = 200
ERROR_CODE = 400
ACCEPTED_CODE = 202
REST_TIMEOUT = 300

CABLE_VALIDATION_LOGIN_URL = "cablevalidation/login"
CABLE_VALIDATION_REPORT_URL = "cablevalidation/report/validation"
CABLE_VALIDATION_PROTOCOL = "https"
CABLE_VALIDATION_LOCAL_PORT_NUMBER = 8633 #
COOKIE_FILE_PATH = "/tmp/cable_validation_cookie"

class PortType(Enum):
    SOURCE = 1
    DESTINATION = 2


class Constants:
    # NDT keys
    start_device_keys = ["#StartDevice", "#Fields:StartDevice", "StartDevice"]
    start_port_key = "StartPort"
    end_device_key = "EndDevice"
    end_port_key = "EndPort"

    # UFM keys
    source_description_key = "source_port_node_description"
    source_port_key = "source_port"
    destination_description_key = "destination_port_node_description"
    destination_port_key = "destination_port"

    internal_hdr_link = "Mellanox Technologies Aggregation Node"


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

def check_valid_peer_port_param(parameter_val):
    '''
    peer parameter value should not be none or empty string
    :param parameter_val:
    '''
    if not parameter_val or parameter_val.isspace():
        return False
    return True

def extract_section(content, section_name):
    """
    Extract a section from a string based on the section name.
    
    Args:
        content (str): The content string to search for the section.
        section_name (str): The name of the section to extract.
    """
    pattern = rf"START_{section_name}\n(.*?)END_{section_name}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def check_not_empty_valid_params(parameters_vals_list):
    '''
    peer parameters values should not be none or empty string
    :param parameters_vals_list:
    '''
    for parameter_val in parameters_vals_list:
        if not parameter_val or parameter_val.isspace():
            return False
    return True

def parse_ndt_port(file, row, index, port_type, patterns, merger=False):
    if port_type == PortType.SOURCE:
        device_key = ""
        for start_device_key in Constants.start_device_keys:
            if row.get(start_device_key):
                device_key = start_device_key
                break
        port_key = Constants.start_port_key
    elif port_type == PortType.DESTINATION:
        device_key = Constants.end_device_key
        port_key = Constants.end_port_key
    else:
        return "", "", "Internal error: incorrect port_type"

    try:
        device = row[device_key]
    except KeyError as ke:
        error_message = "Failed to parse {}: {}, in file: {}, line: {}. KeyError: {}" \
            .format(port_type,
                    row[port_key],
                    file, index, ke)
        logging.error(error_message)
        return "", "", error_message
    port = ""
    if patterns:
        for pattern in patterns:
            match = re.match(pattern, row[port_key])
            if match:
                port = match.group(1)
    else:
        port = row[port_key]
        pattern = "^Port (\\d+)$"
        match = re.match(pattern, port)
        if match:
            port = match.group(1)
    if not port and not merger:
        error_message = "Failed to parse {}: {}, in file: {}, line: {}." \
            .format(port_type,
                    row[port_key],
                    file, index)
        logging.error(error_message)
        return "", "", error_message
    else:
        return device, port, ""


def parse_ndt_file(ndt_links, ndt_file, patterns, ndt_links_reversed=None, merger=False):
    logging.debug("Reading from csv file:" + ndt_file)
    error_response = []
    try:
        with open(ndt_file, 'r') as csvfile:
            dictreader = csv.DictReader(csvfile)
            try:
                _ = iter(dictreader)
            except TypeError as te:
                error_message = "{} is empty or cannot be parsed: {}".format(ndt_file, te)
                logging.error(error_message)
                return [error_message]
            total_rows = 0
            for index, row in enumerate(dictreader):
                logging.debug("Parsing NDT link: {}".format(row))
                total_rows += 1
                try:
                    start_device, start_port, error_message =\
                        parse_ndt_port(os.path.basename(ndt_file), row, index, PortType.SOURCE, patterns,merger)
                    if error_message:
                        error_response.append(error_message)
                    end_device, end_port, error_message =\
                        parse_ndt_port(os.path.basename(ndt_file), row, index, PortType.DESTINATION, patterns,merger)
                    if merger:
                        # plase holder - if it will be additional stuff to filter for merger
                        if not end_device or not end_port:
                            # merger flow qnd probably boundary port - need to skip this row
                            logging.debug("Not found peer device name and port - number - boundary port. Skip")
                            continue
                    if error_message:
                        error_response.append(error_message)
                    ndt_links.add(Link(start_device, start_port, end_device, end_port))
                    if ndt_links_reversed is not None:
                        ndt_links_reversed.add(Link(end_device, end_port, start_device, start_port))
                except KeyError as ke:
                    error_message = "No such column: {}, in line: {}".format(ke, index)
                    logging.error(error_message)
                    error_response.append(error_message)
            if total_rows:
                return error_response
            else:
                return ["{} is empty or cannot be parsed".format(ndt_file)]
    except FileNotFoundError as fnfe:
        error_message = "{} not found: {}".format(ndt_file, fnfe)
        logging.error(error_message)
        return [error_message]

def parse_ibdiagnet_dump(db_csv_path):
    """
    Parse ibdiagnet dump file and return the same structures as parse_ibdiagnet_dump
    Args:
        db_csv_path (str): Path to the db_csv file containing LINKS, PORT_HIERARCHY_INFO, and NODES sections
    Returns:
        tuple: (ibdiagnet_links, ibdiagnet_links_reverse, links_info_dict, [])
            - ibdiagnet_links: Set of Link objects for forward direction (switch-to-switch and switch-to-host)
            - ibdiagnet_links_reverse: Set of Link objects for reverse direction (only switch-to-switch)
            - links_info_dict: Dictionary mapping node_name___port_number to node_guid
            - []: Empty list for compatibility
    """
    with open(db_csv_path, 'r') as f:
        content = f.read()

    # Extract sections
    links_txt = extract_section(content, "LINKS")
    port_hierarchy_txt = extract_section(content, "PORT_HIERARCHY_INFO")
    nodes_txt = extract_section(content, "NODES")

    # Read into DataFrames
    links_df = pd.read_csv(io.StringIO(links_txt), sep=',')
    port_hierarchy_df = pd.read_csv(io.StringIO(port_hierarchy_txt), sep=',')
    nodes_df = pd.read_csv(io.StringIO(nodes_txt), sep=',')

    # Clean up the data
    nodes_df[NODE_DESC_COLUMN] = nodes_df[NODE_DESC_COLUMN].astype(str).str.strip()
    nodes_df[NODE_GUID_COLUMN] = nodes_df[NODE_GUID_COLUMN].astype(str).str.strip()
    nodes_df[NODE_TYPE_COLUMN] = nodes_df[NODE_TYPE_COLUMN].astype(str).str.strip()
    port_hierarchy_df[NODE_GUID_COLUMN] = port_hierarchy_df[NODE_GUID_COLUMN].astype(str).str.strip()

    # Create mappings for easier lookup
    node_guid_to_desc = nodes_df.set_index(NODE_GUID_COLUMN)[NODE_DESC_COLUMN].to_dict()
    node_guid_to_type = nodes_df.set_index(NODE_GUID_COLUMN)[NODE_TYPE_COLUMN].to_dict()
    port_label_map = port_hierarchy_df.set_index([NODE_GUID_COLUMN, PORT_NUM_COLUMN])[EXTENDED_LABEL_COLUMN].to_dict()

    # Initialize return values
    ibdiagnet_links = set()
    ibdiagnet_links_reverse = set()
    # links_info_dict is a dictionary that maps a link key to a tuple containing the source and destination node descriptions and port labels
    links_info_dict = {}
    # in future to resolve GUID and host description
    node_description_to_guid_dict = {}
    # in future to resolve port number and pair of node description and port label
    node_description_port_lablel_to_port_number_dict = create_node_description_port_label_mapping(nodes_df, port_hierarchy_df)

    print(f"total links {len(links_df)}")
    # Process links according to requirements
    for _, row in links_df.iterrows():
        src_guid = row['NodeGuid1']
        src_port = row['PortNum1']
        dst_guid = row['NodeGuid2']
        dst_port = row['PortNum2']

        src_node_desc = node_guid_to_desc.get(src_guid, '')
        dst_node_desc = node_guid_to_desc.get(dst_guid, '')
        src_node_type = node_guid_to_type.get(src_guid, '')
        dst_node_type = node_guid_to_type.get(dst_guid, '')
        src_port_label = port_label_map.get((src_guid, src_port), str(src_port))
        dst_port_label = port_label_map.get((dst_guid, dst_port), str(dst_port))
        node_description_to_guid_dict[src_node_desc] = src_guid
        node_description_to_guid_dict[dst_node_desc] = dst_guid 

        # Exclude any link where either source / destination node description contains "Mellanox Technologies Aggregation Node"
        if 'Mellanox Technologies Aggregation Node' in src_node_desc or 'Mellanox Technologies Aggregation Node' in dst_node_desc:
            continue
        link_key_1 = f"{src_node_desc}___{src_port_label}"
        link_key_2 = f"{dst_node_desc}___{dst_port_label}"
        links_info_dict[link_key_1] = f"{src_guid}:{src_port}"
        links_info_dict[link_key_2] = f"{dst_guid}:{dst_port}"

        # Host to switch: need to "switch" between link src and dst to be compatible with topoconfig format
        if src_node_type == '1' and dst_node_type == '2':
            # Add to links_info_dict
            ibdiagnet_links.add(Link(dst_node_desc, dst_port_label, src_node_desc, src_port_label))
            continue

        # Switch to switch: add both directions
        if src_node_type == '2' and dst_node_type == '2':
            # Add to links_info_dict
            # Add forward link
            ibdiagnet_links.add(Link(src_node_desc, src_port_label, dst_node_desc, dst_port_label))
            ibdiagnet_links.add(Link(dst_node_desc, dst_port_label, src_node_desc, src_port_label))
            # Add reverse link (only for switch-to-switch)
            ibdiagnet_links_reverse.add(Link(src_node_desc, src_port_label, dst_node_desc, dst_port_label))
            ibdiagnet_links_reverse.add(Link(dst_node_desc, dst_port_label, src_node_desc, src_port_label))
            continue

        # Switch to host: keep as is
        if src_node_type == '2' and dst_node_type == '1':
            # Add to links_info_dict
            # Add link - no reverse link for switch-to-host
            ibdiagnet_links.add(Link(src_node_desc, src_port_label, dst_node_desc, dst_port_label))
            continue

    return (ibdiagnet_links, ibdiagnet_links_reverse, links_info_dict, node_description_to_guid_dict,
                        node_description_port_lablel_to_port_number_dict, [])


def get_reverse_link_info(link_info_dict):
    '''
    return reversive link information
    :param link_info_dict: 
    '''
    reverce_link_info_dict = {}
    reverce_link_info_dict["node_name"] = link_info_dict["peer_node_name"]
    reverce_link_info_dict["node_guid"] = link_info_dict["peer_node_guid"]
    reverce_link_info_dict["node_port_number"] = link_info_dict["peer_node_port_number"]
    reverce_link_info_dict["peer_node_name"] = link_info_dict["node_name"]
    reverce_link_info_dict["peer_node_guid"] = link_info_dict["node_guid"]
    reverce_link_info_dict["peer_node_port_number"] = link_info_dict["node_port_number"]
    return reverce_link_info_dict


def parse_ndt_files(ndts_list_file, switch_patterns, host_patterns):
    error_response = []
    ndt_links = set()
    ndt_links_reversed = set()
    ndt_files_dir = os.path.dirname(ndts_list_file)
    # in case somebody deleted ndts.json - unhandled exception, server should be restarted
    with open(ndts_list_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        if not data:
            return {}, {}, ["No NDTs were uploaded for comparison"]
        for ndt_file_entry in data:
            # in case somebody manually changed ndts.json format - unhandled exception, server should be restarted
            ndt_file = ndt_file_entry["file"]
            ndt_type = ndt_file_entry["file_type"]
            if ndt_type == "switch_to_host":
                error_response.extend(parse_ndt_file(ndt_links,
                                                     os.path.join(ndt_files_dir, ndt_file),
                                                     switch_patterns + host_patterns,
                                                     ndt_links_reversed))
            elif ndt_type == "switch_to_switch":
                error_response.extend(parse_ndt_file(ndt_links,
                                                     os.path.join(ndt_files_dir, ndt_file),
                                                     switch_patterns,
                                                     None))
            else:
                error_response.append("Unknown file format")
        if error_response:
            return {}, {}, error_response

        return ndt_links, ndt_links_reversed, []


def get_request(host_ip, protocol, resource, headers):
    request = protocol + '://' + host_ip + resource
    response = requests.get(request, verify=False, headers=headers)
    logging.info("UFM API Request Status: {}, URL: {}".format(response.status_code, request))
    return response


def save_cable_validation_cookies(requests_cookiejar, cookie_filename):
    '''
    Save cookies to file
    :param requests_cookiejar:
    :param cookie_filename:
    '''
    with open(cookie_filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cable_validation_cookies(cookie_filename):
    '''
    Load cookie from file
    :param cookie_filename:
    '''
    with open(cookie_filename, 'rb') as f:
        return pickle.load(f)

def post_request_with_cookies(host_addr, port_num, username, password):
    '''
    Create cookie file and then use it for get request
    :param host_addr:
    :param port_num:
    :param username:
    :param password:
    :param url:
    '''
    send_url = f"{CABLE_VALIDATION_PROTOCOL}://{host_addr}:{port_num}/{CABLE_VALIDATION_LOGIN_URL}"
    send_payload = {'httpd_username': username, 'httpd_password': password}
    try:
        session = requests.Session()
        logging.info("Send cable validation login request.")
        rest_respond = session.post(send_url,data=send_payload,verify=False,
                                            timeout=REST_TIMEOUT)
        if rest_respond.status_code != SUCCESS_CODE:
            logging.error(f"Cable validation login request failed: {send_url} return code {rest_respond.status_code}")
            return None
        logging.info("Save cable validation request cookies.")
        save_cable_validation_cookies(session.cookies, COOKIE_FILE_PATH)
    except Exception as e:
        logging.error(f"Cable validation login request failed: {send_url} error: {e}")
        return None
    # send request for cable validation report
    cv_report_url = f"{CABLE_VALIDATION_PROTOCOL}://{host_addr}:{port_num}/{CABLE_VALIDATION_REPORT_URL}"
    cv_rest_respond = None
    try:
        session = requests.Session()
        logging.info(f"Send request for cable validation report using cookies: {cv_report_url}")
        cv_rest_respond = session.get(cv_report_url,
                        cookies=load_cable_validation_cookies(COOKIE_FILE_PATH),
                        verify=False,
                        timeout=REST_TIMEOUT)
    except Exception as e:
        logging.error(f"Request for Cable Validation report failed: {cv_report_url} error: {e}")
    return cv_rest_respond

def post_request(host_ip, ufm_protocol, resource, headers, send_payload):
    '''
    Send put request to UFM
    :param host_ip:
    :param ufm_protocol:
    :param resource:
    :param headers:
    :param payload:
    '''
    request = ufm_protocol + '://' + host_ip + resource
    response = requests.post(request, headers=headers,
                                            json=send_payload, verify=False,
                                            timeout=300)
    logging.info("UFM API PUT Request Status: {}, URL: {}".format(response.status_code, request))
    return response

def get_ufm_links(ufm_port):
    ufm_host = "127.0.0.1:{}".format(ufm_port)
    ufm_protocol = "http"
    resource = "/resources/links"
    headers = {"X-Remote-User": "ufmsystem"}
    response = get_request(ufm_host, ufm_protocol, resource, headers)
    if response.status_code != SUCCESS_CODE:
        return {}, response.status_code
    else:
        return response.json, SUCCESS_CODE

def upload_topoconfig_file(ufm_port, payload):
    '''
    Upload topoconfig file to the UFM server
    :param ufm_port:
    '''
    ufm_host = "127.0.0.1:{}".format(ufm_port)
    ufm_protocol = "http"
    resource = "/Topology_Compare/master_topology"
    headers = {"X-Remote-User": "ufmsystem"}
    response = post_request(ufm_host, ufm_protocol, resource, headers, payload)
    if response.status_code not in (ACCEPTED_CODE, SUCCESS_CODE):
        return "Failed to upload topoconfig file to UFM", response.status_code
    else:
        return response.json, SUCCESS_CODE

def get_local_cable_validation_report(ufm_port):
    '''
    Send request for cable validation report locally
    '''
    ufm_host = "127.0.0.1:{}".format(ufm_port)
    ufm_protocol = "http"
    resource = "/plugin/cablevalidation/cablevalidation/report/validation"
    headers = {"X-Remote-User": "ufmsystem"}
    response = get_request(ufm_host, ufm_protocol, resource, headers)
    if not response:
        logging.error("Failed to get respond for cable validation report request from localhost.")
        return {}, ERROR_CODE
    else:
        return json.loads(response.text), SUCCESS_CODE


def get_cable_validation_report(cable_validation_server_address,
                                cable_validation_request_port,
                                cable_validation_username,
                                cable_validation_password):
    '''
    Send request for cable validation report
    :param cable_validation_server_address:
    :param cable_validation_request_port:
    :param cable_validation_username:
    :param cable_validation_password:
    '''
    # 1 create cookies file 
    # 2. using cookies file get cable validation report
    response = post_request_with_cookies(cable_validation_server_address,
                                cable_validation_request_port,
                                cable_validation_username,
                                cable_validation_password)
    if not response:
        logging.error(f"Failed to get respond for cable validation report request from {cable_validation_server_address}.")
        return {}, ERROR_CODE
    else:
        return json.loads(response.text), SUCCESS_CODE

def parse_ufm_port(link, port_type):
    if port_type == PortType.SOURCE:
        node_description = Constants.source_description_key
        port = Constants.source_port_key
    elif port_type == PortType.DESTINATION:
        node_description = Constants.destination_description_key
        port = Constants.destination_port_key
    else:
        return "", "", "Internal error: incorrect port_type"

    dev_name_split = link[node_description].split(':')
    logging.debug("Parsing UFM {}: {}".format(node_description, dev_name_split))
    try:
        if len(dev_name_split) == 2:
            device = dev_name_split[0]
            if dev_name_split[1].isnumeric():
                port = link[port]
            else:
                director_name_split = dev_name_split[1].split('/')
                if len(director_name_split) == 3:
                    director_name_split[0] = director_name_split[0].split('L')[1]
                    director_name_split[1] = director_name_split[1].split('U')[1]
                    if int(director_name_split[0]) < 10:
                        director_name_split[0] = "0" + director_name_split[0]
                    port = "Blade " + director_name_split[0] \
                        + "_Port " + director_name_split[1] + "/" + director_name_split[2]
                else:
                    error_message = "Failed to parse UFM link node: {}".format(link[node_description])
                    logging.error(error_message)
                    return "", "", error_message
        else:
            port_name_split = dev_name_split[0]
            dev_name_split = link[node_description].split(' ')
            device = dev_name_split[0]
            port = port_name_split
        return device, port, ""
    except KeyError as ke:
        error_message = "Failed to parse UFM link node: {}".format(link[node_description])
        logging.error(error_message)
        return "", "", error_message


def parse_ufm_links(ufm_port):
    ufm_links = set()
    ufm_links_reversed = set()
    links, status_code = get_ufm_links(ufm_port)
    if status_code != SUCCESS_CODE:
        error_message = "Failed to get links from UFM, status_code: {}".format(status_code)
        logging.error(error_message)
        return {}, {}, error_message

    for link in links():
        if Constants.internal_hdr_link in link[Constants.source_description_key] \
                or Constants.internal_hdr_link in link[Constants.destination_description_key]:
            # ignore links from the switches to the aggregation nodes as they are
            # not part of the physical topology and can generate false difference
            continue

        start_device, start_port, error_message = parse_ufm_port(link, PortType.SOURCE)
        if error_message:
            return {}, {}, error_message
        end_device, end_port, error_message = parse_ufm_port(link, PortType.DESTINATION)
        if error_message:
            return {}, {}, error_message

        ufm_links.add(Link(start_device, start_port, end_device, end_port))
        ufm_links_reversed.add(Link(end_device, end_port, start_device, start_port))

    return ufm_links, ufm_links_reversed, ""


def get_port(link, port_type):
    if port_type == PortType.SOURCE:
        return link.start_port.upper()
    elif port_type == PortType.DESTINATION:
        return link.end_port.upper()
    else:
        return ""


def check_miswired(port_type, ndt_unique, ufm_unique, miss_wired, merger=False):
    ndt_dict = {(link.start_dev.upper(), link.end_dev.upper(), get_port(link, port_type))
                : link for link in ndt_unique}
    ufm_dict = {(link.start_dev.upper(), link.end_dev.upper(), get_port(link, port_type))
                : link for link in ufm_unique}

    for start_port, link_ndt in ndt_dict.items():
        link_ufm = ufm_dict.get(start_port)
        if link_ufm:
            if merger:
                miss_wired.append("expected: %s. actual: %s" %(str(link_ndt),str(link_ufm)))
            else:
                miss_wired.append({"expected": str(link_ndt),
                                   "actual": str(link_ufm)})
            print("NDT: actual \"{}\" does not match expected \"{}\"".format(link_ufm, link_ndt), flush=True)

            ndt_unique.remove(link_ndt)
            ufm_unique.remove(link_ufm)

def compare_topologies_ndt_ibdiagnet(timestamp,
                                     ibdiagnet_links, ibdiagnet_links_reverse,
                                     ndt_links, ndt_links_reversed):
    '''
    Compare links created from NDT file and received from ibdiagnet output
    (ibdiagnet2.net_dump)
    :param timestamp:
    :param ibdiagnet_links:
    :param ibdiagnet_links_reverse:
    :param ndt_links:
    :param ndt_links_reversed:
    '''
    # do I need it ???
    if not ndt_links:
        logging.warning("List of NDT links is empty")
    if not ibdiagnet_links:
        logging.warning("List of Ibdiagnet links is empty")

    miss_wired = []
    miss_wired_key = "missing in wire"
    missing_in_ibdiag = []
    missing_in_ibdiag_key = "missing in topology"
    missing_in_ndt = []
    missing_in_ndt_key = "missing in ndt"
    missing_map = {
        miss_wired_key: miss_wired,
        missing_in_ibdiag_key: missing_in_ibdiag,
        missing_in_ndt_key: missing_in_ndt
        }

    ndt_unique = ndt_links - ibdiagnet_links - ibdiagnet_links_reverse
    ibdiagnet_unique = ibdiagnet_links - ndt_links - ndt_links_reversed

    check_miswired(PortType.SOURCE, ndt_unique, ibdiagnet_unique, miss_wired, True)
    check_miswired(PortType.DESTINATION, ndt_unique, ibdiagnet_unique, miss_wired, True)

    while ndt_unique:
        link = str(ndt_unique.pop())
        missing_in_ibdiag.append(link)
        print("NDT: missing in ibdiagnet \"{}\"".format(link), flush=True)

    while ibdiagnet_unique:
        link = str(ibdiagnet_unique.pop())
        missing_in_ndt.append(link)
        print("NDT: missing in NDT \"{}\"".format(link), flush=True)

    report = []
    for category_key, missing_links in missing_map.items():
        for missing_link in missing_links:
            report_item = {"category": category_key,
                           "description": missing_link}
            report.append(report_item)

    if miss_wired or missing_in_ibdiag or missing_in_ndt:
        report_status = "Completed with errors"
    else:
        report_status = "Completed successfully"
        report = "NDT and current topology are fully match"
    
    response = {"status": report_status,
                "error": "",
                "timestamp": timestamp,
                "report": report}

    return response

def compare_topologies(timestamp, ndts_list_file, switch_patterns, host_patterns, ufm_port):
    ndt_links, ndt_links_reversed, error_message = parse_ndt_files(ndts_list_file, switch_patterns, host_patterns)
    if error_message:
        return {"error": error_message,
                "timestamp": timestamp}
    if not ndt_links:
        logging.warning("List of NDT links is empty")
    ufm_links, ufm_links_reversed, error_message = parse_ufm_links(ufm_port)
    if error_message:
        return {"error": error_message,
                "timestamp": timestamp}
    if not ufm_links:
        logging.warning("List of UFM links is empty")

    miss_wired = []
    missing_in_ufm = []
    missing_in_ndt = []

    ndt_unique = ndt_links - ufm_links - ufm_links_reversed
    ufm_unique = ufm_links - ndt_links - ndt_links_reversed

    check_miswired(PortType.SOURCE, ndt_unique, ufm_unique, miss_wired)
    check_miswired(PortType.DESTINATION, ndt_unique, ufm_unique, miss_wired)

    while ndt_unique:
        link = str(ndt_unique.pop())
        missing_in_ufm.append(link)
        print("NDT: missing in UFM \"{}\"".format(link), flush=True)

    while ufm_unique:
        link = str(ufm_unique.pop())
        missing_in_ndt.append(link)
        print("NDT: missing in NDT \"{}\"".format(link), flush=True)

    # put only last 10k into the report
    report = {"miss_wired": miss_wired[-10000:],
              "missing_in_ufm": missing_in_ufm[-10000:],
              "missing_in_ndt": missing_in_ndt[-10000:]}

    response = {"error": "",
                "timestamp": timestamp,
                "report": report}

    return response


def create_node_description_port_label_mapping(nodes_df, port_hierarchy_df):
    """
    Create mapping between node description, port label and port number
    
    Args:
        nodes_df (pd.DataFrame): DataFrame containing node information
        port_hierarchy_df (pd.DataFrame): DataFrame containing port hierarchy information
        
    Returns:
        dict: Dictionary mapping "{node_description}___{port_label}" to port number
    """
    # Create node GUID to description mapping
    node_guid_to_desc = nodes_df.set_index(NODE_GUID_COLUMN)[NODE_DESC_COLUMN].to_dict()
    
    # Initialize the mapping dictionary
    node_description_port_label_to_port_number = {}
    
    # Iterate through port hierarchy to create mappings
    for _, row in port_hierarchy_df.iterrows():
        node_guid = row[NODE_GUID_COLUMN]
        port_num = row[PORT_NUM_COLUMN]
        port_label = row[EXTENDED_LABEL_COLUMN]
        
        # Get node description from GUID
        node_description = node_guid_to_desc.get(node_guid)
        if node_description:
            # Create key in format "node_description___port_label"
            key = f"{node_description}___{port_label}"
            node_description_port_label_to_port_number[key] = port_num
            
    return node_description_port_label_to_port_number
