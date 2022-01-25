UFM Telemetry endpoint stream To FluentD endpoint
--------------------------------------------------------


This plugin is used to extract ufm telemetry via [Prometheus](https://prometheus.io/) metrics and stream it via [fluentd](https://www.fluentd.org/) protocol to telemetry console

Overview
--------------------------------------------------------

NVIDIA UFM Telemetry platform provides network validation tools to monitor network performance and conditions, capturing and streaming rich real-time network telemetry information, application workload usage to an on-premise or cloud-based database for further analysis.
As a fabric manager, the UFM Telemetry holds a real-time network telemetry information of the network topology. This information should be reflected, over time (as it can change with time) towards telemetry console. In order to do so, we present stream To FluentD plugin



Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Fluentd configurations
--------------------------------------------------------

- We provide [fluentd.conf](conf/fluentd.conf) as a fluentd configurations sample.

Run
--------------------------------------------------------
### 1) using command line arguments :


    python3 ufm-telemetry-stream-to-fluentd.py --ufm_telemetry_host=<host> --ufm_telemetry_port=<port> --fluentd_host=fluentd_host --fluentd_port=fluentd_port  


### 2) using configuration file:

  - copy config file sample ufm-telemetry-stream-to-fluentd.sample.cfg to ufm-telemetry-stream-to-fluentd.cfg


    cp ufm-telemetry-stream-to-fluentd.sample.cfg ufm-telemetry-stream-to-fluentd.cfg

  - Edit config file with relevant parameters


    vi ufm-telemetry-stream-to-fluentd.cfg

  - Run


    python3 ufm-telemetry-stream-to-fluentd.py

 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --fluentd_host <fluentd_host> | [fluentd-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L7) | True |  Hostname or IP for FluentD endpoint
| --fluentd_port <fluentd_port> | [fluentd-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L8) | True | Port for FluentD endpoint
| --fluentd_timeout <fluentd_timeout> | [fluentd-endpoint.timeout](conf/ufm-telemetry-stream-to-fluentd.cfg#L9) | True | Timeout for FluentD endpoint streaming [Default is 120 seconds]
| --fluentd_message_tag_name <fluentd_message_tag_name> | [fluentd-endpoint.message_tag_name](conf/ufm-telemetry-stream-to-fluentd.cfg#L10) | False | Message Tag Name for FluentD endpoint message [Default is the ufm_telemetry_host]
| --ufm_telemetry_host <ufm_telemetry_host> | [ufm-telemetry-endpoint.host](conf/ufm-telemetry-stream-to-fluentd.cfg#L2) | True | Hostname or IP for The UFM Telemetry Endpoint
| --ufm_telemetry_port <ufm_telemetry_port> | [ufm-telemetry-endpoint.port](conf/ufm-telemetry-stream-to-fluentd.cfg#L3) | True | Port for The UFM Telemetry Endpoint [Default is 9001]
| --ufm_telemetry_url <ufm_telemetry_url> | [ufm-telemetry-endpoint.url](conf/ufm-telemetry-stream-to-fluentd.cfg#L4) | True | URL for The UFM Telemetry Endpoint [Default is 'enterprise']
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](../conf/ufm-sdk.sample.cfg#L11) | False | Log file name [Default = 'console.log']
| --logs_level <logs_level> | [logs-config.logs_level](../conf/ufm-sdk.sample.cfg#L14) | False | Default is 'info'

*If command line argument is provided, the corresponding config value will be ignored

Use
--------------------------------------------------------
This application is not a daemon; you should run it via time-based job scheduler (cron job).
