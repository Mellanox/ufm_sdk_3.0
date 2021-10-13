import requests
import os
import csv


def parse_switch_to_switch_ndt(ndt_dict_of_dicts, switch_to_switch_path):
    print("Reading from csv file:" + switch_to_switch_path)
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
    print("Reading from csv file:" + switch_to_host_path)
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


# reading csv file
def parse_ndt_files():
    ndt_dict_of_dicts = {}
    try:
        ndt_dir = "ndt_files"
        for ndt_file in os.listdir(ndt_dir):  # TODO: replace with constant
            if "switch_to_switch" in ndt_file:
                parse_switch_to_switch_ndt(ndt_dict_of_dicts, os.path.join(ndt_dir, ndt_file))
            elif "switch_to_host" in ndt_file:
                parse_switch_to_host_ndt(ndt_dict_of_dicts, os.path.join(ndt_dir, ndt_file))
    except Exception as e:
        print(e)
    finally:
        return ndt_dict_of_dicts


def get_ufm_links():
    ufm_protocol = "https"
    ufm_host = "swx-tol"
    ufm_username = "admin"
    ufm_password = "123456"
    request = ufm_protocol + '://' + ufm_host + '/ufmRest/resources/links'
    headers = {}
    try:
        print("Send UFM API Request, URL:" + request)
        response = requests.get(request, verify=False, headers=headers, auth=(ufm_username, ufm_password))
        print("UFM API Request Status [" + str(response.status_code) + "], URL " + request)
        if response.raise_for_status():
            print(response.raise_for_status())
        return response.json()
    except Exception as e:
        print(e)


def parse_ufm_links():
    ufm_dict_of_dicts = {}

    for link in get_ufm_links():
        ufm_dict = {}

        # parse source_port_node_description
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

        # parse source_port_node_description
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


def main(timestamp):
    try:
        ndt_dict_of_dicts = parse_ndt_files()
        ufm_dict_of_dicts = parse_ufm_links()

        report = []
        # compare NDT to UFM
        for ndt_key in ndt_dict_of_dicts:
            if ndt_key not in ufm_dict_of_dicts.keys():
                report.append({"expected": ndt_key,
                               "actual": ""})

        # compare UFM to NDT
        for ufm_key in ufm_dict_of_dicts:
            if ufm_key not in ndt_dict_of_dicts.keys():
                report.append({"expected": "",
                               "actual": ufm_key})

        response = {"errors": "",
                    "timestamp": timestamp,
                    "report": report}

        return response

    except Exception as global_ex:
        print(global_ex)
