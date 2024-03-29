UFM Fabric Health
--------------------------------------------------------


This script is used to run Fabric Health Report via the UFM APIs.
Through Fabric Health Report, you can create reports that run a series of checks on the fabric.

For more details, click [here](https://docs.nvidia.com/networking/display/UFMEnterpriseUMv69/Fabric+Health+Tab).

Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Run
--------------------------------------------------------
### 1. Using command line arguments :

    python3 run_fabric_health_report.py --cables=True



### 2. Using configuration file :
    
  - Copy main SDK config file sample ufm-sdk.sample.cfg to ufm-sdk.cfg


        cp ../conf/ufm-sdk.sample.cfg ../conf/ufm-sdk.cfg

  - Edit config file with relevant parameters


        vi ../conf/ufm-sdk.cfg
    
  - Copy ufm fabric health config file sample fabric_health.sample.cfg to fabric_health.cfg


        cp fabric_health.sample.cfg fabric_health.cfg

  - Edit config file with relevant parameters


        vi fabric_health.cfg

  - Run


        python3 run_fabric_health_report.py


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
| --duplicate_nodes <duplicate_nodes> | [fabric-health.duplicate_nodes](fabric_health.sample.cfg#L3) | True | Duplicated Node Description [Default = False]
| --map_guids_desc <map_guids_desc> | [fabric-health.map_guids_desc](fabric_health.sample.cfg#L4) | False | Use Node Guid-Description Mapping [Default = False]
| --cables <cables> | [fabric-health.cables](fabric_health.sample.cfg#L7) | True | Cable Type Check & Cable Diagnostics [Default = True]
| --cables_errors_only <cables_errors_only> | [fabric-health.cables_errors_only](fabric_health.sample.cfg#L8) | False | Show Cable Errors And Warnings Only [Default = True]
| --duplicate_zero_and_lids <duplicate_zero_and_lids> | [fabric-health.duplicate_zero_and_lids](fabric_health.sample.cfg#L11) | False | Duplicate/Zero LIDs Check [Default = False]
| --non_opt_links <non_opt_links> | [fabric-health.non_opt_links](fabric_health.sample.cfg#L14) | True | Non-Optimal Links Check [Default = False]
| --non_opt_speed_width <non_opt_speed_width> | [fabric-health.non_opt_speed_width](fabric_health.sample.cfg#L15) | True | Non-Optimal Speed And Width [Default = False]
| --link_speed <link_speed> | [fabric-health.link_speed](fabric_health.sample.cfg#L17) | False | Link Speed, Possible values: ALL,SDR,DDR,QDR,FDR_10,FDR,EDR,HDR,NDR [if non_opt_speed_width is False then default=None, otherwise default=QDR]
| --link_width <link_width> | [fabric-health.link_width](fabric_health.sample.cfg#L19) | False | Link Width, Possible values: ALL,X_1,X_4,X_8,X_12 [if non_opt_speed_width is False then default=None, otherwise default=ALL]
| --effective_ber_check <effective_ber_check> | [fabric-health.effective_ber_check](fabric_health.sample.cfg#L20) | True | Effective Ber Check [Default = False]
| --symbol_ber_check <symbol_ber_check> | [fabric-health.symbol_ber_check](fabric_health.sample.cfg#L21) | True | Symbol Ber Check [Default = False]
| --phy_port_grade <phy_port_grade> | [fabric-health.phy_port_grade](fabric_health.sample.cfg#L22) | True | Physical Port Grade [Default = False]
| --eye_open <eye_open> | [fabric-health.eye_open](fabric_health.sample.cfg#L25) | True | Eye Open Check [Default = False]
| --min_bound <min_bound> | [fabric-health.min_bound](fabric_health.sample.cfg#L26) | False | Minimum Port Bound [if eye_open is False then default=None, otherwise default=22]
| --max_bound <max_bound> | [fabric-health.max_bound](fabric_health.sample.cfg#L27) | False | Maximum Port Bound [if eye_open is False then default=None, otherwise default=65]
| --eye_open_errors_only <eye_open_errors_only> | [fabric-health.eye_open_errors_only](fabric_health.sample.cfg#L28) | True | Show Errors And Warnings Only For Eye Open Check [Default = False]
| --firmware <firmware> | [fabric-health.firmware](fabric_health.sample.cfg#31) | True | Firmware Version Check [Default = False]
| --sm_state <sm_state> | [fabric-health.sm_state](fabric_health.sample.cfg#L34) | True | SM Configuration Check [Default = False]
| --ufm_alarms <ufm_alarms> | [fabric-health.ufm_alarms](fabric_health.sample.cfg#L37) | True | UFM Alarms [Default = False]

*If command line argument is provided, the corresponding config value will be ignored

