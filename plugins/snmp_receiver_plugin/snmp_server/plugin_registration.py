import requests
import socket

# Getting all the switches in the network
def get_request(host_ip, protocol, resource, headers):
    request = protocol + '://' + host_ip + resource
    response = requests.get(request, verify=False, headers=headers)
    return response

def get_ufm_switches():
    ufm_host = "127.0.0.1:8000"
    ufm_protocol = "http"
    resource = "/resources/systems?type=switch"
    headers = {"X-Remote-User": "ufmsystem"}
    response = get_request(ufm_host, ufm_protocol, resource, headers)
    switch_ips = []
    for switch in response.json():
        switch_ips.append(switch["ip"])
    return switch_ips

# Sending it to UFM as an external event
def post_request(session, host_ip, protocol, resource, headers, data=None, json=None):
    request = protocol + '://' + host_ip + resource
    response = session.post(request, verify=False, headers=headers, data=data, json=json)
    return response

def register_plugin():
    switch_ips = get_ufm_switches()
    credentials = "f_user_id=admin&f_password=admin"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    for ip in switch_ips:
        session = requests.Session()
        # authentication
        _ = post_request(session, ip, "https", "/admin/launch?script=rh&template=login&action=login", headers, data=credentials)
        # registration
        local_hostname = socket.gethostname()
        local_ip = socket.gethostbyname(local_hostname)
        payload = {"cmd": f"snmp-server host {local_ip} traps"}
        _ = post_request(session, ip, "https", "/admin/launch?script=json", headers, json=payload)

if __name__ == "__main__":
    register_plugin()