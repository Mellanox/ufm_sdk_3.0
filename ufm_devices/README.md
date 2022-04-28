UFM Devices Action
--------------------------------------------------------


This plugin is used to run devices action via the UFM APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt


Running using command line arguments :
--------------------------------------------------------
### 1. reboot devices :

    pyhton3 reboot_action.py --object_ids=guid1,guid2.. --description=optional_action_description --object_type=object_type --identifier=identifier --ufm_host=ufm_host --ufm_protocol=ufm_protocol --ufm_username=ufm_username --ufm_password=ufm_password

### 2. sw upgrade:

    python3 sw_upgrade_action.py --object_ids=guid1,guid2..  --username=username --password=password --path=path --image=image --protocol=scp/ftp --server=server_ip --description=optional_action_description --object_type=object_type --identifier=identifier --ufm_host=ufm_host --ufm_protocol=ufm_protocol --ufm_username=ufm_username --ufm_password=ufm_password


Running using configuration file:
--------------------------------------------------------
- copy config file sample ufm-devices.sample.cfg to ufm-devices.cfg


    cp ufm-devices.sample.cfg ufm-devices.cfg

  - Edit config file with relevant parameters


    vi ufm-devices.cfg

  - Run


    pyhton3 reboot_action.py or python3 sw_upgrade_action.py


 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --ufm_host <ufm_host> | [ufm-remote-server-config.host](../conf/ufm-devices.sample.cfg#L2) | True | Hostname or IP for The UFM Enterprise
| --ufm_protocol <ufm_protocol> | [ufm-server-config.ws_protocol](../conf/ufm-devices.sample.cfg#L4) | True | Web services protocol used by UFM Enterprise (HTTP, HTTPS)
| --ufm_access_token <ufm_access_token> | [ufm-server-config.access_token](../conf/ufm-devices.sample.cfg#L5) | True | Access Token of UFM
| --ufm_username <ufm_username> | [ufm-server-config.username](../conf/ufm-devices.sample.cfg#L6) | True | Username of UFM user
| --ufm_password <ufm_password> | [ufm-server-config.password](../conf/ufm-devices.sample.cfg#L7) | True | Password of UFM user
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](../conf/ufm-devices.sample.cfg#L11) | False | Log file name [Default = 'console.log']
| --logs_level <logs_level> | [logs-config.logs_level](../conf/ufm-devices.sample.cfg#L14) | False | Default is 'info'

### 1. reboot devices args:
| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --object_ids <object_ids> | ufm-devices-reboot.object_ids | False | comma separated GUIDs if this arg was not provided the action will be run on all devices in UFM fabric
| --description <description> | ufm-devices-reboot.description | False | Option to set a description for run action
| --object_type <object_type> | ufm-devices-reboot.object_type| False | Option to set object type by default the value will be System
| --identifier <identifier> | ufm-devices-reboot.identifier| False | Option to set identifier by default the value will be id

### 2. sw upgrade:
| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --object_ids <object_ids> | ufm-devices-sw-upgrade.object_ids | False | comma separated GUIDs if this arg was not provided the action will be run on all devices in UFM fabric
| --description <description> | ufm-devices-sw-upgrade.description | False | Option to set a description for run action
| --object_type <object_type> | ufm-devices-sw-upgrade.object_type| False | Option to set object type by default the value will be System
| --identifier <identifier> | ufm-devices-sw-upgrade.identifier| False | Option to set identifier by default the value will be id
| --username <username> | ufm-devices-sw-upgrade.username| True | Option to set user name
| --password <password> | ufm-devices-sw-upgrade.password| True | Option to set password
| --path <path> | ufm-devices-sw-upgrade.path| True | Option to set image path
| --image <image> | ufm-devices-sw-upgrade.image| True | Option to set image name
| --protocol <protocol> | ufm-devices-sw-upgrade.protocol| True | Option to set protocol SCP/FTP
| --server <server> | ufm-devices-sw-upgrade.server| True | Option to set server ip that contain the image

*If command line argument is provided, the corresponding config value will be ignored

