*Under Development*

**Deployment**

To deploy the plugin on UFM Appliance:
- login as admin;
- run _enable_;
- run _config terminal_;
- make sure that UFM is running with _show ufm status_;
  - if UFM is down then run it with _ufm start_;
- make sure that Sysinfo plugin is disabled with _show ufm plugin_;
- load the plugin container with _docker load mellanox/ufm-plugin-sysinfo_;
  - in case of HA load the plugin on the standby node as well;
- run _ufm plugin ndt add_ to enable the plugin;
- check that plugin is up and running with _ufm plugin show_;

To deploy the plugin with UFM (SA or HA):
- install the latest version of UFM;
- run UFM with _/etc/init.d/ufmd start_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-sysinfo_;
  - in case of HA load the plugin on the standby node as well;
- run _/opt/ufm/scripts/manage_ufm_plugins.sh add -p ndt_ to enable the plugin;
- check that plugin is up and running with _docker ps_;

Log file sysinfo.log is located in /opt/ufm/files/log on the host.

------------------------------------------------------------------------------------------------------------

**Explanation**

The plugin query commands to switches using AIOHttps communication to those switches.
The plugin also responsible to login and logout the sessions with the all of the switches.
The commands can be every command that can run on managed switch using URL of /admin/launch?script=json (such as ["show power","show inventory"]).
Queries can be set to be periodically and with given interval in seconds.

For more details, run _python sysinfo_rest_api.py --help_.

**Usage**

