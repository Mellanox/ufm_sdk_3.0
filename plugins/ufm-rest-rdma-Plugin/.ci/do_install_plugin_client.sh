#!/bin/bash -x
cd docker/
tagver=$(cat release_info)
docker load < /ufm-plugin-rest-rdma_$tagver.tar.gz > /dev/null
docker run -d --network=host --privileged --name=ufm-plugin-rest-rdma --rm -v /tmp/ibdiagnet:/tmp/ibdiagnet mellanox/ufm-plugin-rest-rdma:$tagver client
cd /
./ufm_rest_rdma_client.sh -u admin -p admin -t simple -a POST -w ufmRest/actions/add_guids_to_pkey -l'{\"pkey\": \"0x0002\",\"guids\": [\"f452140300188540\"],\"index0\": true,\"default_membership\": \"full\",\"ip_over_ib\": false}'
gettoken=$(./ufm_rest_rdma_client.sh -u admin -p admin -t simple -a GET -w ufmRest/actions/get_all_pkeys?guids_data=true)
if [ "$gettoken" != [] ]
then
    echo "post request passed"
else
    echo "simple post request faild  "
    exit 1
fi
./ufm_rest_rdma_client.sh -u admin -p admin -t simple -a POST -w ufmRest/actions/remove_guids_from_pkey -l '{\"pkey\":\"0x0002\",\"guids\":[\"f452140300188540\"]}'
gettoken=$(./ufm_rest_rdma_client.sh -u admin -p admin -t simple -a GET -w ufmRest/actions/get_all_pkeys?guids_data=true)
if [ "$gettoken" != [] ]
then
    echo "delete request failed"
    exit 1
else
    echo "delete request passed"
fi
./ufm_rest_rdma_client.sh -u admin -p admin -t ibdiagnet -a POST -w ufmRest/reports/ibdiagnetPeriodic -l '{\"general\": {\"name\": \"RestRDMA\", \"location\": \"local\", \"running_mode\": \"once\"}, \"command_flags\": {\"--pc\": \"\"}}'
tmpibi=$(ls -l /tmp/ibdiagnet/)
if [ "$tmpibi" == "total 0" ]
then
    echo "ibiagent request failed"
    exit 1
else 
    echo "ibdiagnet post request passed"
fi
rm -rf /tmp/ibdiagnet/*
docker stop ufm-plugin-rest-rdma
docker image rm $(docker images |grep mell|awk '{print $3}')