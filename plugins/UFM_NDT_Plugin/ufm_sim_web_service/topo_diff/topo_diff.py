import requests
import os
import csv
import logging
import json


def parse_switch_to_switch_ndt(ndt_dict_of_dicts, switch_to_switch_path):
    logging.debug("Reading from csv file:" + switch_to_switch_path)
    with open(switch_to_switch_path, 'r') as csvfile:
        dictreader = csv.DictReader(csvfile)

        for row in dictreader:
            ndt_dict = {}
            ndt_dict["StartDev"] = row["#StartDevice"]  # Nvidia Case
            # NDT_dict["StartDev"] = row["#Fields:StartDevice"] #Microsoft Case
            port_name_split = ((row["StartPort"]).upper()).split(' ')
            if (len(port_name_split) == 2):
                ndt_dict["StartPort"] = port_name_split[1]
            else:
                ndt_dict["StartPort"] = row["StartPort"].upper()
            ndt_dict["EndDev"] = row["EndDevice"]
            port_name_split = ((row["EndPort"]).upper()).split(' ')
            if (len(port_name_split) == 2):
                ndt_dict["EndPort"] = port_name_split[1]
            else:
                ndt_dict["EndPort"] = row["EndPort"].upper()
            unique_key = ndt_dict["StartDev"] + ":" + ndt_dict["StartPort"] + ":" + ndt_dict["EndDev"] + ":" + \
                         ndt_dict["EndPort"]
            ndt_dict_of_dicts[unique_key] = ndt_dict


def parse_switch_to_host_ndt(ndt_dict_of_dicts, switch_to_host_path):
    logging.debug("Reading from csv file:" + switch_to_host_path)
    with open(switch_to_host_path, 'r') as csvfile:
        dictreader = csv.DictReader(csvfile)

        for row in dictreader:
            ndt_dict = {}
            ndt_dict["StartDev"] = row["#StartDevice"]
            ndt_dict["StartPort"] = (row["StartPort"]).upper()
            ndt_dict["EndDev"] = row["EndDevice"]
            port_name_split = (row["EndPort"]).split(' ')
            ndt_dict["EndPort"] = port_name_split[1]
            unique_key = ndt_dict["StartDev"] + ":" + ndt_dict["StartPort"] + ":" + ndt_dict["EndDev"] + ":" + \
                         ndt_dict["EndPort"]
            ndt_dict_of_dicts[unique_key] = ndt_dict
            unique_key = ndt_dict["EndDev"] + ":" + ndt_dict["EndPort"] + ":" + ndt_dict["StartDev"] + ":" + \
                         ndt_dict["StartPort"]
            ndt_dict_of_dicts[unique_key] = ndt_dict


def parse_ndt_files(ndts_list_file):
    ndt_dict_of_dicts = {}
    ndt_files_dir = os.path.dirname(ndts_list_file)
    try:
        with open(ndts_list_file, "r") as file:
            data = json.load(file)
            for ndt_file_entry in data:
                ndt_file = ndt_file_entry["file"]
                ndt_type = ndt_file_entry["file_type"]
                if ndt_type == "switch_to_switch":
                    parse_switch_to_switch_ndt(ndt_dict_of_dicts, os.path.join(ndt_files_dir, ndt_file))
                elif ndt_type == "switch_to_host":
                    parse_switch_to_host_ndt(ndt_dict_of_dicts, os.path.join(ndt_files_dir, ndt_file))
    except Exception as e:
        logging.error(e)
    finally:
        return ndt_dict_of_dicts


def get_ufm_links():
    ufm_host = "127.0.0.1"
    # ufm_protocol = "http"
    # ufm_username = "ufmsystem"
    # ufm_password = ""
    ufm_protocol = "https"
    ufm_username = "admin"
    ufm_password = "123456"
    request = ufm_protocol + '://' + ufm_host + '/ufmRest/resources/links'
    headers = {}
    try:
        logging.info("Send UFM API Request, URL:" + request)
        response = requests.get(request, verify=False, headers=headers, auth=(ufm_username, ufm_password))
        logging.info("UFM API Request Status [" + str(response.status_code) + "], URL " + request)
        if response.raise_for_status():
            logging.warning(response.raise_for_status())
        return response.json()
    except Exception as e:
        logging.error(e)


