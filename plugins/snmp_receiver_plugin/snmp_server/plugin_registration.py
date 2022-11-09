import requests
import socket
import snmp_server.helpers as helpers

# Sending it to UFM as an external event
def post_request(session, host_ip, protocol, resource, headers, data=None, json=None):
    request = protocol + '://' + host_ip + resource
    response = session.post(request, verify=False, headers=headers, data=data, json=json)
    return response

def register_plugin():
    switch_ips = helpers.get_ufm_switches()
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