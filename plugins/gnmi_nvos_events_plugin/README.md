# Deployment

## UFM WEB UI
- pull the plugin container with _docker pull mellanox/ufm-plugin-gnmi-nvos-events_;
- add the plugin through UFM WEB UI -> Settings -> Plugin Management;

## CLI

### To deploy the plugin on UFM Appliance:
- login as admin;
- run _enable_;
- run _config terminal_;
- make sure that UFM is running with _show ufm status_;
  - if UFM is down then run it with _ufm start_;
- make sure that GNMI NVOS Events plugin is disabled with _show ufm plugin_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-gnmi-nvos-events_;
  - in case of HA load the plugin on the standby node as well;
- on UFM Enterprise Appliance (e.g., gen3), open the default SNMP port with _ufw allow 162/udp_ (enter _\_shell_, if needed);
- run _ufm plugin gnmi\_events add_ to enable the plugin;
- check that plugin is up and running with _ufm plugin show_;

### To deploy the plugin with UFM (SA or HA):
- install the latest version of UFM;
- run UFM with _systemctl start ufm-infra_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-gnmi-nvos-events_;
  - in case of HA load the plugin on the standby node as well;
- run _/opt/ufm/scripts/manage\_ufm\_plugins.sh add -p gnmi\_events_ to enable the plugin;
- check that plugin is up and running with _docker ps_;

Log file gnmi_nvos_events.log is located in /opt/ufm/files/log/plugins/gnmi-nvos-events on the host.

# Usage

This plugin is listening to GNMI traps from all NVOS managed switches in the fabric and redirecting them as events to UFM.

# Testing

Upon a startup of the plugin, all managed switches in the fabric, that have an IP and SSH credentials (global or local), will be sending system events in "on change" mode to the plugin. The plugin then parses the events and sends them to UFM in the form of general external events.
An example of a positive testing flow is the following:
- start UFM;
- load the plugin;
- make sure IP of a switch is valid in Managed Elements > Devices tab, or set it manually via Device Access tab;
- set global credentials through Settings > Device Access tab;
- login to the switch;
- reset any valid port (e.g., nv action reset platform transceiver sw1p1);
- check the event(s) was received in Events & Alarms tab.