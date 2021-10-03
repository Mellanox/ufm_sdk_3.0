UFM Topology Management and Visualization
--------------------------------------------------------


This plugin is used to export the ufm topology as topo or to compare the current topology with an external topo file via UFM API and visualize it via [Gephi](https://github.com/gephi/gephi) tool

Overview
--------------------------------------------------------

The UFM Enterprise product is Nvidia’s platform for IB fabric management. Through this platform, the various devices (switches, multi-chip systems, cables, etc.) are discovered, configured and the status of the entire fabric is reflected.
As a fabric manager, the UFM Enterprise holds an internal representation model of the network topology. This topology should be exported and compared with other snapshots of the topology (as it can change with time) towards external files.



Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Run
--------------------------------------------------------
### 1. Using command line arguments :
 - Export topology as .topo file:

        python3 ufm_topology.py --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password --export_as_topo

 - Export topology to Gephi:

        python3 ufm_topology.py --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password --export_to_gephi

 - Compare topology with external .topo file:

        python3 ufm_topology.py --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password --compare_topology_with=path_to_external_topo_file

 - Compare topology with external .topo file and export compare result to Gephi:

        python3 ufm_topology.py --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password --compare_topology_with=path_to_external_topo_file --export_compare_topology_to_gephi


### 2) using configuration file:

  - Copy main SDK config file sample ufm-sdk.sample.cfg to ufm-sdk.cfg


        cp ../conf/ufm-sdk.sample.cfg ../conf/ufm-sdk.cfg

  - Edit config file with relevant parameters


        vi ../conf/ufm-sdk.cfg
    
  - Copy ufm topology config file sample ufm_topology.sample.cfg to ufm_topology.cfg


        cp ufm_topology.sample.cfg ufm_topology.cfg

  - Edit config file with relevant parameters


        vi ufm_topology.cfg
    

  - Run


        python3 ufm-topology.py

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
| --export_to_gephi <export_to_gephi> | [ufm-topology.export_to_gephi](ufm_topology.sample.cfg#L2) | False | Option to export the topology as gexf file [Default is False]
| --export_as_topo <export_as_topo> | [ufm-topology.export_as_topo](ufm_topology.sample.cfg#L3) | False | Option to export the topology as topo file [Default is False]
| --path_to_export <path_to_export> | [ufm-topology.path_to_export](ufm_topology.sample.cfg#L5) | False | Option to specify where the exported files will be stored [Default = 'api_results']
| --gephi_file_name <gephi_file_name> | [ufm-topology.gephi_file_name](ufm_topology.sample.cfg#L7) | False | Option to have file name for the exported topology [Default will be auto-generated name]
| --topo_file_name <topo_file_name> | [ufm-topology.topo_file_name](ufm_topology.sample.cfg#L8) | False | Option to have file name for the exported topology [Default will be auto-generated name]
| --compare_topology_with <compare_topology_with> | [ufm-topology-compare.compare_topology_with](ufm_topology.sample.cfg#L12) | True | The path of the external topo file to compare it with the current topology
| --export_compare_topology_to_gephi <export_compare_topology_to_gephi> | [ufm-topology-compare.export_compare_topology_to_gephi](ufm_topology.sample.cfg#L14) | False | Option to export the result of the topology compare as gexf file [Default = False]


*If command line argument is provided, the corresponding config value will be ignored

