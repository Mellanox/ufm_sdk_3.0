# Welcome To UFM NDT Plugin

To deploy the plugin on UFM Appliance, you should:
-	go to UFM Appliance machine (for me it’s r-ufm235, set up by Avi);
-	run en (short for enable);
-	run co t (short for config terminal);
-	run image fetch scp://<user>:<password>@<host>/auto/mtrswgwork/atolikin/ndt_testing/ufm-plugin-ndt.tar.gz – fetch the image from the machine that has access to /auto share, I used my virtual machine with default root credentials;
-	load the image with docker load ufm-plugin-ndt.tar.gz;
-	run ufm plugin ndt add;
-	check that plugin is up and running with show docker ps;

Log file ndt.log is located in /opt/ufm/history/container_storage/ufm_plugins.data/ndt.


To deploy the plugin with UFM (SA or HA), you should:
-	install the latest version of UFM;
-	load the image with sudo docker load -i /auto/mtrswgwork/atolikin/ndt_testing/ufm-plugin-ndt.tar.gz;
-	run /opt/ufm/scripts/manage_ufm_plugins.py add -p ndt;
-	check that plugin is up and running with docker ps;

Log file ndt.log is located in /opt/ufm/files/log on host.

-----------------------------------------------------------------------------------------------------------
  
Example of a test scenario (positive flow):
-	run UFM simulation based on /auto/mtrswgwork/atolikin/ndt_testing/ibnetdiscover_director.txt file;
-	curl -k -i -X POST -H "Content-Type:application/json" -d ‘<request>’ ‘http://<host_ip>/ufmRest<V2><V3>/plugin/ndt/upload_metadata’: upload the data (ndts can be found here: /auto/mtrswgwork/atolikin/ndt_testing/<name>.ndt), don’t forget to replace Windows line endings with Linux ones;
-	curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/list': check a list of uploaded NDTs;
-	curl -k -i -X POST -H "Content-Type:application/json" -d ‘’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/compare’: run topology comparison;
-	curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports’: check a list of reports;
-	curl -k -i -X GET 'http:// <host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports/1’: check the content of the 1-st (and the only one) report;
-	curl -k -i -X POST -H "Content-Type:application/json" -d ‘<request>’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/compare’: run topology periodic comparison, e.g., startTime is current time, endTime is current time + 2 minutes, interval is 1 minute;
-	wait for 3 minutes and run curl -k -i -X GET 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/reports’ to check the list of reports again – there should be 4 now.
-	curl -k -i -X POST -H "Content-Type:application/json" -d ‘’ 'http://<host_ip>/ ufmRest<V2><V3>/plugin/ndt/delete’: delete NDTs;
