UFM Ports
--------------------------------------------------------


This plugin is used to set ports policy Healthy/Unhealthy via the UFM Rest APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

To export your repository to PYTHONPATH, please run :

   export PYTHONPATH="${PYTHONPATH}:<your ufm_sdk_cookbook path>"

Run
--------------------------------------------------------
### 1. Get all ports that are marked as healthy from OpenSM in the fabric :

    python3 ufm_set_ports_policy.py --get_unhealthy_ports

### 2. Mark ports as unhealthy :

    python3 ufm_set_ports_policy.py --set_ports_policy --ports=port_number1,port_number2 --ports_policy=UNHEALTHY --action=isolate/no_discover

### 3. Mark unhealthy ports as healthy :

    python3 ufm_set_ports_policy.py --set_ports_policy --ports=port_number1,port_number2 --ports_policy=HEALTHY

### 4. Mark ALL unhealthy ports as healthy at once :

    python3 ufm_set_ports_policy.py --set_ports_policy --ports=ALL --ports_policy=HEALTHY

 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --ufm_host <ufm_host> | [ufm-remote-server-config.host](../conf/ufm-sdk.sample.cfg#L2) | True | Hostname or IP for The UFM Enterprise
| --ufm_protocol <ufm_protocol> | [ufm-server-config.ws_protocol](../conf/ufm-sdk.sample.cfg#L4) | True | Web services protocol used by UFM Enterprise (HTTP, HTTPS)
| --ufm_username <ufm_username> | [ufm-server-config.username](../conf/ufm-sdk.sample.cfg#L6) | True | Username of UFM user
| --ufm_password <ufm_password> | [ufm-server-config.password](../conf/ufm-sdk.sample.cfg#L7) | True | Password of UFM user
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](../conf/ufm-sdk.sample.cfg#L11) | False | Log file name [Default = 'console.log']
| --logs_level <logs_level> | [logs-config.logs_level](../conf/ufm-sdk.sample.cfg#L14) | False | Default is 'info'
| --get_unhealthy_ports <get_unhealthy_ports> | None | True | Get all ports that are marked as healthy from OpenSM in the fabric
| --set_ports_policy <set_ports_policy> | None | True | Option to get set ports policy unhealthy/healthy
| --ports <ports> | None | Required for set_ports_policy operation | The List of ports numbers(comma seprated), Each port number should be a string of NodeGUID_PortNumber(Ex 0002c9030060dc20_10) or Keyword 'ALL'
| --ports_policy <ports_policy> | None | Optional for set_ports_policy operation, the default is UNHEALTHY| The ports policy to be applied on the list of ports, could be one of (UNHEALTHY, HEALTHY)
| --action <action> | None | Optional for set_ports_policy operation, the default is isolate | The action to be applied on the list of ports, could be one of (isolate, no_discover)

*If command line argument is provided, the corresponding config value will be ignored
