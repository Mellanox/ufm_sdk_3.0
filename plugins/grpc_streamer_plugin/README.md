## *Plugin under development*


### *Deployment*
To deploy the plugin with UFM (SA or HA):
1. install the latest version of UFM.
2. run UFM with /etc/init.d/ufmd start.
3. pull the plugin image from the known location.
5. run /opt/ufm/scripts/manage_ufm_plugins.py add -p grpc-streamer to enable the plugin;
6. check that plugin is up and running with docker ps;
7. if grpc default port is unavialable change the config file grpc-streamer.conf, and restart the plugin.

### *Usage*
Example of a test scenario using the console:
* Install the required modules and run the console.
* The console runs the basic grpc client and thus supports the main server functions.
* If the grpc default port was changed, the console need to be change as well using:
```
port <number_port>
```
* get the data of rest api once using:
```
client once --server_ip=<host_ip> --id=<unique_id> --auth=<username>,<password> --apis=events,links,alarms
```
where in this example the requested rest api are events, alarams and links. 
the result should be the same as calling those command:
<<<<<<< HEAD
<<<<<<< HEAD
```
curl -k -i -X GET 'http://<host_ip>/app/events’
curl -k -i -X GET 'http://<host_ip>/app/alarms’
curl -k -i -X GET 'http://<host_ip>/resources/links’
```
=======
curl -k -i -X GET 'http://<host_ip>/app/events’
curl -k -i -X GET 'http://<host_ip>/app/alarms’
curl -k -i -X GET 'http://<host_ip>/resources/links’
=======
```
curl -k -i -X GET 'http://<host_ip>/app/events’
curl -k -i -X GET 'http://<host_ip>/app/alarms’
curl -k -i -X GET 'http://<host_ip>/resources/links’
```

* get the data of rest api in a grpc stream using:
```
client stream --server_ip=<host_ip> --id=<unique_id> --token=token --apis=events;40;True,alarms;10
```
where in this example the requested rest api are events and alarms. The events receive every 40 seconds only the delta changes between the intervals, and alarms receive every 10 seconds all the results from the UFM.
=======
where in this example the requested rest api are events and alarms. The events receive every 40 seconds only the delta changes between the intervals, and alarms receive every 10 seconds all the results in the UFM.
