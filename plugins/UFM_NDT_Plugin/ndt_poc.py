
import requests
import configparser
import json
import logging
import os
import argparse
import time
import datetime
import sys
import csv
#import collections

UFM_API_LINKS = 'resources/links'
#NDT_CSV_FILES_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/switch-to-switch.csv'
#NDT_CSV_FILES_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/switch-to-host.csv'
NDT_CSV_SWITCH_TO_SWITCH_FILES_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/switch-to-switch.csv'
NDT_CSV_SWITCH_TO_HOST_FILES_PATH = '/.autodirect/mtrswgwork/nahum/ndt_poc/switch-to-host.csv'
UFM_API_LINKS_RESULT = '/.autodirect/mtrswgwork/nahum/ndt_poc/ufm_links.txt'
UFM_FORMATED_LINKS = '/.autodirect/mtrswgwork/nahum/ndt_poc/ufm_formated_links.txt'
NDT_FORMATED_LINKS = '/.autodirect/mtrswgwork/nahum/ndt_poc/ndt_formated_links.txt'
UFM_COMPARISON_LINKS = '/.autodirect/mtrswgwork/nahum/ndt_poc/ufm_comparison_links.txt'
NDT_COMPARISON_LINKS = '/.autodirect/mtrswgwork/nahum/ndt_poc/ndt_comparison_links.txt'

# initializing the titles and rows list
fields = []
rows = []

UFM_dict_of_dicts = {}
NDT_dict_of_dicts = {}
# reading csv file
def read_csv_from_file(switch_to_switch_path, switch_to_host_path):
    try:
        print("Reading from csv file:" + switch_to_switch_path)
        with open(switch_to_switch_path, 'r') as csvfile:
            # creating a csv reader object
            #csvreader = csv.reader(csvfile)
            dictreader = csv.DictReader(csvfile)
            # extracting field names through first row
            #fields = next(csvreader)
            # printing the field names
            #print('\nField names are:' + ', '.join(field for field in fields))

            # Conversion From NDT to NDT Dictionaries Phase
            #dict_index_key = 0
            for row in dictreader:
                #row = collections.OrderedDict(row)
                #print(dict(row))
                NDT_dict = {}
                #NDT_dict["StartDev"] = row["#StartDevice"] #Nvidia Case
                NDT_dict["StartDev"] = row["#Fields:StartDevice"] #Microsoft Case
                #Port_Name_split = (row["StartPort"]).split(' ')
                Port_Name_split = ((row["StartPort"]).upper()).split(' ')
                if (len(Port_Name_split) == 2):
                    #NDT_dict["StartPort"] = row["StartPort"]
                    NDT_dict["StartPort"] = Port_Name_split[1]
                else:
                    NDT_dict["StartPort"] = row["StartPort"].upper()
                NDT_dict["EndDev"] = row["EndDevice"]
                #Port_Name_split = (row["EndPort"]).split(' ')
                Port_Name_split = ((row["EndPort"]).upper()).split(' ')
                if (len(Port_Name_split) == 2):
                    #NDT_dict["EndPort"] = row["EndPort"]
                    NDT_dict["EndPort"] = Port_Name_split[1]
                else:
                    NDT_dict["EndPort"] = row["EndPort"].upper()
                Unique_Key = NDT_dict["StartDev"] + ":" + NDT_dict["StartPort"] + ":" + NDT_dict["EndDev"] + ":" + NDT_dict["EndPort"]
                NDT_dict_of_dicts[Unique_Key] = NDT_dict
                #if ("SAT11-0101-0903-01IB1-A:BLADE 06_PORT 1/22:SAT11-0101-0903-01IB1-A:BLADE 02_PORT 2/40" == Unique_Key):
                #    pass
                # NDT_dict_of_dicts[dict_index_key] = NDT_dict #For Test Only
                # dict_index_key += 1 #For Test Only
                #Unique_Key = NDT_dict["EndDev"] + ":" + NDT_dict["EndPort"] + ":" + NDT_dict["StartDev"] + ":" + NDT_dict["StartPort"]
                #NDT_dict_of_dicts[Unique_Key] = NDT_dict
            #'''
            print("Reading from csv file:" + switch_to_host_path)
            with open(switch_to_host_path, 'r') as csvfile:
                # creating a csv reader object
                # csvreader = csv.reader(csvfile)
                dictreader = csv.DictReader(csvfile)
                # extracting field names through first row
                # fields = next(csvreader)
                # printing the field names
                # print('\nField names are:' + ', '.join(field for field in fields))

                # Conversion From NDT to NDT Dictionaries Phase
                # dict_index_key = 0
                for row in dictreader:
                    # row = collections.OrderedDict(row)
                    # print(dict(row))
                    NDT_dict = {}
                    NDT_dict["StartDev"] = row["#StartDevice"]
                    #Port_Name_split = (row["StartPort"]).split(' ')
                    NDT_dict["StartPort"] = (row["StartPort"]).upper()
                    #NDT_dict["StartPort"] = Port_Name_split[1]
                    NDT_dict["EndDev"] = row["EndDevice"]
                    Port_Name_split = (row["EndPort"]).split(' ')
                    #NDT_dict["EndPort"] = row["EndPort"]
                    NDT_dict["EndPort"] = Port_Name_split[1]
                    Unique_Key = NDT_dict["StartDev"] + ":" + NDT_dict["StartPort"] + ":" + NDT_dict["EndDev"] + ":" + NDT_dict["EndPort"]
                    NDT_dict_of_dicts[Unique_Key] = NDT_dict
                    # NDT_dict_of_dicts[dict_index_key] = NDT_dict #For Test Only
                    # dict_index_key += 1 #For Test Only
                    Unique_Key = NDT_dict["EndDev"] + ":" + NDT_dict["EndPort"] + ":" + NDT_dict["StartDev"] + ":" + NDT_dict["StartPort"]
                    NDT_dict_of_dicts[Unique_Key] = NDT_dict
            #'''

            #Saving in File
            print("Num of NDT_dict_of_dicts Items:", len(NDT_dict_of_dicts))
            print("NDT_dict_of_dicts Last Item Unique Key:", Unique_Key)
            print("NDT_dict_of_dicts Last Item:", NDT_dict_of_dicts[Unique_Key])
            with open(NDT_FORMATED_LINKS, 'w') as convert_file:
                for key in NDT_dict_of_dicts:
                    convert_file.write(key)
                    convert_file.write(" ")
                    convert_file.write(json.dumps(NDT_dict_of_dicts[key]))
                    convert_file.write("\n")

            # print("dict_index_key:", dict_index_key)  # For Test Only
            # print("NDT_dict_of_dicts Last Item:", NDT_dict_of_dicts[dict_index_key - 1]) #For Test Only

            # extracting each data row one by one
            # for row in csvreader:
            #     rows.append(row)

            # get total number of rows
            # print("Total no. of rows: %d" % (csvreader.line_num))

            #  printing first 5 rows
            #print('\nFirst 5 rows are:\n')
            #for row in rows[:csvreader.line_num]:
            #for row in rows[:5]:
                # parsing each column of a row
                #for col in row:
                #    print("%10s" % col),
                # print(row) #!!!
                # print('\n')

    except Exception as e:
        print(e)

