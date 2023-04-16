**Deployment**

To deploy the plugin on UFM Appliance:
- login as admin;
- run _enable_;
- run _config terminal_;
- make sure that UFM is running with _show ufm status_;
  - if UFM is down then run it with _ufm start_;
- make sure that SNMP plugin is disabled with _show ufm plugin_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-snmp_;
  - in case of HA load the plugin on the standby node as well;
- on gen3 appliance, open the default SNMP port with _ufw allow 162/udp_;
- run _ufm plugin snmp add_ to enable the plugin;
- check that plugin is up and running with _ufm plugin show_;

To deploy the plugin with UFM (SA or HA):
- install the latest version of UFM;
- run UFM with _service ufmd start_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-snmp_;
  - in case of HA load the plugin on the standby node as well;
- run _/opt/ufm/scripts/manage_ufm_plugins.sh add -p snmp_ to enable the plugin;
- check that plugin is up and running with _docker ps_;

Log file snmp.log is located in /opt/ufm/files/log on the host.

------------------------------------------------------------------------------------------------------------

**Usage**

This plugin is listening to SNMP traps from all managed switches in the fabric and redirecting them as events to UFM.
