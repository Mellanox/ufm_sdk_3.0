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
