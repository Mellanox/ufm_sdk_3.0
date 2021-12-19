# ufm-rest-rdma
ufm_rest_rdma is an utility to send rest requests over ib to ufm server.
ufm_rest_rdma could serve as server and as client.

##Build and Deployment:
Build version should be updated in release_info file under docker directory
to build docker image, enter docker directory and run
`docker_build.sh`

once completed - docker image ufm-plugin-rest-rdma_[version].tar.gz
will be located at / of your build server

#To deploy the plugin on UFM Appliance:
login as admin
run enable
run config terminal
make sure that UFM is running using
`show ufm status`
if UFM is down then run it using
`ufm start`
make sure that rest-rdma plugin is disabled using
`show ufm plugin`
pull the plugin container with
`docker pull mellanox/ufm-plugin-rest-rdmа`
run
`ufm plugin ufm-plugin-rest-rdma add`
to enable the plugin

check that plugin is up and running using 
`ufm plugin show`

#To deploy the plugin with UFM (SA or HA), you should:
install the latest version of UFM
run UFM with
`/etc/init.d/ufmd start`
pull the plugin container using
`docker pull mellanox/ufm-plugin-rest-rdma`
to enable the plugin run
`/opt/ufm/scripts/manage_ufm_plugins.py add -p rest-rdma`;
check that plugin is up and running using
`docker ps`
Log file ufm_rest_over_rdma.log is located in /opt/ufm/files/log on the host.
Check that plugin is up and running using
`ufm plugin show`

to start container as client run
`docker run -d --network=host --privileged --name=ufm-plugin-rest-rdma --rm -v /tmp/ibdiagnet:/tmp/ibdiagnet mellanox/ufm-plugin-rest-rdma:[version] client`

to enter docker container run
`docker exec -it ufm-plugin-ufm-rest bash`

If container used as client. There are two options to run client:
From inside the docker or using custom script from the hosting server.
1. From inside the docker:
 Enter to the docker and
 cd /opt/ufm/src/ufm-plugin-rest-rdma
 How to run client - use -h help option to see available parameters
`./ufm_rdma.py -h`
2. From hosting server
It is a script located at /opt/ufm/ufm-plugin-ufm-rest/ufm_rest_rdma_client.sh inside docker,
that could be copied using command
`cp <containerId>:/opt/ufm/ufm-plugin-ufm-rest/ufm_rest_rdma_client.sh /host/path/target`
from docker to client host and could be used to run REST requests
directly from the host with no need to enter to the client docker container

## Example:
```
./ufm_rest_rdma_client.sh -u admin -p 123456 -t simple -a GET -w ufmRest/app/ufm_version
```
To see available options run
`./ufm_rest_rdma_client.sh -h`


## Examples:
```
### user name password authentication

* to get UFM version
./ufm_rdma.py -r client -u admin -p 123456 -t simple -a GET -w ufmRest/app/ufm_version

* to get ibdiagnet run result
./ufm_rdma.py -r client -u admin -p 123456 -t ibdiagnet -a POST -w ufmRest/reports/ibdiagnetPeriodic -l '{"general": {"name": "IBDiagnet_CMD_1234567890_199_88", "location": "local", "running_mode": "once"}, "command_flags": {"--pc": ""}}'

### if use client certificate:
need to pass path to client certificate file and name of UFM server machine: 
./ufm_rdma.py -r client -t simple -a GET -w ufmRest/resources/modules -d /path/to/certificate/file/ufm-client.pfx -s ufm.azurehpc.core.azure-test.net

### if to use token:
nedd to pass it for authentication

./ufm_rdma.py -r client -k OGUY7TwLvTmFkXyTkcsEWD9KKNvq6f -t simple -a GET -w ufmRestV3/app/ufm_version
```

