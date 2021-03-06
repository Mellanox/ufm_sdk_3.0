import requests
import os
import csv
import logging
import json
import re
from enum import Enum

SUCCESS_CODE = 200


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


def parse_ndt_port(file, row, index, port_type, patterns):
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
    if not port:
        error_message = "Failed to parse {}: {}, in file: {}, line: {}." \
            .format(port_type,
                    row[port_key],
                    file, index)
        logging.error(error_message)
        return "", "", error_message
    else:
        return device, port, ""


def parse_ndt_file(ndt_links, ndt_file, patterns, ndt_links_reversed=None):
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
                        parse_ndt_port(os.path.basename(ndt_file), row, index, PortType.SOURCE, patterns)
                    if error_message:
                        error_response.append(error_message)
                    end_device, end_port, error_message =\
                        parse_ndt_port(os.path.basename(ndt_file), row, index, PortType.DESTINATION, patterns)
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


def check_miswired(port_type, ndt_unique, ufm_unique, miss_wired):
    ndt_dict = {(link.start_dev.upper(), link.end_dev.upper(), get_port(link, port_type))
                : link for link in ndt_unique}
    ufm_dict = {(link.start_dev.upper(), link.end_dev.upper(), get_port(link, port_type))
                : link for link in ufm_unique}

    for start_port, link_ndt in ndt_dict.items():
        link_ufm = ufm_dict.get(start_port)
        if link_ufm:
            miss_wired.append({"expected": str(link_ndt),
                               "actual": str(link_ufm)})
            print("NDT: actual \"{}\" does not match expected \"{}\"".format(link_ufm, link_ndt), flush=True)

            ndt_unique.remove(link_ndt)
            ufm_unique.remove(link_ufm)


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