def read_json_from_file(path):
    data = ''
    try:
        with open(path) as f:
            data = json.load(f)
        print("Finished reading from json file"+"{path}")
    except Exception as e:
        print(e)
    return data


def write_json_to_file(path, json_obj):
    try:
        f = open(path, "w")
        #f.write(json.dumps(json_obj))
        for x in json_obj:
            f.write(json.dumps(x))
            f.write("\n\n")
        f.close()
        print("Finished writing to json file" + "{path}")
    except Exception as e:
        print(e)


def send_ufm_request(url):
    # ufm_host = get_config_value(args.ufm_host, 'ufm-remote-server-config', 'host',
    #                             '127.0.0.1' if local_streaming else None)
    # ufm_protocol = get_config_value(args.ufm_protocol, 'ufm-remote-server-config', 'ws_protocol',
    #                                 'http' if local_streaming else None)
    # ufm_username = get_config_value(args.ufm_username, 'ufm-remote-server-config', 'username', None)
    # ufm_password = get_config_value(args.ufm_password, 'ufm-remote-server-config', 'password', None)
    ufm_protocol = "https"
    ufm_host = "10.213.0.4" #127.0.0.1 ?!
    #ufm_host = "127.0.0.1"
    ufm_username = "admin"
    ufm_password = "123456"
    url = ufm_protocol + '://' + ufm_host + '/ufmRest/' + url
    headers = {}
    # token auth: to be done
    # if token:
    #    headers = {"Authorization": "Bearer " + token['access_token']}
    try:
        print("Send UFM API Request, URL:"+url)
        #response = requests.get(url, verify=False, headers=headers, auth=(ufm_username, ufm_password))
        response = requests.get(url, verify=False, headers=headers, auth=(ufm_username, ufm_password))
        print("UFM API Request Status [" + str(response.status_code) + "], URL "+url)
        if response.raise_for_status():
            print(response.raise_for_status())
        return response.json()
    except Exception as e:
        print(e)

