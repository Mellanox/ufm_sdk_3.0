**Overview**

UFM consumer plugin is a self-contained Docker container with REST API support managed by UFM.
The plugin is acting as UFM Multi-Subnet consumer with all the available for Multi-Subnet UFM (consumer) functionality.
The Multi-Subnet UFM feature allows for the management of large fabrics, consisting of multiple sites,
within a single product, namely Multi-Subnet UFM.

This feature is comprised of two layers: 
UFM Multi-Subnet Provider and UFM Multi-Subnet Consumer (UFM consumer plugin).
The UFM Provider functions as a Multi-Subnet Provider, exposing all local InfiniBand fabric
information to the UFM consumer (UFM consumer plugin). 
On the other hand, the UFM Consumer plugin acts as a Multi-Subnet Consumer, collecting and aggregating data
from currently configured UFM Providers, enabling users to manage multiple sites in one place.
While UFM Consumer offers similar functionality to regular UFM,
there are several behavioural differences related to aggregation.

**Deployment**

To deploy the plugin on UFM Appliance:
- login as admin;
- run _enable_;
- run _config terminal_;
- make sure that UFM is running with _show ufm status_;
  - if UFM is down then run it with _ufm start_;
- make sure that Sysinfo plugin is disabled with _show ufm plugin_;
- load the plugin container with _docker load mellanox/ufm-plugin-ufm_consumer_;
  - in case of HA load the plugin on the standby node as well;
- run _ufm plugin ufm_consumer add_ to enable the plugin;
- check that plugin is up and running with _ufm plugin show_;

To deploy the plugin with UFM (SA or HA):
- install the latest version of UFM;
- run UFM with _/etc/init.d/ufmd start_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-ufm_consumer_;
  - in case of HA load the plugin on the standby node as well;
- run _/opt/ufm/scripts/manage_ufm_plugins.sh add -p ufm_consumer_ to enable the plugin;
- check that plugin is up and running with _docker ps_;

Log files are UFM known log files are located in /opt/ufm/files/log/plugins/ufm_consumer on the host.

------------------------------------------------------------------------------------------------------------

**Usage**
Functionality of UFM consumer plugin identical to functionality of Multi-Subnet UFM.
Please refer to UFM Multi-Subnet UFM User manual page for additionl information
https://docs.nvidia.com/networking/display/ufmenterpriseumv6170/multi-subnet+ufm
