# ufm-rest-rdma
ufm_rest_rdma is an utility to send rest requests over ib to ufm server.
ufm_rest_rdma could serve as server and as client.

##Build and Deployment:
to build docker image, enter docker directory and run
`docker_build.sh [version]`

once completed - docker image ufm-plugin-ufm-rest_[version].tar.gz
will be located at / of your build server

to load image run
`docker load < ufm-plugin-ufm-rest.tar.gz`

to start container as server run
`docker run -d --network=host --privileged --name=ufm-plugin-ufm-rest --rm -v /opt/ufm/files/periodicIbdiagnet:/opt/ufm/files/periodicIbdiagnet -v /opt/ufm/files/log:/opt/ufm/files/log -v /opt/ufm/files/conf:/opt/ufm/files/conf ufm-plugin-ufm-rest`

to start container as client run
`docker run -d --network=host --privileged --name=ufm-plugin-ufm-rest --rm ufm-plugin-ufm-rest client`

to enter docker container run
`docker exec -it ufm-plugin-ufm-rest bash`

In server mode ufm_rdma.py will started automatically and will be restarted if exit.
If ufm_rdma.py server is not running start it:
```cd /opt/ufm/src/ufm-plugin-ufm-rest
   ./ufm_rdma.py -r server
```


If container used as client. (see abow start command)
`cd /opt/ufm/src/ufm-plugin-ufm-rest`

To run client use help option to see available parameters
`./ufm_rdma.py -h`

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

## Use client script directly from host (no need to enter docker container).
```
Example:
./ufm_rest_rdma_client.sh -u admin -p 123456 -t simple -a GET -w ufmRest/app/ufm_version

To see available options run
./ufm_rest_rdma_client.sh -h
```
