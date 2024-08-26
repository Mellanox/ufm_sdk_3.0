#!/usr/bin/env python3

import argparse
import csv
from time import sleep
import requests
from base64 import b64encode
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def get_authorization_header(username, password):
    """
    Get the Basic Authorization header.
    Args:
        username (str): The username.
        password (str): The password.
    
    Returns:
        dict: A dictionary containing the Authorization header.
    """
    auth_string = "{}:{}".format(username, password)
    encoded_auth_string = b64encode(auth_string.encode()).decode()
    return {"Authorization": "Basic " + encoded_auth_string}


def parse_args():
    """
    Parse the arguments provided by the user.
    """
    parser = argparse.ArgumentParser(description="This script results in a switch with one port marked as healthy")
    parser.add_argument("-H", "--host", default="localhost", help="UFM host address")
    parser.add_argument("-u", "--user", default="admin", help="UFM user name")
    parser.add_argument("-p", "--password", default="123456", help="UFM password")
    parser.add_argument("--num_retries", default=10, type=int, help="Number of retries when marking Switch as isolated or when waiting for port to be up")
    parser.add_argument("--sleep_time", default=20, type=int, help="How much time to sleep until the next time we check the isolation job status or when waiting for port to be up")
    parser.add_argument("-f", "--file", help="CSV file path", required=True)
    return parser.parse_args()

def fix_bom_if_needed(input):
    """
    Fix the input string in case on BOM
    """
    return input[1:] if input.startswith('\ufeff') else input

def validate_csv_file_and_get_list_of_items(csv_file):
    """
    Validate the CSV file.
    Assuming the first colum is the switch and the second is the port.
    Returns a list of tuples, each tuple is a switch + port, or None + None 
                                                        representing a batch
    """
    switch_ids = set()
    switches_info = list()
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 2:
                print("Invalid CSV file. Each row must have 2 items.")
                exit(1)
            elif row[0] == '===': #Meaning we got to the batch delimiter
                switches_info.append((None, None)) 
                continue
            switch_id = fix_bom_if_needed(row[0])
            port = fix_bom_if_needed(row[1])
            if switch_id in switch_ids:
                print("Invalid CSV file. Switch ID {} appears more than once.".format(switch_id))
                exit(1)
            switch_ids.add(switch_id)
            switches_info.append((switch_id, port))
    print('Input file is valid')
    return switches_info


def get_next_batch(switches_info_list):
    """
    Gets the next batch of items to work with and removes them from the list.
    Returns two sets:
    First - a set of the switches
    Second - a set of the switches and their ports
    """
    switches = list()
    switches_ports = list()
    num_items_to_remove = 0
    for switch, port in switches_info_list:
        num_items_to_remove += 1
        if switch is None and port is None:
            break
        switches.append(switch)
        switches_ports.append(switch + '_' + port)
    if num_items_to_remove > 0: #We are not in the last batch
        for i in range(num_items_to_remove):
            del switches_info_list[0]
    switches_ports = [switches_port[1:] if switches_port.startswith('\ufeff') else switches_port for switches_port in switches_ports]
    return switches, switches_ports


def mark_switches_as_unhealthy(host, authorization_header, switches):
    """
    Isolate switches.
    """

    url = "https://{}/ufmRest/actions".format(host)
    payload = {
    "params": {
               "action": "isolate",
             "device_policy": "UNHEALTHY"
    },
   "action": "mark_device_unhealthy",
   "object_ids": switches,
   "object_type": "System",
   "identifier":"id"
}
    headers = authorization_header
    headers['Content-Type'] = "application/json"
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code != 202:
        print("Failed to isolate switches. Error: {}".format(response.text))
        exit(1)
    location_header = response.headers['Location']
    job_id = location_header.split('/')[-1]
    print('Marking switches as unhealthy is in progress, job id: {}'.format(job_id))
    return job_id


def wait_for_job_done(host, authorization_header, job_id, num_retries=10, sleep_time=20):
    """
    Wait until the job is done.
    """
    url = "https://{}/ufmRest/jobs/{}".format(host, job_id)
    headers = authorization_header
    for i in range(num_retries):
        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                job_status = response.json()['Status']
                if job_status == 'Completed':
                    return True
        except:
            pass
        finally:
            print('Job {} is not complete, waiting 20 sec'.format(job_id))
            sleep(sleep_time)
            print(f'checking again the status for job {job_id}')
    print(f'Max retires reached while waiting for job {job_id}')
    return False

def mark_switches_and_port_as_healthy(host, authorization_header, switch_port_ids):
    url = "https://{}/ufmRest/app/unhealthy_ports".format(host)
    payload = {"ports": switch_port_ids,
                "ports_policy": "HEALTHY"}
    headers = authorization_header
    headers['Content-Type'] = "application/json"
    response = requests.put(url, json=payload, headers=headers, verify=False)
    if response.status_code != 200:
        print("Failed to bring back switches. Error: {}".format(response.text))
        exit(1)
    print('Marked the below ports as active')
    print('{}'.format(switch_port_ids))


def wait_for_ports_to_be_healthy(host, authorization_header, switch_port_ids, number_retries, sleep_time):
    """
    Waiting for given ports not to be listed as Unhealthy
    """
    print('Waiting for the ports to be active')
    url = "https://{}/ufmRest/app/unhealthy_ports".format(host)
    for i in range(number_retries):
        response = requests.get(url, headers=authorization_header, verify=False)
        if response.status_code != 200:
            print("Failed getting list of unhealthy ports. Error: {}".format(response.text))
            exit(1)
        unhealthy_ports = response.json()
        still_unhealthy_ports = []
        for switch_port in switch_port_ids:
            switch, port = switch_port.split('_')
            for unhealthy_port in unhealthy_ports:
                if unhealthy_port['PeerGUID'] == switch and unhealthy_port['PeerPortDname'] == port:
                    still_unhealthy_ports.append((switch, port))
        if len(still_unhealthy_ports) > 0:
            print('Some ports are still unhealthy {}'.format(still_unhealthy_ports))
            print('Waiting {} sec'.format(sleep_time))
            sleep(sleep_time)
        else:
            print('All ports {} are healthy'.format(switch_port_ids))
            return
    print('Reached max retires for ports to be healthy, please check manually and continue to next batch')


def main():
    # args = parse_args()
    # # Validating that the input CSV is valid and getting a list of all the items in it,
    # # Including the batch delimiter.
    # switches_info = validate_csv_file_and_get_list_of_items(args.file)
    # authorization_header = get_authorization_header(args.user, args.password)
    # # Getting the next batch of switches to work with, and a list of switch_port for the make port healthy.
    # switches, switches_ports = get_next_batch(switches_info)
    # while len(switches) > 0:
    #     input("Press Enter key to start the operation on the next batch: {}".format(switches))
    #     print('Performing operations on {} switches'.format(len(switches)))
    #     job_id = mark_switches_as_unhealthy(args.host, authorization_header, switches)
    #     status = wait_for_job_done(args.host, authorization_header, job_id, args.num_retries, args.sleep_time)
    #     if not status:
    #         print(f'Error waiting for job {job_id} to be done')
    #         exit(1)
    #     print('{} switches ports were isolated'.format(str(switches)))
    #     mark_switches_and_port_as_healthy(args.host, authorization_header, switches_ports)
    #     wait_for_ports_to_be_healthy(args.host, authorization_header, switches_ports, args.num_retries, args.sleep_time)
    #     switches, switches_ports = get_next_batch(switches_info)

if __name__ == "__main__":
    main()
