import requests
import os
import csv
import logging
import json

SUCCESS_CODE = 200


def add_link(links, link_dict, bidirectional=False):
    links.add((link_dict["StartDev"], link_dict["StartPort"], link_dict["EndDev"], link_dict["EndPort"]))
    if bidirectional:
        links.add((link_dict["EndDev"], link_dict["EndPort"], link_dict["StartDev"], link_dict["StartPort"]))


def update_dict_of_dicts(dict_of_dicts, link_dict, bidirectional=False):
    unique_key = link_dict["StartDev"] + ":" + link_dict["StartPort"] + ":" + link_dict["EndDev"] + ":" + \
                 link_dict["EndPort"]
    dict_of_dicts[unique_key] = link_dict
    if bidirectional:
        unique_key = link_dict["EndDev"] + ":" + link_dict["EndPort"] + ":" + link_dict["StartDev"] + ":" + \
                     link_dict["StartPort"]
        dict_of_dicts[unique_key] = link_dict


def parse_switch_to_switch_ndt(ndt_links, switch_to_switch_path):
    logging.debug("Reading from csv file:" + switch_to_switch_path)
    try:
        with open(switch_to_switch_path, 'r') as csvfile:
            dictreader = csv.DictReader(csvfile)
            try:
                _ = iter(dictreader)
            except TypeError as te:
                error_message = "{} is empty or cannot be parsed: {}".format(switch_to_switch_path, te)
                logging.error(error_message)
                return error_message
            for index, row in enumerate(dictreader):
                try:
                    ndt_dict = {}
                    ndt_dict["StartDev"] = row["#StartDevice"]  # Nvidia Case
                    # NDT_dict["StartDev"] = row["#Fields:StartDevice"] #Microsoft Case
                    port_name_split = ((row["StartPort"]).upper()).split(' ')
                    if len(port_name_split) == 2:
                        ndt_dict["StartPort"] = port_name_split[1]
                    else:
                        ndt_dict["StartPort"] = row["StartPort"].upper()
                    ndt_dict["EndDev"] = row["EndDevice"]
                    port_name_split = ((row["EndPort"]).upper()).split(' ')
                    if len(port_name_split) == 2:
                        ndt_dict["EndPort"] = port_name_split[1]
                    else:
                        ndt_dict["EndPort"] = row["EndPort"].upper()
                    add_link(ndt_links, ndt_dict)
                except KeyError as ke:
                    error_message = "No such column: {}, in line: {}".format(ke, index)
                    logging.error(error_message)
                    return error_message
            return ""
    except FileNotFoundError as fnfe:
        error_message = "{} not found: {}".format(switch_to_switch_path, fnfe)
        logging.error(error_message)
        return error_message


def parse_switch_to_host_ndt(ndt_links, switch_to_host_path):
    logging.debug("Reading from csv file:" + switch_to_host_path)
    try:
        with open(switch_to_host_path, 'r') as csvfile:
            dictreader = csv.DictReader(csvfile)
            try:
                _ = iter(dictreader)
            except TypeError as te:
                error_message = "{} is empty or cannot be parsed: {}".format(switch_to_host_path, te)
                logging.error(error_message)
                return error_message
            for index, row in enumerate(dictreader):
                try:
                    ndt_dict = {}
                    ndt_dict["StartDev"] = row["#StartDevice"]
                    ndt_dict["StartPort"] = (row["StartPort"]).upper()
                    ndt_dict["EndDev"] = row["EndDevice"]
                    port_name_split = (row["EndPort"]).split(' ')
                    ndt_dict["EndPort"] = port_name_split[1]
                    add_link(ndt_links, ndt_dict, bidirectional=True)
                except KeyError as ke:
                    error_message = "No such column: {}, in line: {}".format(ke, index)
                    logging.error(error_message)
                    return error_message
            return ""
    except FileNotFoundError as fnfe:
        error_message = "{} not found: {}".format(switch_to_host_path, fnfe)
        logging.error(error_message)
        return error_message


def parse_ndt_files(ndts_list_file):
    ndt_links = set()
    ndt_files_dir = os.path.dirname(ndts_list_file)
    # in case somebody deleted ndts.json - unhandled exception, server should be restarted
    with open(ndts_list_file, "r") as file:
        data = json.load(file)
        for ndt_file_entry in data:
            # in case somebody manually changed ndts.json format - unhandled exception, server should be restarted
            ndt_file = ndt_file_entry["file"]
            ndt_type = ndt_file_entry["file_type"]
            if ndt_type == "switch_to_switch":
                error_message = parse_switch_to_switch_ndt(ndt_links, os.path.join(ndt_files_dir, ndt_file))
                if error_message:
                    return {}, error_message
            elif ndt_type == "switch_to_host":
                error_message = parse_switch_to_host_ndt(ndt_links, os.path.join(ndt_files_dir, ndt_file))
                if error_message:
                    return {}, error_message
        return ndt_links, ""


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


