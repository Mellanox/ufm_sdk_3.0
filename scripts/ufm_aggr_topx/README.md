UFM Devices
--------------------------------------------------------


This script is used to get topx data by category. it will support three categories conv ,bw and alarms.


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

To exported your repository to PYTHONPATH, please run :

   export PYTHONPATH="${PYTHONPATH}:<your ufm_sdk_cookbook path>"


Running using command line arguments :
--------------------------------------------------------
     python3 ufm_aggr_topx.py --object=object --attr=attr --mode=mode --members_type=members_type --ufm_host=ufm_host --ufm_protocol=ufm_protocol --ufm_username=ufm_username --ufm_password=ufm_password



Running using configuration file:
--------------------------------------------------------
- copy config file sample ufm_aggr_topx.sample.cfg to ufm_aggr_topx.cfg


    cp ufm_aggr_topx.sample.cfg ufm_aggr_topx.cfg

- Edit config file with relevant parameters


    vi ufm_aggr_topx.cfg

- Run


    python3 ufm_aggr_topx.py


 Running syntax
--------------------------------------------------------

| Argument | Corresponding Config Value | Required | Description |
| :---: | :---: |:---: |:---: |
| --ufm_host <ufm_host> | [ufm-remote-server-config.host](../../conf/ufm-sdk.sample.cfg#L2) | True | Hostname or IP for The UFM Enterprise
| --ufm_protocol <ufm_protocol> | [ufm-server-config.ws_protocol](../../conf/ufm-sdk.sample.cfg#L4) | True | Web services protocol used by UFM Enterprise (HTTP, HTTPS)
| --ufm_username <ufm_username> | [ufm-server-config.username](../../conf/ufm-sdk.sample.cfg#L6) | True | Username of UFM user
| --ufm_password <ufm_password> | [ufm-server-config.password](../../conf/ufm-sdk.sample.cfg#L7) | True | Password of UFM user
| --logs_file_name <logs_file_name> | [logs-config.logs_file_name](../../conf/ufm-sdk.sample.cfg#L11) | False | Log file name [Default = 'console.log']
| --logs_level <logs_level> | [logs-config.logs_level](../../conf/ufm-sdk.sample.cfg#L14) | False | Default is 'info'
| --object <object_type> | [ufm-aggr-topx.object](ufm_aggr_topx.sample.cfg#L2) | True | TopX object type (servers, switches)
| --attr <attr> | [ufm-aggr-topx.attr](ufm_aggr_topx.sample.cfg#L3) | True | TopX attribute (bw, cong, alarms)
| --mode <mode> | [ufm-aggr-topx.mode](ufm_aggr_topx.sample.cfg#L4) | True | Option to decide which data to show, sender data or reciever data. this option is not rquired if attr=alarms (the value should be (RxBW or TxBW) if attr=bw and (RCBW or TCBW) if attr=cong)
| --members_type <members_type> | [ufm-aggr-topx.members_type](ufm_aggr_topx.sample.cfg#L5) | True | device or port [Default = device if attr=alarms]


*If command line argument is provided, the corresponding config value will be ignored