def parse_ufm_links():
    ufm_dict_of_dicts = {}
    links = get_ufm_links()
    if not links:
        return ufm_dict_of_dicts

    for link in get_ufm_links():
        ufm_dict = {}

        # logging.debug("Parsing source_port_node_description")
        dev_name_split = ((link["source_port_node_description"]).upper()).split(':')
        if (len(dev_name_split) == 2):
            ufm_dict["StartDev"] = dev_name_split[0]
            if dev_name_split[1].isnumeric():
                ufm_dict["StartPort"] = link["source_port"]
            else:
                director_name_split = ((dev_name_split[1]).upper()).split('/')
                director_name_split[0] = director_name_split[0].split('L')[1]
                director_name_split[1] = director_name_split[1].split('U')[1]
                if (int(director_name_split[0]) < 10):
                    director_name_split[0] = "0" + director_name_split[0]
                ufm_dict["StartPort"] = "BLADE " + director_name_split[0] \
                                        + "_PORT " + director_name_split[1] + "/" + director_name_split[2]
        else:
            port_name_split = dev_name_split[0]
            dev_name_split = ((link["source_port_node_description"]).upper()).split(' ')
            ufm_dict["StartDev"] = dev_name_split[0]
            ufm_dict["StartPort"] = port_name_split

        # logging.debug("Parsing destination_port_node_description")
        dev_name_split = ((link["destination_port_node_description"]).upper()).split(':')
        if (len(dev_name_split) == 2):
            ufm_dict["EndDev"] = dev_name_split[0]
            if dev_name_split[1].isnumeric():
                ufm_dict["EndPort"] = link["destination_port"]
            else:
                director_name_split = ((dev_name_split[1]).upper()).split('/')
                director_name_split[0] = director_name_split[0].split('L')[1]
                director_name_split[1] = director_name_split[1].split('U')[1]
                if (int(director_name_split[0]) < 10):
                    director_name_split[0] = "0" + director_name_split[0]
                ufm_dict["EndPort"] = "BLADE " + director_name_split[0] \
                                      + "_PORT " + director_name_split[1] + "/" + director_name_split[2]
        else:
            port_name_split = dev_name_split[0]
            dev_name_split = ((link["destination_port_node_description"]).upper()).split(' ')
            ufm_dict["EndDev"] = dev_name_split[0]
            ufm_dict["EndPort"] = port_name_split

        unique_key = ufm_dict["StartDev"] + ":" + ufm_dict["StartPort"] \
                     + ":" + ufm_dict["EndDev"] + ":" + ufm_dict["EndPort"]
        ufm_dict_of_dicts[unique_key] = ufm_dict
        unique_key = ufm_dict["EndDev"] + ":" + ufm_dict["EndPort"] \
                     + ":" + ufm_dict["StartDev"] + ":" + ufm_dict["StartPort"]
        ufm_dict_of_dicts[unique_key] = ufm_dict

    return ufm_dict_of_dicts


def compare_topologies(timestamp, ndts_list_file):
    try:
        ndt_dict_of_dicts = parse_ndt_files(ndts_list_file)
        ufm_dict_of_dicts = parse_ufm_links()

        report = []
        logging.debug("Comparing NDT to UFM")
        if ndt_dict_of_dicts:
            for ndt_key in ndt_dict_of_dicts:
                if ndt_key not in ufm_dict_of_dicts.keys():
                    report.append({"expected": ndt_key,
                                   "actual": ""})
        else:
            logging.warning("List of NDT links is empty")

        logging.debug("Comparing UFM to NDT")
        if ufm_dict_of_dicts:
            for ufm_key in ufm_dict_of_dicts:
                if ufm_key not in ndt_dict_of_dicts.keys():
                    report.append({"expected": "",
                                   "actual": ufm_key})
        else:
            logging.warning("List of UFM links is empty")

        response = {"errors": "",
                    "timestamp": timestamp,
                    "report": report}

        return response

    except Exception as global_ex:
        logging.error(global_ex)