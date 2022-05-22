UFM stream To FluentD endpoint
--------------------------------------------------------


This plugin is used to extract topology via UFM API and stream it via [fluentd](https://www.fluentd.org/) protocol to telemetry console

Overview
--------------------------------------------------------

The UFM Enterprise product is Nvidia’s platform for IB fabric management. Through this platform, the various devices (switches, multi-chip systems, cables, etc.) are discovered, configured and the status of the entire fabric is reflected.
As a fabric manager, the UFM Enterprise holds an internal representation model of the network topology. This topology should be reflected, over time (as it can change with time) towards telemetry console. In order to do so, we present stream To FluentD plugin



Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Fluentd configurations
--------------------------------------------------------

- We provide [fluentd.conf](fluentd.conf) as a fluentd configurations sample.

Run
--------------------------------------------------------
### 1) using command line arguments :


    python3 fluentd_topology_plugin.py --fluentd_host=fluentd_host --fluentd_port=fluentd_port --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password


### 2) using configuration file:

  - copy config file sample fluentd_topology_plugin.sample.cfg to fluentd_topology_plugin.cfg


    cp fluentd_topology_plugin.sample.cfg fluentd_topology_plugin.cfg

  - Edit config file with relevant parameters


    vi fluentd_topology_plugin.cfg

  - Run


    python3 fluentd_topology_plugin.py

 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --fluentd_host <fluentd_host> | [fluentd-config.host](fluentd_topology_plugin.sample.cfg#L20) | True |  Hostname or IP for FluentD endpoint
| --fluentd_port <fluentd_port> | [fluentd-config.port](fluentd_topology_plugin.sample.cfg#L21) | True | Port for FluentD endpoint
| --fluentd_timeout <fluentd_timeout> | [fluentd-config.timeout](fluentd_topology_plugin.sample.cfg#L22) | True | Timeout for FluentD endpoint streaming [Default is 120 seconds]
| --fluentd_message_tag_name <fluentd_message_tag_name> | [fluentd-config.message_tag_name](fluentd_topology_plugin.sample.cfg#L22) | False | Message Tag Name for FluentD endpoint message [Default is the ufm_host]
| --ufm_host <ufm_host> | [ufm-remote-server-config.host](fluentd_topology_plugin.sample.cfg#L2) | True | Hostname or IP for The UFM Enterprise
| --ufm_protocol <ufm_protocol> | [ufm-server-config.ws_protocol](fluentd_topology_plugin.sample.cfg#L4) | True | Web services protocol used by UFM Enterprise (HTTP, HTTPS)
| --ufm_username <ufm_username> | [ufm-server-config.username](fluentd_topology_plugin.sample.cfg#L6) | True | Username of UFM user
| --ufm_password <ufm_password> | [ufm-server-config.password](fluentd_topology_plugin.sample.cfg#L7) | True | Password of UFM user
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](fluentd_topology_plugin.sample.cfg#L27) | False | Log file name, if not provided a default stream wil lbe used
| --logs_level <logs_level> | [logs-config.logs_level](fluentd_topology_plugin.sample.cfg#L30) | False | Default is 'info'
| --local_streaming <local_streaming> | [streaming-config.local_streaming](fluentd_topology_plugin.sample.cfg#L10) | False | Enable/Disable local topology streaming [Default is 'False']
| --streaming <streaming> | [streaming-config.streaming](fluentd_topology_plugin.sample.cfg#L11) | False | Enable/Disable topology streaming [Default is 'True']
| --streaming_interval <streaming_interval> | [streaming-config.interval](fluentd_topology_plugin.sample.cfg#L12) | False | The periodic interval [the script will be ran in every X minutes (Default is 5 minutes)]
| --streaming_systems <streaming_systems> | [streaming-config.systems](fluentd_topology_plugin.sample.cfg#L13) | False | Default is 'True'
| --streaming_ports <streaming_ports> | [streaming-config.ports](fluentd_topology_plugin.sample.cfg#L14) | False | Default is 'True'
| --streaming_links <streaming_links> | [streaming-config.links](fluentd_topology_plugin.sample.cfg#L15) | False | Default is 'True'
| --streaming_alarms <streaming_alarms> | [streaming-config.alarms](fluentd_topology_plugin.sample.cfg#L16) | False | Default is 'True'

*If command line argument is provided, the corresponding config value will be ignored

Use
--------------------------------------------------------
This application is not a daemon; you should run it via time-based job scheduler (cron job).
