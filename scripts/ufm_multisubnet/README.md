UFM Multisubnet Automation Setup
--------------------------------------------------------


This script is used to automate the process of setting up the configurations of multi-sites UFM servers 


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

To export your repository to PYTHONPATH, please run :

   export PYTHONPATH="${PYTHONPATH}:<your ufm_sdk_cookbook path>"


Running using command line arguments :
--------------------------------------------------------
     python3 scripts/ufm_multisubnet/src/app.py --ufm_consumer_ip=<ufm_consumer_address> --ufm_consumer_username=<username> --ufm_consumer_password=<password> --ufm_providers_from_ip=<start_provider_ip_address> --ufm_providers_to_ip=<end_provider_ip_address> --ufm_provider_username=<username> --ufm_provider_password=<password>  

Note: the script should be executed under the ufm_sdk_3.0 directory


Running using configuration file:
--------------------------------------------------------
- Edit config file with relevant parameters


    vi scripts/ufm_multisubnet/conf/multisubnet.cfg

- Run


    python3 scripts/ufm_multisubnet/src/app.py


Log file tfs.log is created in /log/multisubnet_configration_setup.log once you run the script.

 Running syntax
--------------------------------------------------------

|                          Argument                           |                    Corresponding Config Value                     | Required |                                                                                 Description                                                                                  |
|:-----------------------------------------------------------:|:-----------------------------------------------------------------:|:--------:|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|             --ufm_consumer_ip <ufm_consumer_ip>             |        [Consumer.ufm_consumer_ip](conf/multisubnet.cfg#L2)        |   True   |                                                                        IP for the consumer UFM server                                                                        |
|       --ufm_consumer_username <ufm_consumer_username>       |     [Consumer.ufm_consumer_username](conf/multisubnet.cfg#L3)     |   True   |                                                                     Username for the consumer UFM server                                                                     |
|       --ufm_consumer_password <ufm_consumer_password>       |     [Consumer.ufm_consumer_password](conf/multisubnet.cfg#L4)     |   True   |                                                                     Password for the consumer UFM server                                                                     |
|       --ufm_providers_from_ip <ufm_providers_from_ip>       |    [Providers.ufm_providers_from_ip](conf/multisubnet.cfg#L7)     |   True   |                                                          Starting IP range of the providers UFM servers (inclusive)                                                          |
|         --ufm_providers_to_ip <ufm_providers_to_ip>         |     [Providers.ufm_providers_to_ip](conf/multisubnet.cfg#L8)      |   True   |                                                           Ending IP range of the providers UFM servers (inclusive)                                                           |
|       --ufm_provider_username <ufm_provider_username>       |    [Providers.ufm_provider_username](conf/multisubnet.cfg#L3)     |   True   |                                                                     Username for the provider UFM server                                                                     |
|       --ufm_provider_password <ufm_provider_password>       |    [Providers.ufm_provider_password](conf/multisubnet.cfg#L4)     |   True   |                                                                     Password for the provider UFM server                                                                     |
|  --ufm_provider_topology_port <ufm_provider_topology_port>  | [Providers.ufm_provider_topology_port](conf/multisubnet.cfg#L12)  |   True   |                                                                  Providers topology port [Default is 7120]                                                                   |
|     --ufm_provider_proxy_port <ufm_provider_proxy_port>     |   [Providers.ufm_provider_proxy_port](conf/multisubnet.cfg#L13)   |   True   |                                                                    Providers proxy port [Default is 443]                                                                     |
| --ufm_provider_telemetry_port <ufm_provider_telemetry_port> | [Providers.ufm_provider_telemetry_port](conf/multisubnet.cfg#L14) |   True   |                                                             Providers telemetry endpoint port [Default is 9001]                                                              |
|   --ufm_auto_token_generation <ufm_auto_token_generation>   |  [Providers.ufm_auto_token_generation](conf/multisubnet.cfg#L16)  |  False   | If true, a token will be generated in the UFM provider via the provider's credentials and use it by the consumer with the communication with this provider [Default is True] |
|              --logs_file_name <logs_file_name>              |      [logs-config.logs_file_name](conf/multisubnet.cfg#L19)       |   True   |                                                     Log file name [Default = '/log/multisubnet_configration_setup.log']                                                      |
|                  --logs_level <logs_level>                  |        [logs-config.logs_level](conf/multisubnet.cfg#L20)         |   True   |                                                                              Default is 'INFO'                                                                               |
|           --max_log_file_size <max_log_file_size>           |     [logs-config.max_log_file_size](conf/multisubnet.cfg#L21)     |   True   |                                                              Maximum log file size in Bytes [Default is 10 MB]                                                               |
|       --log_file_backup_count <log_file_backup_count>       |   [logs-config.log_file_backup_count](conf/multisubnet.cfg#L22)   |   True   |                                                              Maximum number of backup log files [Default is 5]                                                               |

