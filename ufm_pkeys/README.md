UFM Pkeys Management
--------------------------------------------------------


This plugin is used to manage the Pkeys records of the IB fabric via the UFM APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Run
--------------------------------------------------------
### 1. Get all existing pkeys :

    python3 ufm_pkeys.py --get_pkeys

### 2. Get an existing pkey's parameters:

    python3 ufm_pkeys.py --get_pkey=pkey_hexadecimal

### 3. Set a new Pkey or update existing Pkey's parameters and members :

    python3 ufm_pkeys.py --set_pkey --pkey=pkey_hexadecimal --guids=guid1,guid2

### 4. Delete an existing pkey :

    python3 ufm_pkeys.py --delete_pkey=pkey_hexadecimal


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
| --get_pkeys <get_pkeys> | None | True | Option to get all existing pkeys data
| --get_pkey <get_pkey> | None | True | Option to get specific Pkey data
| --delete_pkey <delete_pkey> | None | True | Option to delete specific Pkey
| --set_pkey <set_pkey> | None | True | Option to set a Pkey network
| --pkey <pkey> | None | Required for set_pkey operation | Network Pkey [Hexadecimal string between '0x0'-'0x7fff' exclusive]
| --guids <guids> | None | Required for set_pkey operation | The List of port GUIDs(comma seprated), Each GUID is a hexadecimal string with a minimum length of 16 characters and maximum length of 20 characters,[e.g.043f720300dd1d3c,0c42a103007aca90,etc...] 
| --membership <membership> | None | Optional for set_pkey operation | 'full' / 'limited'. “full”- members with full membership can communicate with all hosts (members)" within the network/partition “limited” - members with limited membership cannot communicate with other members with limited membership. However, communication is allowed between every other combination of membership types. [Default = 'full'].* This parameter will be ignored in case the “memberships” parameter has been set
| --memberships <memberships> | None | Optional for set_pkey operation | List of “full” or “limited” comma-separated strings.It must be the same length as the GUIDs list. Each value by an index represents a GUID membership e.g. ['full', 'limited', etc...]. This parameter conflicts with the “membership” parameter. You must select either a list of memberships or just one membership for all GUIDs
| --index0 <index0> | None | Optional for set_pkey operation | If true, the API will store the PKey at index 0 of the PKey table of the GUID.[Default = False]
| --ip_over_ib <index0> | None | Optional for set_pkey operation | If true, PKey is a member in a multicast group that uses IP over InfiniBand.[Default = True]


*If command line argument is provided, the corresponding config value will be ignored