#Get links from via UFM Rest API
def get_ufm_links():
    stored_links_api = send_ufm_request(UFM_API_LINKS)
    #write_json_to_file(UFM_API_LINKS_RESULT, stored_links_api)
    return stored_links_api

# if run as main module
if __name__ == "__main__":
    try:
        # init app args
        #args = parse_args()

        # init app configurations
        #CONFIG = configparser.RawConfigParser()
        #CONFIG.read(CONFIG_FILE)

        # init logging configuration
        #init_logging_config()

        # check app parameters
        #check_app_params()

        # if not streaming:
        #     logging.warning("Streaming flag is disabled, please enable it from the configurations")
        #     sys.exit()

        # load_fluentd_metadata_json()
        # if streaming_interval_is_valid():
        #     ufm_new_version = load_ufm_versioning_api()
        #     if ufm_new_version is None:
        #         sys.exit()
        #     load_memory_with_jsons()
        #     update_ufm_apis(ufm_new_version)
        #     stream_to_fluentd()
        # else:
        #     logging.error("Streaming interval isn't completed")

        links = get_ufm_links()
        '''
        json_formatted_str = json.dumps(links, indent=4)
        print(json_formatted_str)
        links_dict = json.loads(json_formatted_str)
        print(links_dict)
        '''

        '''
        for x in links:
            print(json.dumps(x))
            print("\n\n")
        '''
        # Conversion From Links to Links Dictionaries Phase
        dict_index_key = 0
        for x in links:
            UFM_dict = {}
            Dev_Name_split = ((x["source_port_node_description"]).upper()).split(':')
            if ( len(Dev_Name_split) == 2):
                UFM_dict["StartDev"] = Dev_Name_split[0]
                #UFM_dict["StartPort"] = Dev_Name_split[1]
                if Dev_Name_split[1].isnumeric():
                    UFM_dict["StartPort"] = x["source_port"]
                else:
                    #UFM_dict["StartPort"] = x["source_port"]
                    Director_Name_split = ((Dev_Name_split[1]).upper()).split('/')
                    Director_Name_split[0] = Director_Name_split[0].split('L')[1]
                    Director_Name_split[1] = Director_Name_split[1].split('U')[1]
                    if (int(Director_Name_split[0]) < 10):
                        Director_Name_split[0] = "0"+Director_Name_split[0]
                    UFM_dict["StartPort"] = "BLADE "+Director_Name_split[0]+"_PORT "+Director_Name_split[1]+"/"+Director_Name_split[2]
            else:
                Port_Name_split = Dev_Name_split[0]
                Dev_Name_split = ((x["source_port_node_description"]).upper()).split(' ')
                UFM_dict["StartDev"] = Dev_Name_split[0]
                UFM_dict["StartPort"] = Port_Name_split
            #UFM_dict["StartPort"] = x["source_port"]
            Dev_Name_split = ((x["destination_port_node_description"]).upper()).split(':')
            if ( len(Dev_Name_split) == 2):
                UFM_dict["EndDev"] = Dev_Name_split[0]
                if Dev_Name_split[1].isnumeric():
                    UFM_dict["EndPort"] = x["destination_port"]
                else:
                    #UFM_dict["StartPort"] = Dev_Name_split[1]
                    #UFM_dict["EndPort"] = x["destination_port"]
                    Director_Name_split = ((Dev_Name_split[1]).upper()).split('/')
                    Director_Name_split[0] = Director_Name_split[0].split('L')[1]
                    Director_Name_split[1] = Director_Name_split[1].split('U')[1]
                    if (int(Director_Name_split[0]) < 10):
                        Director_Name_split[0] = "0"+Director_Name_split[0]
                    UFM_dict["EndPort"] = "BLADE " + Director_Name_split[0] + "_PORT " + Director_Name_split[1] + "/" + Director_Name_split[2]
            else:
                Port_Name_split = Dev_Name_split[0]
                Dev_Name_split = ((x["destination_port_node_description"]).upper()).split(' ')
                UFM_dict["EndDev"] = Dev_Name_split[0]
                UFM_dict["EndPort"] = Port_Name_split
            #UFM_dict["EndDev"] = Dev_Name_split[0]
            #UFM_dict["EndPort"] = x["destination_port"]
            #UFM_dict["EndPort"] = Dev_Name_split[1]
            Unique_Key = UFM_dict["StartDev"] + ":" + UFM_dict["StartPort"] + ":" + UFM_dict["EndDev"] + ":" + UFM_dict["EndPort"]
            #Unique_Key = UFM_dict["StartDev"]+":"+UFM_dict["StartPort"]+":"+UFM_dict["EndDev"]+":"+UFM_dict["EndPort"]
            UFM_dict_of_dicts[Unique_Key] = UFM_dict
            #UFM_dict_of_dicts[dict_index_key] = UFM_dict #For Test Only
            #dict_index_key+=1 #For Test Only
            Unique_Key = UFM_dict["EndDev"] + ":" + UFM_dict["EndPort"] + ":" + UFM_dict["StartDev"] + ":" + UFM_dict["StartPort"]
            UFM_dict_of_dicts[Unique_Key] = UFM_dict

            # UFM_dict = {}
            # Dev_Name_split = ((x["destination_port_node_description"]).upper()).split(':')
            # UFM_dict["StartDev"] = Dev_Name_split[0]
            # UFM_dict["StartPort"] = x["destination_port"]
            # Dev_Name_split = ((x["source_port_node_description"]).upper()).split(':')
            # UFM_dict["EndDev"] = Dev_Name_split[0]
            # UFM_dict["EndPort"] = x["source_port"]
            # Unique_Key = UFM_dict["StartDev"] + ":" + UFM_dict["StartPort"] + ":" + UFM_dict["EndDev"] + ":" + UFM_dict["EndPort"]
            # # Unique_Key = UFM_dict["StartDev"]+":"+UFM_dict["StartPort"]+":"+UFM_dict["EndDev"]+":"+UFM_dict["EndPort"]
            # UFM_dict_of_dicts[Unique_Key] = UFM_dict

        print("Num of UFM_dict_of_dicts Items:", len(UFM_dict_of_dicts))
        print("UFM_dict_of_dicts Last Item Unique Key:", Unique_Key)
        print("UFM_dict_of_dicts Last Item:", UFM_dict_of_dicts[Unique_Key])
        # Saving in File
        with open(UFM_FORMATED_LINKS, 'w') as convert_file:
            for key in UFM_dict_of_dicts:
                convert_file.write(key)
                convert_file.write(" ")
                convert_file.write(json.dumps(UFM_dict_of_dicts[key]))
                convert_file.write("\n")

        #print("dict_index_key:", dict_index_key) #For Test Only
        #print("UFM_dict_of_dicts Last Item:", UFM_dict_of_dicts[dict_index_key-1])  #For Test Only

        read_csv_from_file(NDT_CSV_SWITCH_TO_SWITCH_FILES_PATH, NDT_CSV_SWITCH_TO_HOST_FILES_PATH)

        #Comparison Phases

        #Comparison NDT to UFM Phase
        NDT_dict_of_dicts_ufm_missing = []
        for ndt_key in NDT_dict_of_dicts:
            #ufm_key = NDT_dict_of_dicts[ndt_key]
            #if ufm_key in UFM_dict_of_dicts.keys()
            if ndt_key in UFM_dict_of_dicts.keys():
                pass
                #NDT_dict_of_dicts_ufm_missing.append(NDT_dict_of_dicts[ndt_key])
            else:
                pass
                NDT_dict_of_dicts_ufm_missing.append(NDT_dict_of_dicts[ndt_key])
                #NDT_dict_of_dicts_ufm_missing.append(ndt_key)
        print("Num of NDT_dict_of_dicts_ufm_missing Items:", len(NDT_dict_of_dicts_ufm_missing))
        # Saving in File
        with open(NDT_COMPARISON_LINKS, 'w') as convert_file:
            for item in NDT_dict_of_dicts_ufm_missing:
                convert_file.write(json.dumps(item))
                convert_file.write("\n")

        #Comparison UFM to NDT Phase
        UFM_dict_of_dicts_ndt_missing = []
        for ndt_key in UFM_dict_of_dicts:
            #ufm_key = NDT_dict_of_dicts[ndt_key]
            #if ufm_key in UFM_dict_of_dicts.keys()
            if ndt_key in NDT_dict_of_dicts.keys():
                pass
                #UFM_dict_of_dicts_ndt_missing.append(UFM_dict_of_dicts[ndt_key])
            else:
                pass
                UFM_dict_of_dicts_ndt_missing.append(UFM_dict_of_dicts[ndt_key])
                #UFM_dict_of_dicts_ndt_missing.append(ndt_key)
        print("Num of UFM_dict_of_dicts_ndt_missing Items:", len(UFM_dict_of_dicts_ndt_missing))
        # Saving in File
        with open(UFM_COMPARISON_LINKS, 'w') as convert_file:
            for item in UFM_dict_of_dicts_ndt_missing:
                convert_file.write(json.dumps(item))
                convert_file.write("\n")



    except Exception as global_ex:
        print(global_ex)
