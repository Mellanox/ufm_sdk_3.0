UFM Fabric Validation Tests
--------------------------------------------------------


This plugin is used to run fabric validation tests via the UFM APIs.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

To export your repository to PYTHONPATH, please run :

   export PYTHONPATH="${PYTHONPATH}:<your ufm_sdk_cookbook path>"

Run
--------------------------------------------------------
### 1. Get all available fabric validation tests :

    python3 run_validation_test.py --get_available_tests

### 2. Run a fabric validation test:

    python3 run_validation_test.py --run_test=Test


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
| --run_test <run_test> | None | True | Option to run a test
| --get_pkey <get_pkey> | None | True | Option to get list of tests which are available to run


*If command line argument is provided, the corresponding config value will be ignored

 Available Tests
--------------------------------------------------------

| Test Name 
| :---:
| CheckLids 
| CheckLinks 
| CheckSubnetManager 
| CheckDuplicateNodes 
| CheckRouting
| CheckDuplicateGuids 
| CheckLinkSpeed 
| CheckLinkWidth 
| CheckPartitionKey 
| CheckTemperature
| CheckCables 
| CheckEffectiveBER 
| CheckSymbolBER 
| RailOptimizedTopologyValidation
| DragonflyTopologyValidation 
| SHARPFabricValidation 
| TreeTopologyValidation 
| SocketDirectModeReporting
