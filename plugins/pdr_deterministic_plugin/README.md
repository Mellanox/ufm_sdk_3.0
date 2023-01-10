UFM Packet Drop Rate (PDR) Deterministic Plugin
--------------------------------------------------------


This plugin is used to handle the port isolation handled by the UFM. 

Overview
--------------------------------------------------------

The plugin will isolate ports based on their PDR, BER values and NOC state. An option of dry-run is available to understand the plugin's decisions. It is recommended to disable the UFM's auto-isolation mechanism before running this plugin.



Plugin Deployment
--------------------------------------------------------

Before deploying the plugin please run init_pdr_conf.sh located under /opt/ufm/scripts/ to configure correctly UFM Telemetry and UFM Enterprise. This action will restart both UFM Telemetry and UFM Enterprise processes.
exposed REST API listening in port 8982 enables changing a port state to "treated"