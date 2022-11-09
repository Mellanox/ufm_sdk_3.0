import requests

def get_request(host_ip, protocol, resource, headers):
    request = protocol + '://' + host_ip + resource
    response = requests.get(request, verify=False, headers=headers)
    return response

def post_request(host_ip, protocol, resource, headers, data=None, json=None, session=None):
    request = protocol + '://' + host_ip + resource
    if session:
        response = session.post(request, verify=False, headers=headers, data=data, json=json)
    else:
        response = requests.post(request, verify=False, headers=headers, data=data, json=json)
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

def send_external_event(description):
    ufm_host = "127.0.0.1:8000"
    ufm_protocol = "http"
    resource = "/app/events/external_event"
    headers = {"X-Remote-User": "ufmsystem"}
    payload = {"event_id": 551, "description": description}
    _ = post_request(ufm_host, ufm_protocol, resource, headers, json=payload)