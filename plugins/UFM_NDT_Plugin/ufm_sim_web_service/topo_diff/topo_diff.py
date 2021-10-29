import requests
import os
import csv
import logging
import json
import syslog
import re

SUCCESS_CODE = 200


class Constants:
    # NDT keys
    start_device_key = "#StartDevice"  # Nvidia case
    # start_device_key = "#Fields:StartDevice"  # Microsoft Case
    start_port_key = "StartPort"
    end_device_key = "EndDevice"
    end_port_key = "EndPort"

    # UFM keys
    source_description_key = "source_port_node_description"
    source_port_key = "source_port"
    destination_description_key = "destination_port_node_description"
    destination_port_key = "destination_port"

    switch_to_switch_patterns = (r"^Port (\d+)$", r"(^Blade \d+_Port \d+/\d+$)")
    switch_to_host_patterns = (r"^Port (\d+)$", r"(^SAT\d+ ibp.*$)")


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


def parse_ndt_port(port_string, patterns):
    for pattern in patterns:
        match = re.match(pattern, port_string)
        if match:
            return match.group(1)

    return ""


def parse_ndt_file(ndt_links, ndt_file, ndt_links_reversed=None):
    logging.debug("Reading from csv file:" + ndt_file)
    try:
        with open(ndt_file, 'r') as csvfile:
            dictreader = csv.DictReader(csvfile)
            try:
                _ = iter(dictreader)
            except TypeError as te:
                error_message = "{} is empty or cannot be parsed: {}".format(ndt_file, te)
                logging.error(error_message)
                return error_message
            if ndt_links_reversed is None:
                patterns = Constants.switch_to_switch_patterns
            else:
                patterns = Constants.switch_to_host_patterns
            for index, row in enumerate(dictreader):
                logging.debug("Parsing NDT link: {}".format(row))
                try:
                    start_dev = row[Constants.start_device_key]
                    start_port = parse_ndt_port(row[Constants.start_port_key], patterns)
                    if not start_port:
                        error_message = "Failed to parse start port: {}, in line: {}" \
                            .format(row[Constants.start_port_key], index)
                        logging.error(error_message)
                        return error_message
                    end_dev = row[Constants.end_device_key]
                    end_port = parse_ndt_port(row[Constants.end_port_key], patterns)
                    if not end_port:
                        error_message = "Failed to parse end port: {}, in line: {}" \
                            .format(row[Constants.end_port_key], index)
                        logging.error(error_message)
                        return error_message
                    ndt_links.add(Link(start_dev, start_port, end_dev, end_port))
                    if ndt_links_reversed is not None:
                        ndt_links_reversed.add(Link(end_dev, end_port, start_dev, start_port))
                except KeyError as ke:
                    error_message = "No such column: {}, in line: {}".format(ke, index)
                    logging.error(error_message)
                    return error_message
            return ""
    except FileNotFoundError as fnfe:
        error_message = "{} not found: {}".format(ndt_file, fnfe)
        logging.error(error_message)
        return error_message


def parse_ndt_files(ndts_list_file):
    ndt_links = set()
    ndt_links_reversed = set()
    ndt_files_dir = os.path.dirname(ndts_list_file)
    # in case somebody deleted ndts.json - unhandled exception, server should be restarted
    with open(ndts_list_file, "r") as file:
        data = json.load(file)
        for ndt_file_entry in data:
            # in case somebody manually changed ndts.json format - unhandled exception, server should be restarted
            ndt_file = ndt_file_entry["file"]
            ndt_type = ndt_file_entry["file_type"]
            error_message = parse_ndt_file(ndt_links,
                                           os.path.join(ndt_files_dir, ndt_file),
                                           ndt_links_reversed if ndt_type == "switch_to_host" else None)
            if error_message:
                return {}, error_message
        return ndt_links, ndt_links_reversed, ""


def get_request(host_ip, protocol, resource, user, password, headers):
    request = protocol + '://' + host_ip + resource
    response = requests.get(request, verify=False, headers=headers, auth=(user, password))
    logging.info("UFM API Request Status: {}, URL: {}".format(response.status_code, request))
    return response


