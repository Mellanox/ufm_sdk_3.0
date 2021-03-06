**Deployment**

To deploy the plugin on UFM Appliance:
- login as admin;
- run _enable_;
- run _config terminal_;
- make sure that UFM is running with _show ufm status_;
  - if UFM is down then run it with _ufm start_;
- make sure that NDT plugin is disabled with _show ufm plugin_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-ndt_;
  - in case of HA load the plugin on the standby node as well;
- run _ufm plugin ndt add_ to enable the plugin;
- check that plugin is up and running with _ufm plugin show_;

To deploy the plugin with UFM (SA or HA):
- install the latest version of UFM;
- run UFM with _/etc/init.d/ufmd start_;
- pull the plugin container with _docker pull mellanox/ufm-plugin-ndt_;
  - in case of HA load the plugin on the standby node as well;
- run _/opt/ufm/scripts/manage_ufm_plugins.py add -p ndt_ to enable the plugin;
- check that plugin is up and running with _docker ps_;

Log file ndt.log is located in /opt/ufm/files/log on the host.

------------------------------------------------------------------------------------------------------------

**Usage**

Example of a test scenario (positive flow):
- run UFM simulation based on [ibnetdiscover_director.txt](https://github.com/Mellanox/UFM/blob/master/simulation/ibnetdiscover_files/ibnetdiscover_director.txt) file (instruction on how to run UFM on top of simulated topology could be found [here](https://github.com/Mellanox/UFM/blob/master/simulation/README.md));
- _curl -k -i -X POST -H "Content-Type:application/json" -d ‘<request>’ ‘http://<host_ip>/ufmRest<V2><V3>/plugin/ndt/upload_metadata’_: upload the data, don’t forget to replace Windows line endings with Linux ones;
- _curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/list'_: check a list of uploaded NDTs;
- _curl -k -i -X POST -H "Content-Type:application/json" -d ‘’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/compare’_: run topology comparison;
- _curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports’_: check a list of reports;
- _curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports/1’_: check the content of the 1-st (and the only one) report;
- _curl -k -i -X POST -H "Content-Type:application/json" -d ‘<request>’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/compare’_: run topology periodic comparison, e.g., startTime is current time, endTime is current time + 10 minutes, interval is 5 minute;
- wait for 10 minutes and run _curl -k -i -X GET 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports’_ to check the list of reports again – there should be 4 now.
- _curl -k -i -X POST -H "Content-Type:application/json" -d ‘’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/delete’_: delete NDTs;

Please use tests/ndt_rest_api.py wrapper script as a client for REST API. For more details, run _python ndt_rest_api.py --help_.
