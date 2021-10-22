import requests
import os
import csv
import logging
import json

SUCCESS_CODE = 200


def update_dict_of_dicts(dict_of_dicts, link_dict, bidirectional=False):
    unique_key = link_dict["StartDev"] + ":" + link_dict["StartPort"] + ":" + link_dict["EndDev"] + ":" + \
                 link_dict["EndPort"]
    dict_of_dicts[unique_key] = link_dict
    if bidirectional:
        unique_key = link_dict["EndDev"] + ":" + link_dict["EndPort"] + ":" + link_dict["StartDev"] + ":" + \
                     link_dict["StartPort"]
        dict_of_dicts[unique_key] = link_dict


def parse_switch_to_switch_ndt(ndt_dict_of_dicts, switch_to_switch_path):
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
                    update_dict_of_dicts(ndt_dict_of_dicts, ndt_dict)
                except KeyError as ke:
                    error_message = "No such column: {}, in line: {}".format(ke, index)
                    logging.error(error_message)
                    return error_message
            return ""
    except FileNotFoundError as fnfe:
        error_message = "{} not found: {}".format(switch_to_switch_path, fnfe)
        logging.error(error_message)
        return error_message


def parse_switch_to_host_ndt(ndt_dict_of_dicts, switch_to_host_path):
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
                    update_dict_of_dicts(ndt_dict_of_dicts, ndt_dict, bidirectional=True)
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
    ndt_dict_of_dicts = {}
    ndt_files_dir = os.path.dirname(ndts_list_file)
    # in case somebody deleted ndts.json - unhandled exception, server should be restarted
    with open(ndts_list_file, "r") as file:
        data = json.load(file)
        for ndt_file_entry in data:
            # in case somebody manually changed ndts.json format - unhandled exception, server should be restarted
            ndt_file = ndt_file_entry["file"]
            ndt_type = ndt_file_entry["file_type"]
            if ndt_type == "switch_to_switch":
                error_message = parse_switch_to_switch_ndt(ndt_dict_of_dicts, os.path.join(ndt_files_dir, ndt_file))
                if error_message:
                    return {}, error_message
            elif ndt_type == "switch_to_host":
                error_message = parse_switch_to_host_ndt(ndt_dict_of_dicts, os.path.join(ndt_files_dir, ndt_file))
                if error_message:
                    return {}, error_message
        return ndt_dict_of_dicts, ""


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
    ufm_dict_of_dicts = {}
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

        update_dict_of_dicts(ufm_dict_of_dicts, ufm_dict, bidirectional=True)

    return ufm_dict_of_dicts, ""


def compare_topologies(timestamp, ndts_list_file):
    try:
        ndt_dict_of_dicts, error_message = parse_ndt_files(ndts_list_file)
        if error_message:
            return {"errors": error_message,
                    "timestamp": timestamp}
        ufm_dict_of_dicts, error_message = parse_ufm_links()
        if error_message:
            return {"errors": error_message,
                    "timestamp": timestamp}

        miss_wired = []
        missing_in_ufm = []
        missing_in_ndt = []
        logging.debug("Comparing NDT to UFM")
        if ndt_dict_of_dicts:
            for ndt_key in ndt_dict_of_dicts:
                if ndt_key not in ufm_dict_of_dicts.keys():
                    missing_in_ufm.append({"expected": ndt_key,
                                           "actual": ""})
        else:
            logging.warning("List of NDT links is empty")

        logging.debug("Comparing UFM to NDT")
        if ufm_dict_of_dicts:
            for ufm_key in ufm_dict_of_dicts:
                if ufm_key not in ndt_dict_of_dicts.keys():
                    missing_in_ndt.append({"expected": "",
                                           "actual": ufm_key})
        else:
            logging.warning("List of UFM links is empty")

        # put only last 10k into the report
        report = {"miss_wired": miss_wired[-10000:],
                  "missing_in_ufm": missing_in_ufm[-10000:],
                  "missing_in_ndt": missing_in_ndt[-10000:]}
        response = {"errors": "",
                    "timestamp": timestamp,
                    "report": report}

        return response

    except Exception as global_ex:
        logging.error(global_ex)