def get_ufm_links():
    ufm_host = "127.0.0.1:8000"
    ufm_protocol = "http"
    ufm_username = "ufmsystem"
    resource = "/resources/links"
    ufm_password = ""
    headers = {'X-Remote-User': ufm_username}
    response = get_request(ufm_host, ufm_protocol, resource, ufm_username, ufm_password, headers)
    if response.status_code != SUCCESS_CODE:
        return {}, response.status_code
    else:
        return response.json, SUCCESS_CODE


def parse_ufm_port(link, node_description, port):
    dev_name_split = link[node_description].split(':')
    logging.debug("Parsing UFM {}: {}".format(node_description, dev_name_split))
    try:
        if len(dev_name_split) == 2:
            device = dev_name_split[0]
            if dev_name_split[1].isnumeric():
                port = link[port]
            else:
                director_name_split = dev_name_split[1].split('/')
                director_name_split[0] = director_name_split[0].split('L')[1]
                director_name_split[1] = director_name_split[1].split('U')[1]
                if int(director_name_split[0]) < 10:
                    director_name_split[0] = "0" + director_name_split[0]
                port = "Blade " + director_name_split[0] \
                       + "_Port " + director_name_split[1] + "/" + director_name_split[2]
        else:
            port_name_split = dev_name_split[0]
            dev_name_split = link[node_description].split(' ')
            device = dev_name_split[0]
            port = port_name_split
        return device, port, ""
    except KeyError as ke:
        error_message = "Failed to parse UFM links, wrong key: {}".format(ke)
        logging.error(error_message)
        return "", "", error_message


def parse_ufm_links():
    ufm_links = set()
    ufm_links_reversed = set()
    links, status_code = get_ufm_links()
    if status_code != SUCCESS_CODE:
        error_message = "Failed to get links from UFM, status_code: {}".format(status_code)
        logging.error(error_message)
        return {}, error_message

    for link in links():
        start_dev, start_port, error_message = parse_ufm_port(link,
                                                              Constants.source_description_key,
                                                              Constants.source_port_key)
        if error_message:
            return {}, error_message
        end_dev, end_port, error_message = parse_ufm_port(link,
                                                          Constants.destination_description_key,
                                                          Constants.destination_port_key)
        if error_message:
            return {}, error_message

        ufm_links.add(Link(start_dev, start_port, end_dev, end_port))
        ufm_links_reversed.add(Link(end_dev, end_port, start_dev, start_port))

    return ufm_links, ufm_links_reversed, ""


def links_miss_wired(link_left, link_right):
    return link_left.start_dev == link_right.start_dev \
           and link_left.end_dev == link_right.end_dev \
           and (link_left.start_port == link_right.start_port
                or link_left.end_port == link_right.end_port)


def compare_topologies(timestamp, ndts_list_file):
    ndt_links, ndt_links_reversed, error_message = parse_ndt_files(ndts_list_file)
    if error_message:
        return {"error": error_message,
                "timestamp": timestamp}
    if not ndt_links:
        logging.warning("List of NDT links is empty")
    ufm_links, ufm_links_reversed, error_message = parse_ufm_links()
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
    ndt_unique_wo_miss_wired = set()
    while ndt_unique:
        ndt_link = ndt_unique.pop()
        for ufm_link in ufm_unique:
            if links_miss_wired(ndt_link, ufm_link):
                miss_wired.append({"expected": str(ndt_link),
                                   "actual": str(ufm_link)})
                syslog.syslog("NDT: actual \"{}\" doesn't match expected \"{}\"".format(str(ufm_link), str(ndt_link)))
                ufm_unique.remove(ufm_link)
                break
        else:
            ndt_unique_wo_miss_wired.add(ndt_link)

    while ndt_unique_wo_miss_wired:
        link = str(ndt_unique_wo_miss_wired.pop())
        missing_in_ufm.append(link)
        syslog.syslog("NDT: missing in UFM \"{}\"".format(link))

    while ufm_unique:
        link = str(ufm_unique.pop())
        missing_in_ndt.append(link)
        syslog.syslog("NDT: missing in NDT \"{}\"".format(link))
        syslog.openlog()

    # put only last 10k into the report
    report = {"miss_wired": miss_wired[-10000:],
              "missing_in_ufm": missing_in_ufm[-10000:],
              "missing_in_ndt": missing_in_ndt[-10000:]}
    response = {"error": "",
                "timestamp": timestamp,
                "report": report}

    return response
