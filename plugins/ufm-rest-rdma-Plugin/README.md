# ufm-rest-rdma
Deployment:
to build docker image, enter docker directory and run
docker_build.sh
once completed - docker image ufm-plugin-ufm-rest.tar.gz
will be located at / of your build server

to load image run
docker load < ufm-plugin-ufm-rest.tar.gz

to start container as server run
docker run -d --network=host --privileged --name=ufm-plugin-ufm-rest --rm -v /opt/ufm/files/periodicIbdiagnet:/opt/ufm/files/periodicIbdiagnet -v /opt/ufm/files/log:/opt/ufm/files/log -v /opt/ufm/files/conf:/opt/ufm/files/conf ufm-plugin-ufm-rest

to start container as client run
docker run -d --network=host --privileged --name=ufm-plugin-ufm-rest --rm ufm-plugin-ufm-rest client

to enter docker container run
docker exec -it ufm-plugin-ufm-rest bash

In server mode ufm_rdma.py will started automatically and will be restarted if exit.
If ufm_rdma.py server is not running start it:
cd /opt/ufm/src/ufm-plugin-ufm-rest

./ufm_rdma.py -r server


=============================================

If container used as client. (see abow start command)
cd /opt/ufm/src/ufm-plugin-ufm-rest
To run client use help option
./ufm_rdma.py -h to see
available parameters.
examples:

to get UFM version
./ufm_rdma.py -r client -u admin -p 123456 -t simple -a GET -w ufmRest/app/ufm_version

to get ibdiagnet run result
./ufm_rdma.py -r client -u admin -p 123456 -t ibdiagnet -a POST -w ufmRest/reports/ibdiagnetPeriodic -l '{"general": {"name": "IBDiagnet_CMD_1234567890_199_88", "location": "local", "running_mode": "once"}, "command_flags": {"--pc": ""}}'

if use client certificate:
ufm server name with IP should exist in /etc/hosts file on server side (server docker)
need to pass path to client certificate file and name of UFM server machine: 
./ufm_rdma.py -r client -t simple -a GET -w ufmRest/resources/modules -d /path/to/certificate/file/ufm-client.pfx -s ufm.azurehpc.core.azure-test.net

Additional option is to use client script directly from host (no need to enter docker container).
Example:
./ufm_rest_rdma_client.sh -u admin -p 123456 -t simple -a GET -w ufmRest/app/ufm_version

Run ./ufm_rest_rdma_client.sh -h
ro see available options

