UFM Logical Servers Management
--------------------------------------------------------
This feature is deprecated from UFM 6.9 (April 2022). Please refrain to use it
--------------------------------------------------------


This plugin is used to manage the Logical Servers records of the IB fabric via the UFM APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Run
--------------------------------------------------------
### 1. Get all existing environment :

    python3 ufm_logical_servers.py --get_envs

### 2. Get an existing environment:

    python3 ufm_logical_servers.py --get_env=env_name

### 3. Create a new environment:

    python3 ufm_logical_servers.py --create_env --name=env1 --description=optional_description

### 4. Delete an existing environment:

    python3 ufm_logical_servers.py --delete_env=env_name

### 5. Get all existing networks :

    python3 ufm_logical_servers.py --get_networks

### 6. Get an existing network:

    python3 ufm_logical_servers.py --get_network=network_name

### 7. Create a new network:

    python3 ufm_logical_servers.py --create_network --name=env1 --pkey=optional_hexa_pkey --description=optional_description

### 8. Delete an existing network:

    python3 ufm_logical_servers.py --delete_network=network_name

### 9. Get all existing logical servers :

    python3 ufm_logical_servers.py --get_logical_servers

### 10. Create a new logical server:

    python3 ufm_logical_servers.py --create_logical_server --name=ls_name --environment=env_name --description=optional_description

### 11. Delete an existing logical server:

    python3 ufm_logical_servers.py --delete_logical_server --name=ls_name --environment=env_name

### 12. Get all free (unallocated) hosts:

    python3 ufm_logical_servers.py --get_free_hosts

### 13. Allocate hosts to a logical server automatically:

    python3 ufm_logical_servers.py --auto_allocate_hosts --name=ls_name --environment=env_name --total_computes=number_of_hosts_to_be_allocated

### 14. Allocate hosts to a logical server manually:

    python3 ufm_logical_servers.py --allocate_hosts --name=ls_name --environment=env_name --computes=hosts_guids_to_be_allocated

### 15. Add networks interfaces to logical server:

    python3 ufm_logical_servers.py --allocate_hosts --name=ls_name --environment=env_name --networks=networks_names_to_be_added



 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --ufm_host <ufm_host> | [ufm-remote-server-config.host](../conf/ufm-sdk.sample.cfg#L2) | True | Hostname or IP for The UFM Enterprise
| --ufm_protocol <ufm_protocol> | [ufm-server-config.ws_protocol](../conf/ufm-sdk.sample.cfg#L4) | True | Web services protocol used by UFM Enterprise (HTTP, HTTPS)
| --ufm_access_token <ufm_access_token> | [ufm-server-config.access_token](../conf/ufm-sdk.sample.cfg#L5) | True | Access Token of UFM
| --ufm_username <ufm_username> | [ufm-server-config.username](../conf/ufm-sdk.sample.cfg#L6) | True | Username of UFM user
| --ufm_password <ufm_password> | [ufm-server-config.password](../conf/ufm-sdk.sample.cfg#L7) | True | Password of UFM user
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](../conf/ufm-sdk.sample.cfg#L11) | False | Log file name [Default = 'console.log']
| --logs_level <logs_level> | [logs-config.logs_level](../conf/ufm-sdk.sample.cfg#L14) | False | Default is 'info'
| --name <name> | None | True | Option to provide a name for specific element, e.g.:environment, logical server, network
| --description <description> | None | False | Option to set a description for the created element
| --get_envs <get_envs> | None | True | Option to get all existing environments data
| --get_env <get_env> | None | True | Option to get specific environment data
| --create_env <create_env> | None | True | Option to create an UFM environment
| --delete_env <delete_env> | None | True | Option to delete specific environment by it's name
| --get_networks <get_networks> | None | True | Option to get all existing networks data
| --get_network <get_networks> | None | True | Option to get specific network data
| --create_network <create_network> | None | True | Option to create a network
| --delete_network <delete_network> | None | True | Option to delete specific network by it's name
| --environment <environment> | None | Required for Logical servers operations| Option to provide an environment for the created logical server
| --pkey <pkey> | None | Optional for create_network operation| Network Pkey [Hexadecimal string between '0x0'-'0x7fff' exclusive]
| --get_logical_servers <get_logical_servers> | None | True | Option to get all existing logical servers
| --create_logical_server <create_logical_server> | None | True | Option to create a create_logical_server
| --delete_logical_server <delete_logical_server> | None | True | Option to delete specific logical server by it's name
| --get_free_hosts <get_free_hosts> | None | True | Option to get all free (unallocated) hosts
| --auto_allocate_hosts <auto_allocate_hosts> | None | True | Option to allocate hosts automatically to a logical server 
| --total_computes <total_computes> | None | Required for auto_allocate_hosts operation | Total number of Computes to be allocated automatically to a logical server
| --allocate_hosts <allocate_hosts> | None | True | Option to allocate hosts manually to a logical server
| --computes <computes> | None | Required for allocate_hosts operation| Computes GUIDs to be allocated manually to a logical server (comma separated)
| --add_network_interfaces <add_network_interfaces> | None | True | Option to add networks interfaces to a logical server 
| --networks <networks> | None | Required for add_network_interfaces operation | Networks names to be added into a logical server (comma separated)


*If command line argument is provided, the corresponding config value will be ignored

