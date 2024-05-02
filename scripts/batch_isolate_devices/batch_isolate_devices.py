import argparse
import csv
from time import sleep
import requests
from base64 import b64encode
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

"""
Example for CSV content:
fc6a1c0300621900,1
fc6a1c03001f1a00,10
fc6a1c0300681b00,8
===,
fc6a1c0300621910,1
fc6a1c03001f1a02,1
fc6a1c0300681b30,1
fc6a1c0300624900,1
fc6a1c03001f5a00,1
fc6a1c0300681b11,1
"""


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
    parser.add_argument("--num_retries", default=10, type=int, help="Number of retries when marking Switch as isolated.")
    parser.add_argument("--sleep_time", default=20, type=int, help="How much time to sleep until the next time we check the isolation job status.")
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
    num_items_to_remove = 0
    for switch, port in switches_info_list:
        num_items_to_remove += 1
        if switch is None and port is None:
            break
        switches.append((switch, port))
    if num_items_to_remove > 0: #We are not in the last batch
        for i in range(num_items_to_remove):
            del switches_info_list[0]
    return switches


def mark_ports_as_isolated(host, authorization_header, ports_to_isolate):
    """
    Isolate ports.
    """

    url = "https://{}/ufmRest/app/unhealthy_ports?force_set=true".format(host)
    payload = {
   "ports": ports_to_isolate,
   "ports_policy":"UNHEALTHY",
   "action":"isolate"
}
    headers = authorization_header
    headers['Content-Type'] = "application/json"
    response = requests.put(url, json=payload, headers=headers, verify=False)
    if response.status_code != 200:
        print("Failed to isolate ports. Error: {}".format(response.text))
        exit(1)


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
    print('Notice - it can take up to 1 minute until the ports are up')


def get_all_ports(host, authorization_header):
    url = "https://{}/ufmRest/resources/ports".format(host)
    response = requests.get(url, headers=authorization_header, verify=False)
    if response.status_code != 200:
        print("Failed to get list of all ports")
        exit(1)
    return response.json()


def get_all_unhealthy_ports(host, authorization_header):
    url = "https://{}/ufmRest/app/unhealthy_ports".format(host)
    response = requests.get(url, headers=authorization_header, verify=False)
    if response.status_code != 200:
        print("Failed to get list of unhealthy ports")
        exit(1)
    return response.json()


def check_if_switch_port_is_unhealthy(unhealthy_ports, switch, port):
    for port in unhealthy_ports:
        if port['UnhealthyGUID'] == switch and port['UnhealthyPortDname'] == port:
            return True
    return False


def get_all_ports_to_isolate_for_switch(ports_info, switch, port_to_keep):
    port_numbers = [str(port['external_number']) for port in ports_info if port['guid'] == switch and port['logical_state'] != 'Down']
    if port_to_keep in port_numbers:
        port_numbers.remove(port_to_keep)
        port_numbers = {switch + "_" + str(port_id) for port_id in port_numbers}
        return port_numbers
    else:
        print('The requested port {} does not exists on switch {}'.format(port_to_keep, switch))
        print('The available ports: {}'.format(port_numbers))
        print('Please fix the input file and rerun the script')
        exit(1)



def main():
    args = parse_args()
    # Validating that the input CSV is valid and getting a list of all the items in it,
    # Including the batch delimiter.
    switches_info = validate_csv_file_and_get_list_of_items(args.file)
    authorization_header = get_authorization_header(args.user, args.password)
    all_ports_info = get_all_ports(args.host, authorization_header)
    # Getting the next batch of switches to work with, and a list of switch_port for the make port healthy.
    switches = get_next_batch(switches_info)
    while len(switches) > 0:
        input("Press Enter key to start the operation on the next batch: {}".format(switches))
        print('Performing operations on {} switches'.format(len(switches)))
        ports_to_isolate = list()
        for switch, port in switches:
            ports_to_isolate += get_all_ports_to_isolate_for_switch(all_ports_info, switch, port)
        
        mark_ports_as_isolated(args.host, authorization_header, ports_to_isolate)

        for i in range(20):
            #Checking if isolated
            print('wait 20s')
            sleep(20)
            print('done sleep')
            counter = 0
            all_unhealthy_ports = get_all_unhealthy_ports(args.host, authorization_header)
            for switch_and_port in ports_to_isolate:
                switch, port = switch_and_port.split('_')
                if not check_if_switch_port_is_unhealthy(all_unhealthy_ports, switch, port):
                    print('switch {} and port {} are not yet in unhealthy state'.format(switch, port))
                    counter += 1
            print('counter is {}'.format(counter))
            if counter == 0:
                print('done for this batch')
                break


        switches = get_next_batch(switches_info)

if __name__ == "__main__":
    main()
