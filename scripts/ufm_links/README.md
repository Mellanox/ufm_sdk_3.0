UFM Links
--------------------------------------------------------


This plugin is used to get links information via the UFM APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

To export your repository to PYTHONPATH, please run :

   export PYTHONPATH="${PYTHONPATH}:<your ufm_sdk_cookbook path>"


Running using command line arguments :
--------------------------------------------------------

    python3 load_links.py

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
| --logs_level <logs_level> | [logs-config.logs_level](../conf/ufm-devices.sample.cfg#L14) | False | Default is 'info'
| --system <system> | None | False | Option to get specific system links data
| --cable_info <cable_info> | None | True | Option to show cable information [Default = True]
| --monitoring_counters_info <monitoring_counters_info> | None | False | Option to show monitoring counters data [Default = False]

*If command line argument is provided, the corresponding config value will be ignored