def parse_port(link_type, link, ufm_dict):
    if link_type == "source":
        dev_key = "StartDev"
        port_key = "StartPort"
        node_description = "source_port_node_description"
        port = "source_port"
    elif link_type == "destination":
        dev_key = "EndDev"
        port_key = "EndPort"
        node_description = "destination_port_node_description"
        port = "destination_port"
    else:
        return

    dev_name_split = ((link[node_description]).upper()).split(':')
    logging.debug("Parsing {}: {}".format(node_description, dev_name_split))
    try:
        if len(dev_name_split) == 2:
            ufm_dict[dev_key] = dev_name_split[0]
            if dev_name_split[1].isnumeric():
                ufm_dict[port_key] = link[port]
            else:
                director_name_split = ((dev_name_split[1]).upper()).split('/')
                director_name_split[0] = director_name_split[0].split('L')[1]
                director_name_split[1] = director_name_split[1].split('U')[1]
                if int(director_name_split[0]) < 10:
                    director_name_split[0] = "0" + director_name_split[0]
                ufm_dict[port_key] = "BLADE " + director_name_split[0] \
                                     + "_PORT " + director_name_split[1] + "/" + director_name_split[2]
        else:
            port_name_split = dev_name_split[0]
            dev_name_split = ((link[node_description]).upper()).split(' ')
            ufm_dict[dev_key] = dev_name_split[0]
            ufm_dict[port_key] = port_name_split
        return ""
    except KeyError as ke:
        error_message = "Failed to parse UFM links, wrong key: {}".format(ke)
        logging.error(error_message)
        return error_message


def parse_ufm_links():
    ufm_links = set()
    links, status_code = get_ufm_links()
    if status_code != SUCCESS_CODE:
        error_message = "Failed to get links from UFM, status_code: {}".format(status_code)
        logging.error(error_message)
        return {}, error_message

    for link in links():
        ufm_dict = {}
        error_message = parse_port("source", link, ufm_dict)
        if error_message:
            return {}, error_message
        error_message = parse_port("destination", link, ufm_dict)
        if error_message:
            return {}, error_message

        add_link(ufm_links, ufm_dict, bidirectional=True)

    return ufm_links, ""


def format_link_str(link):
    return "{}/{} - {}/{}".format(link[0], link[1], link[2], link[3])


def compare_topologies(timestamp, ndts_list_file):
    ndt_links, error_message = parse_ndt_files(ndts_list_file)
    if error_message:
        return {"errors": error_message,
                "timestamp": timestamp}
    if not ndt_links:
        logging.warning("List of NDT links is empty")
    ufm_links, error_message = parse_ufm_links()
    if error_message:
        return {"errors": error_message,
                "timestamp": timestamp}
    if not ufm_links:
        logging.warning("List of UFM links is empty")

    miss_wired = []
    missing_in_ufm = []
    missing_in_ndt = []

    ndt_unique = ndt_links - ufm_links
    ufm_unique = ufm_links - ndt_links
    ndt_unique_wo_miss_wired = set()
    while ndt_unique:
        ndt_link = ndt_unique.pop()
        for ufm_link in ufm_unique:
            if ndt_link[0] == ufm_link[0] \
                    and ndt_link[2] == ufm_link[2] \
                    and (ndt_link[1] == ufm_link[1]
                         or ndt_link[3] == ufm_link[3]):
                miss_wired.append({"expected": format_link_str(ndt_link),
                                   "actual": format_link_str(ufm_link)})
                ufm_unique.remove(ufm_link)
                break
        else:
            ndt_unique_wo_miss_wired.add(ndt_link)

    while ndt_unique_wo_miss_wired:
        missing_in_ufm.append(format_link_str(ndt_unique_wo_miss_wired.pop()))

    while ufm_unique:
        missing_in_ndt.append(format_link_str(ufm_unique.pop()))

    # put only last 10k into the report
    report = {"miss_wired": miss_wired[-10000:],
              "missing_in_ufm": missing_in_ufm[-10000:],
              "missing_in_ndt": missing_in_ndt[-10000:]}
    response = {"errors": "",
                "timestamp": timestamp,
                "report": report}

    return response
